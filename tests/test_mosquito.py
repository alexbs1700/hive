"""Mosquito: copies the movement of every distinct Bug Type it's touching."""

from conftest import B, W, board_with, piece

from hive.coordinates import AxialCoordinate as Cell
from hive.pieces import BugType
from hive.rules import movement_destinations


def test_mosquito_touching_only_mosquitoes_cannot_move() -> None:
    mosquito = piece(W, BugType.MOSQUITO)
    other_mosquito = piece(B, BugType.MOSQUITO)
    board = board_with((mosquito, Cell(0, 0)), (other_mosquito, Cell(1, 0)))

    assert movement_destinations(board, mosquito, None) == set()


def test_mosquito_copies_the_union_of_every_touched_bug_type() -> None:
    # Touching a Beetle and a Grasshopper, the Mosquito's options are the
    # union of what each of those would do from the same Cell: some
    # destinations only the Beetle-copy reaches (a climb), others only the
    # Grasshopper-copy reaches (a jump).
    beetle = piece(B, BugType.BEETLE, 1)
    grasshopper = piece(B, BugType.GRASSHOPPER, 1)
    mosquito = piece(W, BugType.MOSQUITO)
    board = board_with((beetle, Cell(0, 0)), (grasshopper, Cell(1, 0)), (mosquito, Cell(1, -1)))

    destinations = movement_destinations(board, mosquito, None)
    assert destinations == {
        Cell(0, 0),
        Cell(1, 0),
        Cell(-1, 1),
        Cell(0, -1),
        Cell(1, 1),
        Cell(2, -1),
    }


def test_mosquito_on_top_of_the_hive_moves_only_as_a_beetle() -> None:
    # The Mosquito climbed there (as a Beetle) to get on top, so it stays
    # locked into Beetle-only movement until it climbs back down — even
    # though it's touching a Grasshopper, whose pattern it would otherwise
    # be able to copy at ground level.
    base = piece(B, BugType.SOLDIER_ANT, 1)
    mosquito = piece(W, BugType.MOSQUITO)
    grasshopper = piece(B, BugType.GRASSHOPPER, 1)
    board = board_with((base, Cell(0, 0)), (mosquito, Cell(0, 0)), (grasshopper, Cell(1, 0)))

    destinations = movement_destinations(board, mosquito, None)
    assert destinations == set(Cell(0, 0).neighbor_set())
