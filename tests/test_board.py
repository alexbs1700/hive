"""Board occupancy, the One Hive Rule's cut-vertex check, and the Freedom to Move gate."""

from hive.board import Board
from hive.coordinates import AxialCoordinate
from hive.pieces import BugType, Color, Piece

ORIGIN = AxialCoordinate(0, 0)
QUEEN_W = Piece(Color.WHITE, BugType.QUEEN_BEE)
QUEEN_B = Piece(Color.BLACK, BugType.QUEEN_BEE)
BEETLE_W1 = Piece(Color.WHITE, BugType.BEETLE, 1)
BEETLE_W2 = Piece(Color.WHITE, BugType.BEETLE, 2)
BEETLE_B1 = Piece(Color.BLACK, BugType.BEETLE, 1)
ANT_W1 = Piece(Color.WHITE, BugType.SOLDIER_ANT, 1)


def test_placing_then_removing_a_piece_empties_the_cell() -> None:
    board = Board()
    board.place(ORIGIN, QUEEN_W)
    assert board.is_occupied(ORIGIN)
    assert board.top_piece(ORIGIN) == QUEEN_W

    removed = board.remove_top(ORIGIN)
    assert removed == QUEEN_W
    assert not board.is_occupied(ORIGIN)


def test_stacking_keeps_bottom_to_top_order() -> None:
    board = Board()
    board.place(ORIGIN, ANT_W1)
    board.place(ORIGIN, BEETLE_W1)
    assert board.stack_at(ORIGIN) == (ANT_W1, BEETLE_W1)
    assert board.top_piece(ORIGIN) == BEETLE_W1
    assert board.height(ORIGIN) == 2


def test_removing_top_exposes_the_piece_beneath() -> None:
    board = Board()
    board.place(ORIGIN, ANT_W1)
    board.place(ORIGIN, BEETLE_W1)
    board.remove_top(ORIGIN)
    assert board.top_piece(ORIGIN) == ANT_W1


def test_find_locates_a_placed_piece() -> None:
    board = Board()
    east = ORIGIN.neighbor(list(ORIGIN.neighbors())[0][0])
    board.place(east, QUEEN_W)
    assert board.find(QUEEN_W) == east


def test_find_returns_none_for_an_unplaced_piece() -> None:
    board = Board()
    assert board.find(QUEEN_W) is None


def test_stack_level_is_zero_indexed_from_the_bottom() -> None:
    board = Board()
    board.place(ORIGIN, ANT_W1)
    board.place(ORIGIN, BEETLE_W1)
    assert board.stack_level(ANT_W1) == 0
    assert board.stack_level(BEETLE_W1) == 1


# --- One Hive Rule: would_disconnect_hive ---------------------------------


def test_removing_the_only_link_between_two_groups_would_disconnect_the_hive() -> None:
    # O - A - B, a straight line of three occupied cells.
    board = Board()
    east_direction = ORIGIN.neighbors()[0][0]
    cell_a = ORIGIN.neighbor(east_direction)
    cell_b = cell_a.neighbor(east_direction)
    board.place(ORIGIN, QUEEN_W)
    board.place(cell_a, ANT_W1)
    board.place(cell_b, QUEEN_B)

    assert board.would_disconnect_hive(cell_a)
    assert not board.would_disconnect_hive(ORIGIN)
    assert not board.would_disconnect_hive(cell_b)


def test_removing_the_top_of_a_taller_stack_never_disconnects_the_hive() -> None:
    # Same line as above, but A is now a two-piece stack: lifting its top
    # leaves a piece behind to hold A's place, so the hive stays whole.
    board = Board()
    east_direction = ORIGIN.neighbors()[0][0]
    cell_a = ORIGIN.neighbor(east_direction)
    cell_b = cell_a.neighbor(east_direction)
    board.place(ORIGIN, QUEEN_W)
    board.place(cell_a, ANT_W1)
    board.place(cell_a, BEETLE_W1)
    board.place(cell_b, QUEEN_B)

    assert not board.would_disconnect_hive(cell_a)


def test_removing_an_isolated_single_piece_hive_does_not_disconnect_anything() -> None:
    board = Board()
    board.place(ORIGIN, QUEEN_W)
    assert not board.would_disconnect_hive(ORIGIN)


# --- Freedom to Move Rule: gate_blocks_slide -------------------------------


def test_ground_slide_is_blocked_when_both_flanking_cells_are_occupied() -> None:
    east_direction = ORIGIN.neighbors()[0][0]
    destination = ORIGIN.neighbor(east_direction)
    board = Board()
    for flank in _flanking_cells(ORIGIN, destination):
        board.place(flank, QUEEN_B)

    assert board.gate_blocks_slide(ORIGIN, destination)


def test_ground_slide_is_open_when_only_one_flanking_cell_is_occupied() -> None:
    east_direction = ORIGIN.neighbors()[0][0]
    destination = ORIGIN.neighbor(east_direction)
    board = Board()
    one_flank = _flanking_cells(ORIGIN, destination)[0]
    board.place(one_flank, QUEEN_B)

    assert not board.gate_blocks_slide(ORIGIN, destination)


def test_climbing_slide_is_open_when_only_one_flank_is_as_tall_as_the_climb() -> None:
    # Mover is descending from height 1 (after lifting) to height 0: a flank
    # needs height >= 2 to pinch that shut. One tall flank isn't enough.
    east_direction = ORIGIN.neighbors()[0][0]
    destination = ORIGIN.neighbor(east_direction)
    board = Board()
    board.place(ORIGIN, ANT_W1)  # the piece left behind once the mover lifts off
    tall_flank, short_flank = _flanking_cells(ORIGIN, destination)
    board.place(tall_flank, QUEEN_B)
    board.place(tall_flank, BEETLE_B1)  # height 2
    board.place(short_flank, QUEEN_W)  # height 1

    assert not board.gate_blocks_slide(ORIGIN, destination)


def test_climbing_slide_is_blocked_when_both_flanks_are_as_tall_as_the_climb() -> None:
    east_direction = ORIGIN.neighbors()[0][0]
    destination = ORIGIN.neighbor(east_direction)
    board = Board()
    board.place(ORIGIN, ANT_W1)
    flank_a, flank_b = _flanking_cells(ORIGIN, destination)
    for flank in (flank_a, flank_b):
        board.place(flank, QUEEN_B)
        board.place(flank, BEETLE_B1)  # height 2 on both sides

    assert board.gate_blocks_slide(ORIGIN, destination)


def _flanking_cells(
    origin: AxialCoordinate, destination: AxialCoordinate
) -> tuple[AxialCoordinate, AxialCoordinate]:
    from hive.coordinates import common_neighbors

    a, b = tuple(common_neighbors(origin, destination))
    return a, b
