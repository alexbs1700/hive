"""Piece Code formatting and Reserve composition."""

import pytest

from hive.pieces import STARTING_COUNTS, BugType, Color, Piece, reserve_pieces


def test_numbered_piece_code_includes_the_disambiguating_number() -> None:
    piece = Piece(Color.WHITE, BugType.SOLDIER_ANT, 1)
    assert piece.code == "wA1"


def test_unnumbered_piece_code_has_no_trailing_number() -> None:
    piece = Piece(Color.BLACK, BugType.QUEEN_BEE)
    assert piece.code == "bQ"


def test_singleton_bug_type_rejects_a_number() -> None:
    with pytest.raises(ValueError, match="does not take"):
        Piece(Color.WHITE, BugType.QUEEN_BEE, 1)


def test_multiple_bug_type_requires_a_number() -> None:
    with pytest.raises(ValueError, match="requires"):
        Piece(Color.WHITE, BugType.SOLDIER_ANT)


def test_reserve_has_fourteen_pieces_per_color() -> None:
    assert len(reserve_pieces(Color.WHITE)) == 14
    assert len(reserve_pieces(Color.BLACK)) == 14


def test_reserve_matches_starting_counts_per_bug_type() -> None:
    pieces = reserve_pieces(Color.WHITE)
    for bug_type, expected_count in STARTING_COUNTS.items():
        actual_count = sum(1 for piece in pieces if piece.bug_type is bug_type)
        assert actual_count == expected_count


def test_reserve_numbers_are_unique_per_bug_type() -> None:
    pieces = reserve_pieces(Color.BLACK)
    ants = [piece.number for piece in pieces if piece.bug_type is BugType.SOLDIER_ANT]
    assert sorted(ants) == [1, 2, 3]
