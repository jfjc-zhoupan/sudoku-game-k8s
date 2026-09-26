"""Desktop Sudoku game with a tkinter GUI."""

from __future__ import annotations

import random
import tkinter as tk
from tkinter import messagebox, ttk
from typing import List, Optional, Tuple

from engine import (
    DIFFICULTY,
    Board,
    copy_board,
    is_valid,
    new_puzzle,
    SIZE,
)


class SudokuApp:
    BG = "#f4f1ea"
    GRID_BG = "#2c3e50"
    GIVEN_BG = "#e8e4d9"
    EMPTY_BG = "#ffffff"
    SELECTED_BG = "#d6eaf8"
    SAME_BG = "#fdebd0"
    ERROR_BG = "#f5b7b1"
    GIVEN_FG = "#1a252f"
    ENTRY_FG = "#1f618d"
    ERROR_FG = "#922b21"

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Sudoku")
        self.root.resizable(False, False)
        self.root.configure(bg=self.BG)

        self.solution: Board = [[0] * SIZE for _ in range(SIZE)]
        self.puzzle: Board = [[0] * SIZE for _ in range(SIZE)]
        self.board: Board = [[0] * SIZE for _ in range(SIZE)]
        self.given = [[False] * SIZE for _ in range(SIZE)]
        self.selected: Optional[Tuple[int, int]] = None
        self.cells: List[List[tk.Label]] = []

        self._build_ui()
        self.new_game()

    def _build_ui(self) -> None:
        header = tk.Frame(self.root, bg=self.BG)
        header.pack(fill="x", padx=16, pady=(16, 8))

        tk.Label(
            header,
            text="Sudoku",
            font=("Segoe UI", 22, "bold"),
            bg=self.BG,
            fg="#1a252f",
        ).pack(side="left")

        controls = tk.Frame(header, bg=self.BG)
        controls.pack(side="right")

        tk.Label(controls, text="Difficulty", bg=self.BG, font=("Segoe UI", 10)).pack(
            side="left", padx=(0, 6)
        )
        self.difficulty = tk.StringVar(value="Easy")
        combo = ttk.Combobox(
            controls,
            textvariable=self.difficulty,
            values=list(DIFFICULTY.keys()),
            state="readonly",
            width=8,
        )
        combo.pack(side="left", padx=(0, 8))

        tk.Button(controls, text="New Game", command=self.new_game, width=10).pack(
            side="left", padx=2
        )
        tk.Button(controls, text="Check", command=self.check_board, width=8).pack(
            side="left", padx=2
        )
        tk.Button(controls, text="Hint", command=self.give_hint, width=8).pack(
            side="left", padx=2
        )

        grid_wrap = tk.Frame(self.root, bg=self.GRID_BG, padx=3, pady=3)
        grid_wrap.pack(padx=16, pady=8)

        self.cells = []
        for r in range(SIZE):
            row_labels = []
            for c in range(SIZE):
                pad_x = (0, 3) if c in (2, 5) else (0, 1)
                pad_y = (0, 3) if r in (2, 5) else (0, 1)
                lbl = tk.Label(
                    grid_wrap,
                    text="",
                    width=3,
                    height=1,
                    font=("Segoe UI", 18, "bold"),
                    relief="flat",
                    bg=self.EMPTY_BG,
                    cursor="hand2",
                )
                lbl.grid(row=r, column=c, padx=pad_x, pady=pad_y, ipady=10)
                lbl.bind("<Button-1>", lambda _e, row=r, col=c: self.select_cell(row, col))
                row_labels.append(lbl)
            self.cells.append(row_labels)

        pad = tk.Frame(self.root, bg=self.BG)
        pad.pack(pady=(4, 8))
        for n in range(1, 10):
            tk.Button(
                pad,
                text=str(n),
                width=4,
                height=2,
                font=("Segoe UI", 12, "bold"),
                command=lambda num=n: self.enter_number(num),
            ).grid(row=0, column=n - 1, padx=3)

        tk.Button(pad, text="Erase", width=8, height=2, command=self.erase).grid(
            row=0, column=9, padx=6
        )

        self.status = tk.Label(
            self.root,
            text="Fill the grid so every row, column, and 3×3 box has 1–9.",
            bg=self.BG,
            font=("Segoe UI", 10),
            fg="#34495e",
        )
        self.status.pack(pady=(0, 16))

        self.root.bind("<Key>", self.on_key)

    def new_game(self) -> None:
        self.status.config(text="Generating puzzle…")
        self.root.update_idletasks()
        self.puzzle, self.solution = new_puzzle(self.difficulty.get())
        self.board = copy_board(self.puzzle)
        self.given = [[self.puzzle[r][c] != 0 for c in range(SIZE)] for r in range(SIZE)]
        self.selected = None
        self.refresh()
        empty = sum(1 for r in range(SIZE) for c in range(SIZE) if self.board[r][c] == 0)
        self.status.config(text=f"New {self.difficulty.get()} puzzle — {empty} empty cells.")

    def select_cell(self, row: int, col: int) -> None:
        self.selected = (row, col)
        self.refresh()

    def enter_number(self, num: int) -> None:
        if self.selected is None:
            self.status.config(text="Select a cell first.")
            return
        row, col = self.selected
        if self.given[row][col]:
            self.status.config(text="That cell is given and cannot be changed.")
            return
        self.board[row][col] = num
        self.refresh()
        if self.is_complete():
            if self.board == self.solution:
                self.status.config(text="Solved — nice work!")
                messagebox.showinfo("Sudoku", "You solved the puzzle!")
            else:
                self.status.config(text="The grid is full, but something is off. Try Check.")

    def erase(self) -> None:
        if self.selected is None:
            return
        row, col = self.selected
        if self.given[row][col]:
            return
        self.board[row][col] = 0
        self.refresh()

    def on_key(self, event: tk.Event) -> None:
        if event.keysym in ("BackSpace", "Delete"):
            self.erase()
            return
        if event.char and event.char in "123456789":
            self.enter_number(int(event.char))

    def give_hint(self) -> None:
        empties = [
            (r, c)
            for r in range(SIZE)
            for c in range(SIZE)
            if self.board[r][c] == 0
        ]
        if not empties:
            self.status.config(text="No empty cells left.")
            return
        row, col = random.choice(empties)
        self.board[row][col] = self.solution[row][col]
        self.selected = (row, col)
        self.refresh()
        self.status.config(text=f"Hint placed at row {row + 1}, column {col + 1}.")
        if self.board == self.solution:
            messagebox.showinfo("Sudoku", "You solved the puzzle!")

    def check_board(self) -> None:
        errors = 0
        for r in range(SIZE):
            for c in range(SIZE):
                val = self.board[r][c]
                if val != 0 and val != self.solution[r][c]:
                    errors += 1
        if errors == 0:
            filled = sum(1 for r in range(SIZE) for c in range(SIZE) if self.board[r][c] != 0)
            if filled == SIZE * SIZE:
                self.status.config(text="Correct — puzzle complete!")
                messagebox.showinfo("Sudoku", "You solved the puzzle!")
            else:
                self.status.config(text="No mistakes so far. Keep going.")
        else:
            self.status.config(text=f"{errors} cell(s) don't match the solution.")
        self.refresh(show_errors=True)

    def is_complete(self) -> bool:
        return all(self.board[r][c] != 0 for r in range(SIZE) for c in range(SIZE))

    def refresh(self, show_errors: bool = False) -> None:
        sel_val = None
        if self.selected:
            sel_val = self.board[self.selected[0]][self.selected[1]]
            if sel_val == 0:
                sel_val = None

        for r in range(SIZE):
            for c in range(SIZE):
                val = self.board[r][c]
                lbl = self.cells[r][c]
                text = str(val) if val else ""
                fg = self.GIVEN_FG if self.given[r][c] else self.ENTRY_FG
                bg = self.GIVEN_BG if self.given[r][c] else self.EMPTY_BG

                if sel_val and val == sel_val:
                    bg = self.SAME_BG
                if self.selected == (r, c):
                    bg = self.SELECTED_BG
                if show_errors and val and val != self.solution[r][c]:
                    bg = self.ERROR_BG
                    fg = self.ERROR_FG
                elif val and not is_valid(self.board, r, c, val):
                    bg = self.ERROR_BG
                    fg = self.ERROR_FG

                lbl.config(text=text, bg=bg, fg=fg)


def main() -> None:
    root = tk.Tk()
    SudokuApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
