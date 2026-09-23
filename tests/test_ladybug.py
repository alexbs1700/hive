"""Ladybug: exactly two climbing steps across the Hive's surface, then one step down."""

from conftest import B, W, board_with, piece

from hive.coordinates import AxialCoordinate as Cell
from hive.pieces import BugType
from hive.rules import movement_destinations


def test_ladybug_needs_two_distinct_pieces_to_climb_across() -> None:
    # A single-piece Hive can't support two climbing steps that don't
    # backtrack onto an empty (and thus un-climbable) origin, so there's
    # nowhere legal to go.
    lone = piece(B, BugType.QUEEN_BEE)
    ladybug = piece(W, BugType.LADYBUG)
    board = board_with((lone, Cell(0, 0)), (ladybug, Cell(1, 0)))

    assert movement_destinations(board, ladybug, None) == set()


def test_ladybug_climbs_two_pieces_then_descends_to_an_empty_cell() -> None:
    first = piece(B, BugType.QUEEN_BEE)
    second = piece(B, BugType.BEETLE, 1)
    ladybug = piece(W, BugType.LADYBUG)
    board = board_with((first, Cell(0, 0)), (second, Cell(1, -1)), (ladybug, Cell(1, 0)))

    destinations = movement_destinations(board, ladybug, None)
    assert destinations == {
        Cell(2, -1),
        Cell(2, -2),
        Cell(1, -2),
        Cell(0, -1),
        Cell(-1, 0),
        Cell(-1, 1),
        Cell(0, 1),
    }


def test_ladybug_never_ends_its_move_back_at_its_own_origin() -> None:
    first = piece(B, BugType.QUEEN_BEE)
    second = piece(B, BugType.BEETLE, 1)
    ladybug = piece(W, BugType.LADYBUG)
    board = board_with((first, Cell(0, 0)), (second, Cell(1, -1)), (ladybug, Cell(1, 0)))

    assert Cell(1, 0) not in movement_destinations(board, ladybug, None)


def test_ladybug_cannot_end_its_move_on_top_of_a_piece() -> None:
    first = piece(B, BugType.QUEEN_BEE)
    second = piece(B, BugType.BEETLE, 1)
    ladybug = piece(W, BugType.LADYBUG)
    board = board_with((first, Cell(0, 0)), (second, Cell(1, -1)), (ladybug, Cell(1, 0)))

    destinations = movement_destinations(board, ladybug, None)
    assert Cell(0, 0) not in destinations
    assert Cell(1, -1) not in destinations
