"""network.py: forward-pass shapes and evaluate_position's legal-move masking."""

import pytest

pytest.importorskip("torch")

import torch  # noqa: E402

from hive.agents.alphazero import action_space, encoding  # noqa: E402
from hive.agents.alphazero.config import NetworkConfig  # noqa: E402
from hive.agents.alphazero.network import HiveNet, evaluate_position  # noqa: E402
from hive.coordinates import AxialCoordinate as Cell  # noqa: E402
from hive.game import Game  # noqa: E402
from hive.moves import Pass  # noqa: E402
from hive.pieces import BugType, Color, Piece  # noqa: E402
from hive.state import GameState  # noqa: E402

# A tiny config keeps these tests fast — correctness doesn't depend on network size.
_TINY_CONFIG = NetworkConfig(residual_channels=8, num_residual_blocks=1, value_head_hidden_units=8)


def _tiny_net() -> HiveNet:
    torch.manual_seed(0)
    return HiveNet(_TINY_CONFIG)


def test_forward_pass_produces_the_documented_shapes() -> None:
    net = _tiny_net()
    tensor = torch.from_numpy(encoding.encode(Game())).unsqueeze(0)

    policy_logits, value = net(tensor)

    assert policy_logits.shape == (1, *action_space.ACTION_SHAPE)
    assert value.shape == (1,)
    assert -1.0 <= value.item() <= 1.0


def test_evaluate_position_returns_a_probability_for_every_legal_move() -> None:
    net = _tiny_net()
    game = Game()

    move_probabilities, value = evaluate_position(net, game)

    assert set(move_probabilities) == set(game.legal_moves())
    assert -1.0 <= value <= 1.0


def test_evaluate_position_probabilities_sum_to_one() -> None:
    net = _tiny_net()
    game = Game()
    game.apply_move(next(m for m in game.legal_moves() if m.piece.code == "wS1"))

    move_probabilities, _ = evaluate_position(net, game)

    assert sum(move_probabilities.values()) == pytest.approx(1.0, abs=1e-5)


def test_evaluate_position_handles_a_forced_pass() -> None:
    net = _tiny_net()
    game = Game()
    game.state = GameState()
    queen = Piece(Color.WHITE, BugType.QUEEN_BEE)
    game.state.board.place(Cell(0, 0), queen)
    game.state.reserves[Color.WHITE] = []
    game.state.last_moved_piece = queen

    move_probabilities, _ = evaluate_position(net, game)

    assert move_probabilities == {Pass(Color.WHITE): 1.0}


def test_network_is_deterministic_in_eval_mode() -> None:
    net = _tiny_net()
    tensor = torch.from_numpy(encoding.encode(Game())).unsqueeze(0)
    net.eval()

    with torch.no_grad():
        first_policy, first_value = net(tensor)
        second_policy, second_value = net(tensor)

    assert torch.equal(first_policy, second_policy)
    assert torch.equal(first_value, second_value)
