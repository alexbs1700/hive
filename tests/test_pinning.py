"""Pinned: covered, the Last-Moved Piece, or a One Hive Rule cut vertex."""

from conftest import B, W, board_with, piece

from hive.coordinates import AxialCoordinate as Cell
from hive.pieces import BugType
from hive.rules import is_pinned, movement_destinations


def test_a_cut_vertex_piece_is_pinned() -> None:
    left = piece(W, BugType.QUEEN_BEE)
    middle = piece(W, BugType.SOLDIER_ANT, 1)
    right = piece(B, BugType.QUEEN_BEE)
    board = board_with((left, Cell(0, 0)), (middle, Cell(1, 0)), (right, Cell(2, 0)))

    assert is_pinned(board, middle, None)
    assert movement_destinations(board, middle, None) == set()


def test_an_endpoint_piece_is_not_pinned_by_the_one_hive_rule() -> None:
    left = piece(W, BugType.QUEEN_BEE)
    middle = piece(W, BugType.SOLDIER_ANT, 1)
    right = piece(B, BugType.QUEEN_BEE)
    board = board_with((left, Cell(0, 0)), (middle, Cell(1, 0)), (right, Cell(2, 0)))

    assert not is_pinned(board, left, None)


def test_the_last_moved_piece_is_pinned_regardless_of_connectivity() -> None:
    left = piece(W, BugType.QUEEN_BEE)
    right = piece(B, BugType.QUEEN_BEE)
    board = board_with((left, Cell(0, 0)), (right, Cell(1, 0)))

    assert is_pinned(board, left, last_moved_piece=left)
    assert movement_destinations(board, left, last_moved_piece=left) == set()


def test_a_covered_piece_is_pinned() -> None:
    bottom = piece(W, BugType.SOLDIER_ANT, 1)
    top = piece(W, BugType.BEETLE, 1)
    board = board_with((bottom, Cell(0, 0)), (top, Cell(0, 0)))

    assert is_pinned(board, bottom, None)
    assert movement_destinations(board, bottom, None) == set()


def test_lifting_the_top_of_a_taller_stack_never_breaks_the_one_hive_rule() -> None:
    left = piece(W, BugType.QUEEN_BEE)
    middle_bottom = piece(W, BugType.SOLDIER_ANT, 1)
    middle_top = piece(W, BugType.BEETLE, 1)
    right = piece(B, BugType.QUEEN_BEE)
    board = board_with(
        (left, Cell(0, 0)),
        (middle_bottom, Cell(1, 0)),
        (middle_top, Cell(1, 0)),
        (right, Cell(2, 0)),
    )

    assert not is_pinned(board, middle_top, None)
