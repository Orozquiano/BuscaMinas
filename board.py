"""Generación del tablero, revelado en cascada y condición de victoria."""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Deque, List, Optional, Set, Tuple


Cell = Tuple[int, int]


class GameStatus(Enum):
    """Estado de la partida."""

    PLAYING = auto()
    WON = auto()
    LOST = auto()


@dataclass
class RevealResult:
    """Resultado de intentar revelar una casilla."""

    status: GameStatus
    newly_revealed: List[Cell] = field(default_factory=list)
    hit_mine: Optional[Cell] = None


class Board:
    """Tablero de buscaminas con minas colocadas tras el primer clic."""

    def __init__(self, rows: int, cols: int, mine_count: int) -> None:
        if rows < 1 or cols < 1:
            raise ValueError("El tablero debe tener al menos 1 fila y 1 columna.")
        max_mines = rows * cols - 1
        if mine_count < 1 or mine_count > max_mines:
            raise ValueError(f"mine_count debe estar entre 1 y {max_mines}.")
        self.rows = rows
        self.cols = cols
        self.mine_count = mine_count
        self._mines: Set[Cell] = set()
        self._generated = False
        self.revealed: Set[Cell] = set()
        self.flags: Set[Cell] = set()
        self.status = GameStatus.PLAYING

    def neighbor_mines(self, r: int, c: int) -> int:
        """Cuenta minas en las 8 casillas adyacentes (no cuenta la propia)."""
        total = 0
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    if (nr, nc) in self._mines:
                        total += 1
        return total

    def _place_mines(self, safe_r: int, safe_c: int) -> None:
        """Coloca minas evitando la casilla inicial y sus 8 vecinas."""
        safe: Set[Cell] = {(safe_r, safe_c)}
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = safe_r + dr, safe_c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    safe.add((nr, nc))
        candidates = [
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if (r, c) not in safe
        ]
        count = min(self.mine_count, len(candidates))
        self._mines = set(random.sample(candidates, count))
        self._generated = True

    def toggle_flag(self, r: int, c: int) -> bool:
        """
        Activa o desactiva bandera en una casilla no revelada.
        @returns True si el estado de banderas cambió.
        """
        if self.status != GameStatus.PLAYING:
            return False
        if (r, c) in self.revealed:
            return False
        if (r, c) in self.flags:
            self.flags.remove((r, c))
        else:
            self.flags.add((r, c))
        return True

    def reveal(self, r: int, c: int) -> RevealResult:
        """Revela una casilla; la primera genera el tablero (zona segura)."""
        if self.status != GameStatus.PLAYING:
            return RevealResult(status=self.status)

        if not self._generated:
            self._place_mines(r, c)

        if (r, c) in self.flags:
            return RevealResult(status=GameStatus.PLAYING)

        if (r, c) in self.revealed:
            return RevealResult(status=GameStatus.PLAYING)

        if (r, c) in self._mines:
            self.revealed.add((r, c))
            self.status = GameStatus.LOST
            return RevealResult(
                status=GameStatus.LOST,
                newly_revealed=[(r, c)],
                hit_mine=(r, c),
            )

        newly: List[Cell] = []
        queue: Deque[Cell] = deque()
        queue.append((r, c))

        while queue:
            cr, cc = queue.popleft()
            if (cr, cc) in self.revealed or (cr, cc) in self.flags:
                continue
            if (cr, cc) in self._mines:
                continue
            self.revealed.add((cr, cc))
            newly.append((cr, cc))
            if self.neighbor_mines(cr, cc) != 0:
                continue
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        if (nr, nc) not in self.revealed and (nr, nc) not in self.flags:
                            queue.append((nr, nc))

        if self._check_win():
            self.status = GameStatus.WON

        return RevealResult(status=self.status, newly_revealed=newly)

    def _check_win(self) -> bool:
        safe_total = self.rows * self.cols - len(self._mines)
        return len(self.revealed) >= safe_total

    def chord_reveal(self, r: int, c: int) -> RevealResult:
        """
        Clic con ambos botones (o central): si el número coincide con banderas
        adyacentes, revela el resto de vecinos no marcados.
        """
        if self.status != GameStatus.PLAYING or not self._generated:
            return RevealResult(status=self.status)
        if (r, c) not in self.revealed or (r, c) in self._mines:
            return RevealResult(status=GameStatus.PLAYING)

        n = self.neighbor_mines(r, c)
        neighbors = []
        flags_adj = 0
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    neighbors.append((nr, nc))
                    if (nr, nc) in self.flags:
                        flags_adj += 1

        if flags_adj != n:
            return RevealResult(status=GameStatus.PLAYING)

        combined = RevealResult(status=GameStatus.PLAYING, newly_revealed=[])
        for nr, nc in neighbors:
            if (nr, nc) in self.revealed or (nr, nc) in self.flags:
                continue
            part = self.reveal(nr, nc)
            combined.newly_revealed.extend(part.newly_revealed)
            if part.hit_mine:
                combined.hit_mine = part.hit_mine
            combined.status = part.status
        return combined

    @property
    def mines(self) -> Set[Cell]:
        return set(self._mines)

    def is_mine(self, r: int, c: int) -> bool:
        return (r, c) in self._mines
