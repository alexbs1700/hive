"""action_space.py: piece-slot x window-cell factoring of the policy head."""

import pytest

pytest.importorskip("numpy")

from hive.agents.alphazero import action_space  # noqa: E402
from hive.game import Game  # noqa: E402
from hive.moves import Pass  # noqa: E402
from hive.pieces import BugType, Color, Piece  # noqa: E402


def test_piece_slots_cover_all_fourteen_pieces_per_side() -> None:
    assert action_space.NUM_PIECE_SLOTS_PER_SIDE == 14
    assert action_space.NUM_PIECE_SLOTS == 28
    assert len(set(action_space.PIECE_SLOTS)) == 14


def test_slot_index_distinguishes_mine_from_the_opponents() -> None:
    queen = Piece(Color.WHITE, BugType.QUEEN_BEE)

    mine = action_space.slot_index_for_piece(queen, my_color=Color.WHITE)
    opponents = action_space.slot_index_for_piece(queen, my_color=Color.BLACK)

    assert mine < action_space.NUM_PIECE_SLOTS_PER_SIDE
    assert opponents >= action_space.NUM_PIECE_SLOTS_PER_SIDE
    assert opponents - mine == action_space.NUM_PIECE_SLOTS_PER_SIDE


def test_pass_has_no_spatial_action_index() -> None:
    game = Game()
    assert action_space.action_index_for_move(Pass(Color.WHITE), game) is None


def test_a_placements_action_index_matches_its_window_coordinates() -> None:
    game = Game()
    move = next(m for m in game.legal_moves() if m.piece.code == "wS1")

    slot, row, col = action_space.action_index_for_move(move, game)

    assert slot == action_space.slot_index_for_piece(move.piece, game.current_turn)
    from hive.agents.alphazero import encoding

    center = encoding.compute_window_center(game.state.board.occupied_cells())
    assert (row, col) == encoding.cell_to_window_coords(move.destination, center)


def test_every_legal_moves_action_index_is_recoverable() -> None:
    game = Game()
    game.apply_move(next(m for m in game.legal_moves() if m.piece.code == "wS1"))
    game.apply_move(next(m for m in game.legal_moves() if m.piece.code == "bA1"))

    action_map = action_space.legal_action_map(game)

    all_indexed_moves = [move for moves in action_map.values() for move in moves]
    assert sorted(all_indexed_moves, key=repr) == sorted(game.legal_moves(), key=repr)
    for index in action_map:
        if index is not None:
            slot, row, col = index
            assert 0 <= slot < action_space.NUM_PIECE_SLOTS
            assert 0 <= row < action_space.ACTION_SHAPE[1]
            assert 0 <= col < action_space.ACTION_SHAPE[2]
