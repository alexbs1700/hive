"""Queen Bee: a single ground slide per Turn, gated and contact-checked like every slider."""

from conftest import B, W, board_with, piece

from hive.coordinates import AxialCoordinate as Cell
from hive.pieces import BugType
from hive.rules import movement_destinations


def test_queen_slides_only_to_cells_that_stay_in_contact_with_the_hive() -> None:
    # A lone neighbor gives the Queen exactly two places to slide to: the
    # cells that stay touching that neighbor. Cells that would lose contact
    # with the Hive entirely are excluded even though they're empty.
    queen = piece(W, BugType.QUEEN_BEE)
    other = piece(B, BugType.QUEEN_BEE)
    board = board_with((queen, Cell(0, 0)), (other, Cell(1, 0)))

    assert movement_destinations(board, queen, None) == {Cell(1, -1), Cell(0, 1)}


def test_queen_cannot_slide_onto_an_occupied_cell() -> None:
    queen = piece(W, BugType.QUEEN_BEE)
    other = piece(B, BugType.QUEEN_BEE)
    board = board_with((queen, Cell(0, 0)), (other, Cell(1, 0)))

    assert Cell(1, 0) not in movement_destinations(board, queen, None)
