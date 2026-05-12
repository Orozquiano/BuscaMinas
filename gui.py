"""Interfaz Tkinter del buscaminas."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from typing import Callable, Optional, Tuple

from minesweeper.board import Board, GameStatus, RevealResult


# Principiante, Intermedio, Experto (filas, columnas, minas)
PRESETS: Tuple[Tuple[str, int, int, int], ...] = (
    ("Principiante (9×9, 10)", 9, 9, 10),
    ("Intermedio (16×16, 40)", 16, 16, 40),
    ("Experto (16×30, 99)", 16, 30, 99),
)

NUMBER_COLORS = (
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


class MinesweeperApp:
    """Ventana principal: rejilla de botones, temporizador y menú de niveles."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Buscaminas")
        self.rows, self.cols, self.mines = 9, 9, 10
        self.board: Optional[Board] = None
        self.cells: list[list[tk.Button]] = []
        self._timer_id: Optional[str] = None
        self._seconds = 0
        self._started = False

        self._build_menu()
        self._build_toolbar()
        self._frame = ttk.Frame(self.root, padding=4)
        self._frame.pack(fill=tk.BOTH, expand=True)
        self.new_game()

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        game_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Juego", menu=game_menu)
        game_menu.add_command(label="Nueva partida", command=self.new_game, accelerator="F2")
        game_menu.add_separator()
        for label, r, c, m in PRESETS:
            game_menu.add_command(
                label=label,
                command=lambda rr=r, cc=c, mm=m: self._set_preset(rr, cc, mm),
            )
        game_menu.add_command(label="Personalizado…", command=self._custom_preset)
        game_menu.add_separator()
        game_menu.add_command(label="Salir", command=self.root.quit)
        self.root.bind("<F2>", lambda e: self.new_game())

    def _build_toolbar(self) -> None:
        bar = ttk.Frame(self.root, padding=(8, 4))
        bar.pack(fill=tk.X)
        self.lbl_mines = ttk.Label(bar, text="Minas: 10", width=14)
        self.lbl_mines.pack(side=tk.LEFT)
        self.btn_reset = ttk.Button(bar, text="Reiniciar", command=self.new_game)
        self.btn_reset.pack(side=tk.LEFT, padx=8)
        self.lbl_time = ttk.Label(bar, text="Tiempo: 0", width=12)
        self.lbl_time.pack(side=tk.LEFT)

    def _set_preset(self, rows: int, cols: int, mines: int) -> None:
        self.rows, self.cols, self.mines = rows, cols, mines
        self.new_game()

    def _custom_preset(self) -> None:
        r = simpledialog.askinteger("Filas", "Número de filas (5-30):", minvalue=5, maxvalue=30)
        if r is None:
            return
        c = simpledialog.askinteger("Columnas", "Número de columnas (5-40):", minvalue=5, maxvalue=40)
        if c is None:
            return
        max_m = r * c - 1
        m = simpledialog.askinteger(
            "Minas",
            f"Número de minas (1-{max_m}):",
            minvalue=1,
            maxvalue=max_m,
        )
        if m is None:
            return
        self.rows, self.cols, self.mines = r, c, m
        self.new_game()

    def _stop_timer(self) -> None:
        if self._timer_id is not None:
            self.root.after_cancel(self._timer_id)
            self._timer_id = None

    def _tick_timer(self) -> None:
        if self.board is None or self.board.status != GameStatus.PLAYING:
            return
        self._seconds += 1
        self.lbl_time.config(text=f"Tiempo: {self._seconds}")
        self._timer_id = self.root.after(1000, self._tick_timer)

    def _maybe_start_timer(self) -> None:
        if self._started:
            return
        self._started = True
        self._seconds = 0
        self.lbl_time.config(text="Tiempo: 0")
        self._stop_timer()
        self._timer_id = self.root.after(1000, self._tick_timer)

    def new_game(self) -> None:
        self._stop_timer()
        self._seconds = 0
        self._started = False
        self.lbl_time.config(text="Tiempo: 0")
        self.board = Board(self.rows, self.cols, self.mines)
        self.lbl_mines.config(text=f"Minas: {self.mines}")
        for w in self._frame.winfo_children():
            w.destroy()
        self.cells = []
        for r in range(self.rows):
            row_widgets: list[tk.Button] = []
            for c in range(self.cols):
                btn = tk.Button(
                    self._frame,
                    width=2,
                    height=1,
                    relief=tk.RAISED,
                    font=("Segoe UI", 10, "bold"),
                )
                btn.grid(row=r, column=c, padx=1, pady=1, sticky="nsew")
                btn.bind("<Button-1>", self._make_left_handler(r, c))
                btn.bind("<Button-3>", self._make_right_handler(r, c))
                btn.bind("<Button-2>", self._make_chord_handler(r, c))
                row_widgets.append(btn)
            self.cells.append(row_widgets)
        for i in range(self.rows):
            self._frame.rowconfigure(i, weight=1)
        for j in range(self.cols):
            self._frame.columnconfigure(j, weight=1)

    def _make_left_handler(self, r: int, c: int) -> Callable[[tk.Event], None]:
        def handler(_: tk.Event) -> None:
            if self.board is None:
                return
            self._maybe_start_timer()
            res = self.board.reveal(r, c)
            self._refresh_after_reveal(res)
        return handler

    def _make_right_handler(self, r: int, c: int) -> Callable[[tk.Event], None]:
        def handler(_: tk.Event) -> None:
            if self.board is None:
                return
            if self.board.toggle_flag(r, c):
                self._update_cell_display(r, c)
                remaining = self.mines - len(self.board.flags)
                self.lbl_mines.config(text=f"Minas: {remaining}")
        return handler

    def _make_chord_handler(self, r: int, c: int) -> Callable[[tk.Event], None]:
        def handler(_: tk.Event) -> None:
            if self.board is None:
                return
            res = self.board.chord_reveal(r, c)
            self._refresh_after_reveal(res)
        return handler

    def _refresh_after_reveal(self, res: RevealResult) -> None:
        for rr, cc in res.newly_revealed:
            self._update_cell_display(rr, cc)
        if res.status == GameStatus.LOST:
            self._stop_timer()
            self._reveal_all_mines()
            messagebox.showinfo("Fin", "¡Has pisado una mina! Partida perdida.")
        elif res.status == GameStatus.WON:
            self._stop_timer()
            self._flag_all_mines()
            messagebox.showinfo("Fin", "¡Has despejado todo! Victoria.")

    def _update_cell_display(self, r: int, c: int) -> None:
        if self.board is None:
            return
        btn = self.cells[r][c]
        if (r, c) in self.board.revealed:
            if self.board.is_mine(r, c):
                btn.config(text="*", bg="#FFAAAA", fg="#000000", relief=tk.SUNKEN, state=tk.DISABLED)
            else:
                n = self.board.neighbor_mines(r, c)
                txt = "" if n == 0 else str(n)
                fg = NUMBER_COLORS[n] if 0 <= n < len(NUMBER_COLORS) else "#000000"
                btn.config(
                    text=txt,
                    fg=fg,
                    bg="#DDDDDD" if n else "#EEEEEE",
                    relief=tk.SUNKEN,
                    state=tk.DISABLED,
                )
        elif (r, c) in self.board.flags:
            btn.config(text="⚑", fg="#CC0000", bg="#DDDDDD", state=tk.NORMAL)
        else:
            btn.config(text="", fg="#000000", bg="#F0F0F0", relief=tk.RAISED, state=tk.NORMAL)

    def _reveal_all_mines(self) -> None:
        if self.board is None:
            return
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board.is_mine(r, c):
                    self.board.revealed.add((r, c))
                    self._update_cell_display(r, c)

    def _flag_all_mines(self) -> None:
        if self.board is None:
            return
        for pos in self.board.mines:
            self.board.flags.add(pos)
        for r in range(self.rows):
            for c in range(self.cols):
                self._update_cell_display(r, c)

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = MinesweeperApp()
    app.run()
