"""Placement adjacency: same-color-only, except each Player's very first Piece."""

from conftest import B, W, board_with, piece

from hive.coordinates import AxialCoordinate as Cell
from hive.pieces import BugType
from hive.rules import placement_destinations


def test_the_games_first_placement_is_always_the_origin() -> None:
    board = board_with()
    assert placement_destinations(board, W) == {Cell(0, 0)}


def test_a_players_own_first_placement_may_touch_the_opponent() -> None:
    white_queen = piece(W, BugType.QUEEN_BEE)
    board = board_with((white_queen, Cell(0, 0)))

    assert placement_destinations(board, B) == set(Cell(0, 0).neighbor_set())


def test_later_placements_must_touch_only_the_players_own_color() -> None:
    white_queen = piece(W, BugType.QUEEN_BEE)
    black_queen = piece(B, BugType.QUEEN_BEE)
    board = board_with((white_queen, Cell(0, 0)), (black_queen, Cell(1, 0)))

    assert placement_destinations(board, W) == {Cell(0, -1), Cell(-1, 0), Cell(-1, 1)}


def test_placement_never_targets_an_occupied_cell() -> None:
    white_queen = piece(W, BugType.QUEEN_BEE)
    black_queen = piece(B, BugType.QUEEN_BEE)
    board = board_with((white_queen, Cell(0, 0)), (black_queen, Cell(1, 0)))

    destinations = placement_destinations(board, W) | placement_destinations(board, B)
    assert Cell(0, 0) not in destinations
    assert Cell(1, 0) not in destinations
