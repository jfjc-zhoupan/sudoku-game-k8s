"""Sudoku puzzle generation and validation (shared by desktop and web)."""

from __future__ import annotations

import random
from typing import List, Optional, Tuple

Board = List[List[int]]
SIZE = 9
BOX = 3

DIFFICULTY = {
    "Easy": 36,
    "Medium": 46,
    "Hard": 54,
}


def find_empty(board: Board) -> Optional[Tuple[int, int]]:
    for r in range(SIZE):
        for c in range(SIZE):
            if board[r][c] == 0:
                return r, c
    return None


def is_valid(board: Board, row: int, col: int, num: int) -> bool:
    if any(board[row][c] == num for c in range(SIZE) if c != col):
        return False
    if any(board[r][col] == num for r in range(SIZE) if r != row):
        return False
    br, bc = (row // BOX) * BOX, (col // BOX) * BOX
    for r in range(br, br + BOX):
        for c in range(bc, bc + BOX):
            if (r, c) != (row, col) and board[r][c] == num:
                return False
    return True


def solve(board: Board) -> bool:
    empty = find_empty(board)
    if empty is None:
        return True
    row, col = empty
    nums = list(range(1, 10))
    random.shuffle(nums)
    for num in nums:
        if is_valid(board, row, col, num):
            board[row][col] = num
            if solve(board):
                return True
            board[row][col] = 0
    return False


def generate_full_board() -> Board:
    board = [[0] * SIZE for _ in range(SIZE)]
    solve(board)
    return board


def copy_board(board: Board) -> Board:
    return [row[:] for row in board]


def unique_solution(board: Board) -> bool:
    count = [0]

    def search(b: Board) -> bool:
        empty = find_empty(b)
        if empty is None:
            count[0] += 1
            return count[0] > 1
        row, col = empty
        for num in range(1, 10):
            if is_valid(b, row, col, num):
                b[row][col] = num
                if search(b):
                    return True
                b[row][col] = 0
        return False

    search(board)
    return count[0] == 1


def make_puzzle(full: Board, holes: int) -> Board:
    puzzle = copy_board(full)
    positions = [(r, c) for r in range(SIZE) for c in range(SIZE)]
    random.shuffle(positions)
    removed = 0
    for r, c in positions:
        if removed >= holes:
            break
        backup = puzzle[r][c]
        puzzle[r][c] = 0
        test = copy_board(puzzle)
        if unique_solution(test):
            removed += 1
        else:
            puzzle[r][c] = backup
    return puzzle


def new_puzzle(difficulty: str) -> tuple[Board, Board]:
    name = difficulty if difficulty in DIFFICULTY else "Easy"
    full = generate_full_board()
    puzzle = make_puzzle(full, DIFFICULTY[name])
    return puzzle, full
