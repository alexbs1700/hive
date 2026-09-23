"""Pillbug: moves like the Queen Bee, or Throws an adjacent Piece instead."""

from conftest import B, W, board_with, piece

from hive.coordinates import AxialCoordinate as Cell
from hive.pieces import BugType
from hive.rules import legal_throws, movement_destinations


def test_pillbug_own_movement_is_a_single_ground_slide() -> None:
    pillbug = piece(W, BugType.PILLBUG)
    other = piece(B, BugType.QUEEN_BEE)
    board = board_with((pillbug, Cell(0, 0)), (other, Cell(1, 0)))

    assert movement_destinations(board, pillbug, None) == {Cell(1, -1), Cell(0, 1)}


def test_pillbug_can_throw_any_adjacent_piece_to_an_empty_neighbor() -> None:
    pillbug = piece(W, BugType.PILLBUG)
    target = piece(B, BugType.SOLDIER_ANT, 1)
    anchor = piece(B, BugType.QUEEN_BEE)
    board = board_with((pillbug, Cell(0, 0)), (target, Cell(1, 0)), (anchor, Cell(1, -1)))

    throws = legal_throws(board, pillbug, None)
    thrown_pieces = {throw.piece for throw in throws}
    assert thrown_pieces == {target, anchor}
    empty_pillbug_neighbors = {Cell(0, -1), Cell(-1, 0), Cell(-1, 1), Cell(0, 1)}
    assert {throw.destination for throw in throws} == empty_pillbug_neighbors


def test_pillbug_cannot_throw_the_last_moved_piece() -> None:
    pillbug = piece(W, BugType.PILLBUG)
    target = piece(B, BugType.SOLDIER_ANT, 1)
    anchor = piece(B, BugType.QUEEN_BEE)
    board = board_with((pillbug, Cell(0, 0)), (target, Cell(1, 0)), (anchor, Cell(1, -1)))

    throws = legal_throws(board, pillbug, last_moved_piece=target)
    assert all(throw.piece != target for throw in throws)
    assert any(throw.piece == anchor for throw in throws)


def test_pillbug_cannot_throw_a_piece_that_would_disconnect_the_hive() -> None:
    # Pillbug - Middle - Far, in a line. Throwing Middle would strand Far.
    pillbug = piece(W, BugType.PILLBUG)
    middle = piece(B, BugType.SOLDIER_ANT, 1)
    far = piece(B, BugType.QUEEN_BEE)
    board = board_with((pillbug, Cell(0, 0)), (middle, Cell(1, 0)), (far, Cell(2, 0)))

    assert legal_throws(board, pillbug, None) == set()


def test_pillbug_cannot_throw_a_piece_that_is_part_of_a_stack() -> None:
    pillbug = piece(W, BugType.PILLBUG)
    stack_bottom = piece(B, BugType.SOLDIER_ANT, 1)
    stack_top = piece(B, BugType.BEETLE, 1)
    anchor = piece(B, BugType.QUEEN_BEE)
    board = board_with(
        (pillbug, Cell(0, 0)),
        (stack_bottom, Cell(1, 0)),
        (stack_top, Cell(1, 0)),
        (anchor, Cell(1, -1)),
    )

    throws = legal_throws(board, pillbug, None)
    assert all(throw.piece != stack_top for throw in throws)
    assert all(throw.piece != stack_bottom for throw in throws)
    assert any(throw.piece == anchor for throw in throws)


def test_mosquito_touching_a_pillbug_can_copy_its_throw() -> None:
    pillbug = piece(B, BugType.PILLBUG)
    target = piece(B, BugType.SOLDIER_ANT, 1)
    mosquito = piece(W, BugType.MOSQUITO)
    board = board_with((pillbug, Cell(0, 0)), (target, Cell(1, 0)), (mosquito, Cell(1, -1)))

    throws = legal_throws(board, mosquito, None)
    assert {throw.piece for throw in throws} == {target, pillbug}
    assert all(throw.thrower == mosquito for throw in throws)


def test_mosquito_not_touching_a_pillbug_cannot_throw() -> None:
    non_pillbug = piece(B, BugType.QUEEN_BEE)
    mosquito = piece(W, BugType.MOSQUITO)
    board = board_with((non_pillbug, Cell(0, 0)), (mosquito, Cell(1, 0)))

    assert legal_throws(board, mosquito, None) == set()
