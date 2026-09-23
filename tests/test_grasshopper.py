"""Grasshopper: jumps in a straight line over occupied Cells, ignoring the Freedom to Move Rule."""

from conftest import B, W, board_with, piece

from hive.coordinates import AxialCoordinate as Cell
from hive.coordinates import common_neighbors
from hive.pieces import BugType
from hive.rules import movement_destinations


def test_grasshopper_jumps_over_one_piece_to_the_first_empty_cell() -> None:
    hopper = piece(W, BugType.GRASSHOPPER, 1)
    blocker = piece(B, BugType.QUEEN_BEE)
    board = board_with((hopper, Cell(0, 0)), (blocker, Cell(1, 0)))

    assert movement_destinations(board, hopper, None) == {Cell(2, 0)}


def test_grasshopper_jumps_over_several_contiguous_pieces() -> None:
    hopper = piece(W, BugType.GRASSHOPPER, 1)
    board = board_with(
        (hopper, Cell(0, 0)),
        (piece(B, BugType.QUEEN_BEE), Cell(1, 0)),
        (piece(B, BugType.BEETLE, 1), Cell(2, 0)),
    )

    assert movement_destinations(board, hopper, None) == {Cell(3, 0)}


def test_grasshopper_has_no_jump_in_a_direction_with_no_adjacent_piece() -> None:
    hopper = piece(W, BugType.GRASSHOPPER, 1)
    blocker = piece(B, BugType.QUEEN_BEE)
    board = board_with((hopper, Cell(0, 0)), (blocker, Cell(1, 0)))

    destinations = movement_destinations(board, hopper, None)
    assert len(destinations) == 1  # only the one direction with a piece to jump


def test_grasshopper_ignores_the_freedom_to_move_gate() -> None:
    # Both cells flanking the origin->east edge are occupied, which would
    # block an ordinary slide — but the Grasshopper jumps, so it's exempt.
    origin = Cell(0, 0)
    east = origin.neighbors()[0][1]
    landing = east.neighbor(origin.direction_to(east))
    flank_a, flank_b = common_neighbors(origin, east)

    hopper = piece(W, BugType.GRASSHOPPER, 1)
    board = board_with(
        (hopper, origin),
        (piece(B, BugType.QUEEN_BEE), east),
        (piece(B, BugType.SOLDIER_ANT, 1), flank_a),
        (piece(B, BugType.SOLDIER_ANT, 2), flank_b),
    )

    assert landing in movement_destinations(board, hopper, None)
