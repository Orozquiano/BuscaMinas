"""
Interfaz gráfica con Tkinter: rejilla de botones, menú de niveles,
temporizador y contador de minas restantes (aproximado por banderas).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from typing import Callable, Optional, Tuple

from minesweeper.board import EstadoPartida, ResultadoRevelado, Tablero

# Texto del menú y (filas, columnas, número de minas) para cada nivel.
NIVELES_PRECONFIGURADOS: Tuple[Tuple[str, int, int, int], ...] = (
    ("Principiante (9×9, 10)", 9, 9, 10),
    ("Intermedio (16×16, 40)", 16, 16, 40),
    ("Experto (16×30, 99)", 16, 30, 99),
)

# Colores clásicos para los números 1–8 (índice 0 sin uso).
COLORES_NUMEROS = (
    "",
    "#0000DD",
    "#007700",
    "#CC0000",
    "#000066",
    "#660000",
    "#007777",
    "#000000",
    "#555555",
)


class AplicacionBuscaminas:
    """Ventana principal: construye la rejilla y enlaza eventos de ratón."""

    def __init__(self) -> None:
        # Raíz de Tkinter.
        self.ventana_principal = tk.Tk()
        self.ventana_principal.title("Buscaminas")
        # Dimensiones y minas de la partida actual (por defecto principiante).
        self.filas, self.columnas, self.minas_totales = 9, 9, 10
        self.tablero: Optional[Tablero] = None
        # Matriz de botones [fila][columna].
        self.casillas_botones: list[list[tk.Button]] = []
        # Identificador devuelto por after() para poder cancelar el temporizador.
        self._id_temporizador: Optional[str] = None
        self._segundos = 0
        # True después del primer revelado (para arrancar el cronómetro una sola vez).
        self._partida_arrancada = False

        self._construir_menu()
        self._construir_barra_herramientas()
        self.marco_rejilla = ttk.Frame(self.ventana_principal, padding=4)
        self.marco_rejilla.pack(fill=tk.BOTH, expand=True)
        self.nueva_partida()

    def _construir_menu(self) -> None:
        """Menú superior: nueva partida, niveles y salida."""
        barra_menu = tk.Menu(self.ventana_principal)
        self.ventana_principal.config(menu=barra_menu)
        menu_juego = tk.Menu(barra_menu, tearoff=0)
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

    def _construir_barra_herramientas(self) -> None:
        """Etiquetas de minas y tiempo más botón reiniciar."""
        barra = ttk.Frame(self.ventana_principal, padding=(8, 4))
        barra.pack(fill=tk.X)
        self.etiqueta_minas = ttk.Label(barra, text="Minas: 10", width=14)
        self.etiqueta_minas.pack(side=tk.LEFT)
        self.boton_reiniciar = ttk.Button(barra, text="Reiniciar", command=self.nueva_partida)
        self.boton_reiniciar.pack(side=tk.LEFT, padx=8)
        self.etiqueta_tiempo = ttk.Label(barra, text="Tiempo: 0", width=12)
        self.etiqueta_tiempo.pack(side=tk.LEFT)

    def _aplicar_nivel_predefinido(self, filas: int, columnas: int, minas: int) -> None:
        """Cambia tamaño y minas según el nivel elegido en el menú."""
        self.filas, self.columnas, self.minas_totales = filas, columnas, minas
        self.nueva_partida()

    def _nivel_personalizado(self) -> None:
        """Diálogos para filas, columnas y minas con límites razonables."""
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
        """Cancela la llamada periódica al avance del tiempo."""
        if self._id_temporizador is not None:
            self.ventana_principal.after_cancel(self._id_temporizador)
            self._id_temporizador = None

    def _avanzar_temporizador(self) -> None:
        """Suma un segundo mientras la partida siga en curso."""
        if self.tablero is None or self.tablero.estado != EstadoPartida.JUGANDO:
            return
        self._segundos += 1
        self.etiqueta_tiempo.config(text=f"Tiempo: {self._segundos}")
        self._id_temporizador = self.ventana_principal.after(1000, self._avanzar_temporizador)

    def _iniciar_temporizador_si_corresponde(self) -> None:
        """Arranca el cronómetro en el primer revelado."""
        if self._partida_arrancada:
            return
        self._partida_arrancada = True
        self._segundos = 0
        self.etiqueta_tiempo.config(text="Tiempo: 0")
        self._detener_temporizador()
        self._id_temporizador = self.ventana_principal.after(1000, self._avanzar_temporizador)

    def nueva_partida(self) -> None:
        """Reinicia estado, crea un Tablero nuevo y vuelve a dibujar los botones."""
        self._detener_temporizador()
        self._segundos = 0
        self._partida_arrancada = False
        self.etiqueta_tiempo.config(text="Tiempo: 0")
        self.tablero = Tablero(self.filas, self.columnas, self.minas_totales)
        self.etiqueta_minas.config(text=f"Minas: {self.minas_totales}")
        for hijo in self.marco_rejilla.winfo_children():
            hijo.destroy()
        self.casillas_botones = []
        for fila in range(self.filas):
            fila_botones: list[tk.Button] = []
            for columna in range(self.columnas):
                boton = tk.Button(
                    self.marco_rejilla,
                    width=2,
                    height=1,
                    relief=tk.RAISED,
                    font=("Segoe UI", 10, "bold"),
                )
                boton.grid(row=fila, column=columna, padx=1, pady=1, sticky="nsew")
                boton.bind("<Button-1>", self._crear_manejador_clic_izquierdo(fila, columna))
                boton.bind("<Button-3>", self._crear_manejador_clic_derecho(fila, columna))
                boton.bind("<Button-2>", self._crear_manejador_acorde(fila, columna))
                fila_botones.append(boton)
            self.casillas_botones.append(fila_botones)
        for i in range(self.filas):
            self.marco_rejilla.rowconfigure(i, weight=1)
        for j in range(self.columnas):
            self.marco_rejilla.columnconfigure(j, weight=1)

    def _crear_manejador_clic_izquierdo(self, fila: int, columna: int) -> Callable[[tk.Event], None]:
        """Devuelve la función que revela la casilla (fila, columna)."""

        def al_clic(_: tk.Event) -> None:
            if self.tablero is None:
                return
            self._iniciar_temporizador_si_corresponde()
            resultado = self.tablero.revelar(fila, columna)
            self._actualizar_tras_revelado(resultado)

        return al_clic

    def _crear_manejador_clic_derecho(self, fila: int, columna: int) -> Callable[[tk.Event], None]:
        """Devuelve la función que alterna bandera en (fila, columna)."""

        def al_clic(_: tk.Event) -> None:
            if self.tablero is None:
                return
            if self.tablero.alternar_bandera(fila, columna):
                self._actualizar_apariencia_casilla(fila, columna)
                restantes = self.minas_totales - len(self.tablero.banderas)
                self.etiqueta_minas.config(text=f"Minas: {restantes}")

        return al_clic

    def _crear_manejador_acorde(self, fila: int, columna: int) -> Callable[[tk.Event], None]:
        """Devuelve la función de revelado por acorde (clic central / rueda)."""

        def al_clic(_: tk.Event) -> None:
            if self.tablero is None:
                return
            resultado = self.tablero.revelar_acorde(fila, columna)
            self._actualizar_tras_revelado(resultado)

        return al_clic

    def _actualizar_tras_revelado(self, resultado: ResultadoRevelado) -> None:
        """Refresca botones y muestra mensaje si la partida terminó."""
        for f, c in resultado.casillas_reveladas:
            self._actualizar_apariencia_casilla(f, c)
        if resultado.estado == EstadoPartida.PERDIDO:
            self._detener_temporizador()
            self._mostrar_todas_las_minas()
            messagebox.showinfo("Fin", "¡Has pisado una mina! Partida perdida.")
        elif resultado.estado == EstadoPartida.GANADO:
            self._detener_temporizador()
            self._marcar_banderas_en_todas_las_minas()
            messagebox.showinfo("Fin", "¡Has despejado todo! Victoria.")

    def _actualizar_apariencia_casilla(self, fila: int, columna: int) -> None:
        """Pinta el botón según revelado, mina, número o bandera."""
        if self.tablero is None:
            return
        boton = self.casillas_botones[fila][columna]
        if (fila, columna) in self.tablero.reveladas:
            if self.tablero.es_mina(fila, columna):
                boton.config(text="*", bg="#FFAAAA", fg="#000000", relief=tk.SUNKEN, state=tk.DISABLED)
            else:
                n = self.tablero.contar_minas_adyacentes(fila, columna)
                texto = "" if n == 0 else str(n)
                color_frente = COLORES_NUMEROS[n] if 0 <= n < len(COLORES_NUMEROS) else "#000000"
                boton.config(
                    text=texto,
                    fg=color_frente,
                    bg="#DDDDDD" if n else "#EEEEEE",
                    relief=tk.SUNKEN,
                    state=tk.DISABLED,
                )
        elif (fila, columna) in self.tablero.banderas:
            boton.config(text="⚑", fg="#CC0000", bg="#DDDDDD", state=tk.NORMAL)
        else:
            boton.config(text="", fg="#000000", bg="#F0F0F0", relief=tk.RAISED, state=tk.NORMAL)

    def _mostrar_todas_las_minas(self) -> None:
        """Al perder, deja visibles todas las minas."""
        if self.tablero is None:
            return
        for fila in range(self.filas):
            for columna in range(self.columnas):
                if self.tablero.es_mina(fila, columna):
                    self.tablero.reveladas.add((fila, columna))
                    self._actualizar_apariencia_casilla(fila, columna)

    def _marcar_banderas_en_todas_las_minas(self) -> None:
        """Al ganar, coloca bandera en cada mina para un cierre visual claro."""
        if self.tablero is None:
            return
        for posicion in self.tablero.minas:
            self.tablero.banderas.add(posicion)
        for fila in range(self.filas):
            for columna in range(self.columnas):
                self._actualizar_apariencia_casilla(fila, columna)

    def ejecutar(self) -> None:
        """Entra en el bucle principal de eventos de Tkinter."""
        self.ventana_principal.mainloop()


def ejecutar() -> None:
    """Crea la aplicación y la muestra."""
    app = AplicacionBuscaminas()
    app.ejecutar()
