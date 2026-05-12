"""
Lógica del buscaminas: colocación de minas, revelado en cascada,
banderas y revelación por acorde (clic central sobre un número).
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Deque, List, Optional, Set, Tuple

# Par (fila, columna) en el tablero.
Casilla = Tuple[int, int]


class EstadoPartida(Enum):
    """Indica si la partida sigue activa o ya terminó."""

    JUGANDO = auto()
    GANADO = auto()
    PERDIDO = auto()


@dataclass
class ResultadoRevelado:
    """Información devuelta al intentar revelar una o varias casillas."""

    # Estado de la partida tras la acción.
    estado: EstadoPartida
    # Casillas que pasan a estar visibles en este turno (puede ser varias por la cascada).
    casillas_reveladas: List[Casilla] = field(default_factory=list)
    # Si se perdió, coordenadas de la mina pisada (si aplica).
    casilla_mina: Optional[Casilla] = None


class Tablero:
    """Tablero: las minas se colocan después del primer clic (zona segura)."""

    def __init__(self, filas: int, columnas: int, cantidad_minas: int) -> None:
        if filas < 1 or columnas < 1:
            raise ValueError("El tablero debe tener al menos 1 fila y 1 columna.")
        max_minas = filas * columnas - 1
        if cantidad_minas < 1 or cantidad_minas > max_minas:
            raise ValueError(f"cantidad_minas debe estar entre 1 y {max_minas}.")
        self.filas = filas
        self.columnas = columnas
        self.cantidad_minas = cantidad_minas
        # Conjunto de posiciones donde hay mina (se rellena al generar).
        self._minas: Set[Casilla] = set()
        # True cuando ya se colocaron las minas (tras el primer revelado).
        self._generado = False
        # Casillas ya descubiertas por el jugador.
        self.reveladas: Set[Casilla] = set()
        # Casillas marcadas con bandera.
        self.banderas: Set[Casilla] = set()
        self.estado = EstadoPartida.JUGANDO

    def contar_minas_adyacentes(self, fila: int, columna: int) -> int:
        """Cuenta cuántas minas hay en las 8 casillas vecinas (no cuenta la propia)."""
        total = 0
        for delta_f in (-1, 0, 1):
            for delta_c in (-1, 0, 1):
                if delta_f == 0 and delta_c == 0:
                    continue
                vec_f, vec_c = fila + delta_f, columna + delta_c
                if 0 <= vec_f < self.filas and 0 <= vec_c < self.columnas:
                    if (vec_f, vec_c) in self._minas:
                        total += 1
        return total

    def _colocar_minas(self, fila_segura: int, columna_segura: int) -> None:
        """Elige posiciones aleatorias de minas evitando la primera casilla y sus vecinas."""
        zona_segura: Set[Casilla] = {(fila_segura, columna_segura)}
        for delta_f in (-1, 0, 1):
            for delta_c in (-1, 0, 1):
                vf, vc = fila_segura + delta_f, columna_segura + delta_c
                if 0 <= vf < self.filas and 0 <= vc < self.columnas:
                    zona_segura.add((vf, vc))
        candidatas = [
            (f, c)
            for f in range(self.filas)
            for c in range(self.columnas)
            if (f, c) not in zona_segura
        ]
        cuantas = min(self.cantidad_minas, len(candidatas))
        self._minas = set(random.sample(candidatas, cuantas))
        self._generado = True

    def alternar_bandera(self, fila: int, columna: int) -> bool:
        """
        Pone o quita una bandera en una casilla tapada.
        Devuelve True si hubo cambio (False si la partida terminó o ya estaba revelada).
        """
        if self.estado != EstadoPartida.JUGANDO:
            return False
        if (fila, columna) in self.reveladas:
            return False
        if (fila, columna) in self.banderas:
            self.banderas.remove((fila, columna))
        else:
            self.banderas.add((fila, columna))
        return True

    def revelar(self, fila: int, columna: int) -> ResultadoRevelado:
        """
        Descubre una casilla. Si es el primer revelado, genera el tablero con zona segura.
        Las casillas con 0 minas vecinas abren en cascada el vecindario.
        """
        if self.estado != EstadoPartida.JUGANDO:
            return ResultadoRevelado(estado=self.estado)

        if not self._generado:
            self._colocar_minas(fila, columna)

        if (fila, columna) in self.banderas:
            return ResultadoRevelado(estado=EstadoPartida.JUGANDO)

        if (fila, columna) in self.reveladas:
            return ResultadoRevelado(estado=EstadoPartida.JUGANDO)

        if (fila, columna) in self._minas:
            self.reveladas.add((fila, columna))
            self.estado = EstadoPartida.PERDIDO
            return ResultadoRevelado(
                estado=EstadoPartida.PERDIDO,
                casillas_reveladas=[(fila, columna)],
                casilla_mina=(fila, columna),
            )

        # Cola para expandir todas las casillas “vacías” (0 minas alrededor) contiguas.
        nuevas: List[Casilla] = []
        cola: Deque[Casilla] = deque()
        cola.append((fila, columna))

        while cola:
            f_actual, c_actual = cola.popleft()
            if (f_actual, c_actual) in self.reveladas or (f_actual, c_actual) in self.banderas:
                continue
            if (f_actual, c_actual) in self._minas:
                continue
            self.reveladas.add((f_actual, c_actual))
            nuevas.append((f_actual, c_actual))
            # Si hay número > 0, no se expande más desde esta casilla.
            if self.contar_minas_adyacentes(f_actual, c_actual) != 0:
                continue
            for delta_f in (-1, 0, 1):
                for delta_c in (-1, 0, 1):
                    if delta_f == 0 and delta_c == 0:
                        continue
                    vec_f, vec_c = f_actual + delta_f, c_actual + delta_c
                    if 0 <= vec_f < self.filas and 0 <= vec_c < self.columnas:
                        if (vec_f, vec_c) not in self.reveladas and (vec_f, vec_c) not in self.banderas:
                            cola.append((vec_f, vec_c))

        if self._comprobar_victoria():
            self.estado = EstadoPartida.GANADO

        return ResultadoRevelado(estado=self.estado, casillas_reveladas=nuevas)

    def _comprobar_victoria(self) -> bool:
        """True si todas las casillas sin mina están reveladas."""
        casillas_seguras = self.filas * self.columnas - len(self._minas)
        return len(self.reveladas) >= casillas_seguras

    def revelar_acorde(self, fila: int, columna: int) -> ResultadoRevelado:
        """
        Revelado por acorde: sobre una casilla ya revelada con número,
        si las banderas alrededor coinciden con ese número, revela el resto de vecinos.
        """
        if self.estado != EstadoPartida.JUGANDO or not self._generado:
            return ResultadoRevelado(estado=self.estado)
        if (fila, columna) not in self.reveladas or (fila, columna) in self._minas:
            return ResultadoRevelado(estado=EstadoPartida.JUGANDO)

        numero = self.contar_minas_adyacentes(fila, columna)
        vecinas: List[Casilla] = []
        banderas_alrededor = 0
        for delta_f in (-1, 0, 1):
            for delta_c in (-1, 0, 1):
                if delta_f == 0 and delta_c == 0:
                    continue
                vf, vc = fila + delta_f, columna + delta_c
                if 0 <= vf < self.filas and 0 <= vc < self.columnas:
                    vecinas.append((vf, vc))
                    if (vf, vc) in self.banderas:
                        banderas_alrededor += 1

        if banderas_alrededor != numero:
            return ResultadoRevelado(estado=EstadoPartida.JUGANDO)

        acumulado = ResultadoRevelado(estado=EstadoPartida.JUGANDO, casillas_reveladas=[])
        for vf, vc in vecinas:
            if (vf, vc) in self.reveladas or (vf, vc) in self.banderas:
                continue
            trozo = self.revelar(vf, vc)
            acumulado.casillas_reveladas.extend(trozo.casillas_reveladas)
            if trozo.casilla_mina:
                acumulado.casilla_mina = trozo.casilla_mina
            acumulado.estado = trozo.estado
        return acumulado

    @property
    def minas(self) -> Set[Casilla]:
        """Copia del conjunto de coordenadas con mina (solo lectura lógica)."""
        return set(self._minas)

    def es_mina(self, fila: int, columna: int) -> bool:
        """Indica si en esa posición hay una mina."""
        return (fila, columna) in self._minas
