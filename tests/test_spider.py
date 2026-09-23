"""Spider: exactly three slides, never revisiting a Cell within the same Move."""

from conftest import B, W, board_with, piece

from hive.coordinates import AxialCoordinate as Cell
from hive.pieces import BugType
from hive.rules import movement_destinations


def test_spider_orbiting_a_single_piece_three_steps_lands_at_the_antipode() -> None:
    # Orbiting a single Piece, the two possible directions (clockwise and
    # counter-clockwise) are each fully forced (revisiting is the only other
    # option at every step but the first) and, since three is half of the
    # Cell's six neighbors, both directions reach the same far side.
    center = piece(B, BugType.QUEEN_BEE)
    spider = piece(W, BugType.SPIDER, 1)
    board = board_with((center, Cell(0, 0)), (spider, Cell(1, 0)))

    assert movement_destinations(board, spider, None) == {Cell(-1, 0)}


def test_spider_along_a_two_piece_wall_diverges_by_starting_direction() -> None:
    wall_a = piece(B, BugType.QUEEN_BEE)
    wall_b = piece(B, BugType.BEETLE, 1)
    spider = piece(W, BugType.SPIDER, 1)
    board = board_with((wall_a, Cell(0, 0)), (wall_b, Cell(1, 0)), (spider, Cell(2, -1)))

    assert movement_destinations(board, spider, None) == {Cell(-1, 0), Cell(0, 1)}


def test_spider_never_ends_its_move_back_at_its_own_origin() -> None:
    center = piece(B, BugType.QUEEN_BEE)
    spider = piece(W, BugType.SPIDER, 1)
    board = board_with((center, Cell(0, 0)), (spider, Cell(1, 0)))

    assert Cell(1, 0) not in movement_destinations(board, spider, None)
