"""
Interfaz Tkinter con tema oscuro, tarjetas y rejilla que escala al redimensionar.
"""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox, simpledialog, ttk
from typing import Callable, Optional, Tuple

from .board import EstadoPartida, ResultadoRevelado, Tablero

# Menú: texto y (filas, columnas, minas).
NIVELES_PRECONFIGURADOS: Tuple[Tuple[str, int, int, int], ...] = (
    ("Principiante (9×9, 10)", 9, 9, 10),
    ("Intermedio (16×16, 40)", 16, 16, 40),
    ("Experto (16×30, 99)", 16, 30, 99),
)

# Colores de números 0–8 sobre fondo oscuro (0 = casilla sin dígito).
COLORES_NUMEROS = (
    "#565f89",
    "#7aa2f7",
    "#9ece6a",
    "#f7768e",
    "#bb9af7",
    "#ff9e64",
    "#73daca",
    "#c0caf5",
    "#565f89",
)


def _tema_visual() -> dict[str, str]:
    """Paleta tipo editor oscuro (legible y contrastada)."""
    return {
        "fondo_raiz": "#1a1b26",
        "fondo_tarjeta": "#24283b",
        "fondo_rejilla": "#16161e",
        "celda_cubierta": "#3b4261",
        "celda_cubierta_activa": "#565f89",
        "celda_revelada": "#16161e",
        "celda_numero": "#1f2335",
        "mina": "#f7768e",
        "mina_fondo": "#4a2f2f",
        "mina_pisada_fondo": "#6b2f3a",
        "bandera": "#bb9af7",
        "bandera_fondo": "#343b55",
        "acento": "#7aa2f7",
        "texto": "#c0caf5",
        "texto_secundario": "#a9b1d6",
        "exito": "#9ece6a",
    }


