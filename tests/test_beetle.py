"""Beetle: like the Queen Bee, but may also climb onto an occupied neighbor."""

from conftest import B, W, board_with, piece

from hive.coordinates import AxialCoordinate as Cell
from hive.coordinates import common_neighbors
from hive.pieces import BugType
from hive.rules import movement_destinations


def test_beetle_can_climb_onto_an_adjacent_occupied_cell() -> None:
    beetle = piece(W, BugType.BEETLE, 1)
    other = piece(B, BugType.QUEEN_BEE)
    board = board_with((beetle, Cell(0, 0)), (other, Cell(1, 0)))

    destinations = movement_destinations(board, beetle, None)
    assert destinations == {Cell(1, 0), Cell(1, -1), Cell(0, 1)}


def test_beetle_descent_is_blocked_only_in_the_gated_direction() -> None:
    # Beetle sits atop a two-piece stack at the origin. Both cells flanking
    # the origin->east edge are themselves two-high, pinching that one
    # direction shut; every other direction (including climbing straight
    # onto the two tall flanks) stays open.
    origin = Cell(0, 0)
    east = origin.neighbors()[0][1]
    flank_a, flank_b = common_neighbors(origin, east)

    remaining_at_origin = piece(B, BugType.SOLDIER_ANT, 1)
    beetle = piece(W, BugType.BEETLE, 1)
    board = board_with(
        (remaining_at_origin, origin),
        (beetle, origin),
        (piece(B, BugType.QUEEN_BEE), flank_a),
        (piece(B, BugType.BEETLE, 2), flank_a),
        (piece(W, BugType.QUEEN_BEE), flank_b),
        (piece(W, BugType.BEETLE, 2), flank_b),
    )

    destinations = movement_destinations(board, beetle, None)
    assert east not in destinations
    assert destinations == set(origin.neighbor_set()) - {east}
