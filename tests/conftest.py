"""Shared test helpers for building small hand-placed Boards."""

from hive.board import Board
from hive.coordinates import AxialCoordinate
from hive.pieces import BugType, Color, Piece

W = Color.WHITE
B = Color.BLACK


def cell(q: int, r: int) -> AxialCoordinate:
    return AxialCoordinate(q, r)


def piece(color: Color, bug_type: BugType, number: int | None = None) -> Piece:
    return Piece(color, bug_type, number)


def board_with(*placements: tuple[Piece, AxialCoordinate]) -> Board:
    """A Board with each (Piece, Cell) placed in order (later entries stack on earlier ones)."""
    board = Board()
    for placed_piece, at in placements:
        board.place(at, placed_piece)
    return board