class AplicacionBuscaminas:
    """Ventana principal: estilos ttk, rejilla expandible y fuente reactiva."""

    def __init__(self) -> None:
        self._tema = _tema_visual()
        # Tk() debe existir antes de font.families() (en 3.11+ no hay raíz implícita).
        self.ventana_principal = tk.Tk()
        self._familia_fuente = "Segoe UI"
        if "Segoe UI" not in tkfont.families(root=self.ventana_principal):
            self._familia_fuente = "TkDefaultFont"

        self.ventana_principal.title("Buscaminas")
        self.ventana_principal.configure(bg=self._tema["fondo_raiz"])
        self.ventana_principal.minsize(520, 420)
        self.ventana_principal.geometry("760x560")

        self.filas, self.columnas, self.minas_totales = 9, 9, 10
        self.tablero: Optional[Tablero] = None
        self.casillas_botones: list[list[tk.Button]] = []
        self._id_temporizador: Optional[str] = None
        self._segundos = 0
        self._partida_arrancada = False
        self._fuente_celdas_px = 11

        self._aplicar_estilos_ttk()
        self._construir_menu()
        self._construir_cuerpo()
        self.nueva_partida()

    def _aplicar_estilos_ttk(self) -> None:
        """Tema ``clam`` con colores alineados al fondo oscuro."""
        t = self._tema
        estilo = ttk.Style()
        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass
        estilo.configure(".", background=t["fondo_raiz"], foreground=t["texto"])
        estilo.configure("Card.TFrame", background=t["fondo_tarjeta"])
        estilo.configure(
            "Title.TLabel",
            background=t["fondo_tarjeta"],
            foreground=t["texto"],
            font=(self._familia_fuente, 16, "bold"),
        )
        estilo.configure(
            "Stat.TLabel",
            background=t["fondo_tarjeta"],
            foreground=t["texto_secundario"],
            font=(self._familia_fuente, 11),
        )
        estilo.configure(
            "Accent.TButton",
            background=t["acento"],
            foreground="#1a1b26",
            font=(self._familia_fuente, 10, "bold"),
            padding=(14, 8),
        )
        estilo.map(
            "Accent.TButton",
            background=[("active", "#89b4fa"), ("pressed", "#6c8fd4")],
        )

    def _construir_menu(self) -> None:
        """Barra de menú nativa (no depende del tema ttk)."""
        barra_menu = tk.Menu(self.ventana_principal, tearoff=0, bg=self._tema["fondo_tarjeta"], fg=self._tema["texto"])
        self.ventana_principal.config(menu=barra_menu)
        menu_juego = tk.Menu(barra_menu, tearoff=0, bg=self._tema["fondo_tarjeta"], fg=self._tema["texto"])
        barra_menu.add_cascade(label="Juego", menu=menu_juego)
        menu_juego.add_command(label="Nueva partida", command=self.nueva_partida, accelerator="F2")
        menu_juego.add_separator()
        for etiqueta, f, c, m in NIVELES_PRECONFIGURADOS:
            menu_juego.add_command(
                label=etiqueta,
                command=lambda ff=f, cc=c, mm=m: self._aplicar_nivel_predefinido(ff, cc, mm),
            )
        menu_juego.add_command(label="Personalizado…", command=self._nivel_personalizado)
        menu_juego.add_separator()
        menu_juego.add_command(label="Salir", command=self.ventana_principal.quit)
        self.ventana_principal.bind("<F2>", lambda _: self.nueva_partida())

    def _construir_cuerpo(self) -> None:
        """Contenedor principal con tarjeta superior y rejilla que ocupa el resto."""
        t = self._tema
        contenedor = ttk.Frame(self.ventana_principal, padding=(16, 14, 16, 16))
        contenedor.pack(fill=tk.BOTH, expand=True)

        tarjeta = ttk.Frame(contenedor, style="Card.TFrame", padding=(18, 14, 18, 14))
        tarjeta.pack(fill=tk.X)
        tarjeta.columnconfigure(0, weight=1)

        titulo = ttk.Label(tarjeta, text="Buscaminas", style="Title.TLabel")
        titulo.grid(row=0, column=0, sticky="w")

        fila_stats = ttk.Frame(tarjeta, style="Card.TFrame")
        fila_stats.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        fila_stats.columnconfigure(1, weight=1)

        self.etiqueta_minas = ttk.Label(fila_stats, text="Minas: 10", style="Stat.TLabel")
        self.etiqueta_minas.grid(row=0, column=0, sticky="w")

        self.boton_reiniciar = ttk.Button(
            fila_stats,
            text="Nueva partida",
            style="Accent.TButton",
            command=self.nueva_partida,
        )
        self.boton_reiniciar.grid(row=0, column=1, padx=12)

        self.etiqueta_tiempo = ttk.Label(fila_stats, text="Tiempo: 0 s", style="Stat.TLabel")
        self.etiqueta_tiempo.grid(row=0, column=2, sticky="e")

        # Marco exterior: la rejilla crece y dispara Configure para escalar fuente.
        self.marco_tablero_exterior = tk.Frame(contenedor, bg=t["fondo_raiz"])
        self.marco_tablero_exterior.pack(fill=tk.BOTH, expand=True, pady=(14, 0))
        self.marco_tablero_exterior.rowconfigure(0, weight=1)
        self.marco_tablero_exterior.columnconfigure(0, weight=1)

        self.marco_rejilla = tk.Frame(
            self.marco_tablero_exterior,
            bg=t["fondo_rejilla"],
            highlightthickness=1,
            highlightbackground=t["celda_cubierta"],
        )
        self.marco_rejilla.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        self.marco_rejilla.bind("<Configure>", self._al_redimensionar_rejilla)

    def _al_redimensionar_rejilla(self, evento: tk.Event) -> None:
        """Ajusta el tamaño de fuente de las celdas según el espacio disponible."""
        if evento.widget is not self.marco_rejilla:
            return
        if not self.casillas_botones:
            return
        ancho = max(int(evento.width), 1)
        alto = max(int(evento.height), 1)
        lado = min(ancho / max(self.columnas, 1), alto / max(self.filas, 1))
        # Factor elegido para que en tableros grandes siga legible y en pequeños no desborde.
        nuevo = max(8, min(22, int(lado * 0.42)))
        if abs(nuevo - self._fuente_celdas_px) < 1:
            return
        self._fuente_celdas_px = nuevo
        fuente = (self._familia_fuente, nuevo, "bold")
        for fila in self.casillas_botones:
            for boton in fila:
                boton.config(font=fuente)

    def _aplicar_nivel_predefinido(self, filas: int, columnas: int, minas: int) -> None:
        self.filas, self.columnas, self.minas_totales = filas, columnas, minas
        self.nueva_partida()

    def _nivel_personalizado(self) -> None:
        f = simpledialog.askinteger("Filas", "Número de filas (5-30):", minvalue=5, maxvalue=30)
        if f is None:
            return
        c = simpledialog.askinteger("Columnas", "Número de columnas (5-40):", minvalue=5, maxvalue=40)
        if c is None:
            return
        max_m = f * c - 1
        m = simpledialog.askinteger(
            "Minas",
            f"Número de minas (1-{max_m}):",
            minvalue=1,
            maxvalue=max_m,
        )
        if m is None:
            return
        self.filas, self.columnas, self.minas_totales = f, c, m
        self.nueva_partida()

    def _detener_temporizador(self) -> None:
        if self._id_temporizador is not None:
            self.ventana_principal.after_cancel(self._id_temporizador)
            self._id_temporizador = None

    def _avanzar_temporizador(self) -> None:
        if self.tablero is None or self.tablero.estado != EstadoPartida.JUGANDO:
            return
        self._segundos += 1
        self.etiqueta_tiempo.config(text=f"Tiempo: {self._segundos} s")
        self._id_temporizador = self.ventana_principal.after(1000, self._avanzar_temporizador)

    def _iniciar_temporizador_si_corresponde(self) -> None:
        if self._partida_arrancada:
            return
        self._partida_arrancada = True
        self._segundos = 0
        self.etiqueta_tiempo.config(text="Tiempo: 0 s")
        self._detener_temporizador()
        self._id_temporizador = self.ventana_principal.after(1000, self._avanzar_temporizador)

    def nueva_partida(self) -> None:
        """Recrea el tablero lógico y los botones; la rejilla sigue siendo expandible."""
        self._detener_temporizador()
        self._segundos = 0
        self._partida_arrancada = False
        self.etiqueta_tiempo.config(text="Tiempo: 0 s")
        self.tablero = Tablero(self.filas, self.columnas, self.minas_totales)
        self.etiqueta_minas.config(text=f"Minas: {self.minas_totales}")

        for hijo in self.marco_rejilla.winfo_children():
            hijo.destroy()
        self.casillas_botones = []

        t = self._tema
        fuente = (self._familia_fuente, self._fuente_celdas_px, "bold")

        for fila in range(self.filas):
            fila_botones: list[tk.Button] = []
            for columna in range(self.columnas):
                boton = tk.Button(
                    self.marco_rejilla,
                    text="",
                    relief=tk.FLAT,
                    bd=0,
                    highlightthickness=0,
                    padx=0,
                    pady=0,
                    activebackground=t["celda_cubierta_activa"],
                    activeforeground=t["texto"],
                    font=fuente,
                    cursor="hand2",
                )
                boton.grid(row=fila, column=columna, padx=1, pady=1, sticky="nsew")
                self._pintar_celda_tapada(boton)
                boton.bind("<Button-1>", self._crear_manejador_clic_izquierdo(fila, columna))
                boton.bind("<Button-3>", self._crear_manejador_clic_derecho(fila, columna))
                boton.bind("<Button-2>", self._crear_manejador_acorde(fila, columna))
                fila_botones.append(boton)
            self.casillas_botones.append(fila_botones)

        for i in range(self.filas):
            self.marco_rejilla.rowconfigure(i, weight=1, uniform="celda")
        for j in range(self.columnas):
            self.marco_rejilla.columnconfigure(j, weight=1, uniform="celda")

        self.ventana_principal.after_idle(lambda: self.marco_rejilla.event_generate("<Configure>"))

    def _pintar_celda_tapada(self, boton: tk.Button) -> None:
        """Aspecto de casilla no revelada (interactiva)."""
        t = self._tema
        boton.config(
            text="",
            fg=t["texto"],
            bg=t["celda_cubierta"],
            relief=tk.FLAT,
            state=tk.NORMAL,
        )

    def _crear_manejador_clic_izquierdo(self, fila: int, columna: int) -> Callable[[tk.Event], None]:
        def al_clic(_: tk.Event) -> None:
            if self.tablero is None:
                return
            self._iniciar_temporizador_si_corresponde()
            resultado = self.tablero.revelar(fila, columna)
            self._actualizar_tras_revelado(resultado)

        return al_clic

    def _crear_manejador_clic_derecho(self, fila: int, columna: int) -> Callable[[tk.Event], None]:
        def al_clic(_: tk.Event) -> None:
            if self.tablero is None:
                return
            if self.tablero.alternar_bandera(fila, columna):
                self._actualizar_apariencia_casilla(fila, columna)
                restantes = self.minas_totales - len(self.tablero.banderas)
                self.etiqueta_minas.config(text=f"Minas: {restantes}")

        return al_clic

    def _crear_manejador_acorde(self, fila: int, columna: int) -> Callable[[tk.Event], None]:
        def al_clic(_: tk.Event) -> None:
            if self.tablero is None:
                return
            resultado = self.tablero.revelar_acorde(fila, columna)
            self._actualizar_tras_revelado(resultado)

        return al_clic

    def _actualizar_tras_revelado(self, resultado: ResultadoRevelado) -> None:
        for f, c in resultado.casillas_reveladas:
            self._actualizar_apariencia_casilla(f, c)
        if resultado.estado == EstadoPartida.PERDIDO:
            self._detener_temporizador()
            self._mostrar_todas_las_minas()
            # Quita banderas en casillas sin mina y las revela: el número solo cuenta minas reales.
            self._revelar_banderas_incorrectas()
            messagebox.showinfo("Fin", "¡Has pisado una mina! Partida perdida.")
        elif resultado.estado == EstadoPartida.GANADO:
            self._detener_temporizador()
            self._marcar_banderas_en_todas_las_minas()
            messagebox.showinfo("Fin", "¡Has despejado todo! Victoria.")

    def _actualizar_apariencia_casilla(self, fila: int, columna: int) -> None:
        if self.tablero is None:
            return
        t = self._tema
        boton = self.casillas_botones[fila][columna]
        fuente = (self._familia_fuente, self._fuente_celdas_px, "bold")

        if (fila, columna) in self.tablero.reveladas:
            if self.tablero.es_mina(fila, columna):
                boton.config(
                    text="*",
                    font=fuente,
                    fg=t["mina"],
                    bg=t["mina_fondo"],
                    relief=tk.FLAT,
                    bd=0,
                    state=tk.DISABLED,
                    highlightthickness=0,
                )
            else:
                n = self.tablero.contar_minas_adyacentes(fila, columna)
                texto = "" if n == 0 else str(n)
                color_frente = COLORES_NUMEROS[n] if 0 <= n < len(COLORES_NUMEROS) else t["texto"]
                fondo = t["celda_numero"] if n else t["celda_revelada"]
                boton.config(
                    text=texto,
                    font=fuente,
                    fg=color_frente,
                    bg=fondo,
                    relief=tk.FLAT,
                    bd=0,
                    state=tk.DISABLED,
                    highlightthickness=0,
                )
        elif (fila, columna) in self.tablero.banderas:
            boton.config(
                text="⚑",
                font=fuente,
                fg=t["bandera"],
                bg=t["bandera_fondo"],
                relief=tk.FLAT,
                bd=0,
                state=tk.NORMAL,
                highlightthickness=0,
            )
        else:
            self._pintar_celda_tapada(boton)
            boton.config(font=fuente)

    def _mostrar_todas_las_minas(self) -> None:
        if self.tablero is None:
            return
        for fila in range(self.filas):
            for columna in range(self.columnas):
                if self.tablero.es_mina(fila, columna):
                    self.tablero.reveladas.add((fila, columna))
                    self._actualizar_apariencia_casilla(fila, columna)

    def _revelar_banderas_incorrectas(self) -> None:
        """
        Tras perder: las banderas que no hayan acertado una mina se quitan y se muestra
        el contenido real (así se entiende por qué un vecino mostraba 1 y no 2).
        """
        if self.tablero is None:
            return
        for fila, columna in list(self.tablero.banderas):
            if not self.tablero.es_mina(fila, columna):
                self.tablero.banderas.remove((fila, columna))
                self.tablero.reveladas.add((fila, columna))
                self._actualizar_apariencia_casilla(fila, columna)

    def _marcar_banderas_en_todas_las_minas(self) -> None:
        if self.tablero is None:
            return
        for posicion in self.tablero.minas:
            self.tablero.banderas.add(posicion)
        for fila in range(self.filas):
            for columna in range(self.columnas):
                self._actualizar_apariencia_casilla(fila, columna)

    def ejecutar(self) -> None:
        self.ventana_principal.mainloop()


def ejecutar() -> None:
    app = AplicacionBuscaminas()
    app.ejecutar()
