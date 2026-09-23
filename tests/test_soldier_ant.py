"""Soldier Ant: unlimited ground slides, reaching anywhere along the Hive's perimeter."""

from conftest import B, W, board_with, piece

from hive.coordinates import AxialCoordinate as Cell
from hive.pieces import BugType
from hive.rules import movement_destinations


def test_ant_orbiting_a_single_piece_reaches_every_other_perimeter_cell() -> None:
    center = piece(B, BugType.QUEEN_BEE)
    ant = piece(W, BugType.SOLDIER_ANT, 1)
    board = board_with((center, Cell(0, 0)), (ant, Cell(1, 0)))

    destinations = movement_destinations(board, ant, None)
    assert destinations == set(Cell(0, 0).neighbor_set()) - {Cell(1, 0)}


def test_ant_cannot_climb_onto_an_occupied_cell() -> None:
    center = piece(B, BugType.QUEEN_BEE)
    blocker = piece(B, BugType.BEETLE, 1)
    ant = piece(W, BugType.SOLDIER_ANT, 1)
    board = board_with((center, Cell(0, 0)), (blocker, Cell(1, -1)), (ant, Cell(1, 0)))

    assert Cell(1, -1) not in movement_destinations(board, ant, None)
