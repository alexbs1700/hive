"""Agent: any object with a matching choose_move satisfies the protocol structurally."""

import random

from hive.agents.protocol import Agent
from hive.agents.random_agent import RandomAgent
from hive.game import Game
from hive.moves import Move


class _StubAgent:
    """Deliberately doesn't inherit from Agent — only structurally matches it."""

    def choose_move(self, game: Game) -> Move:
        return game.legal_moves()[0]


def test_random_agent_satisfies_the_protocol() -> None:
    assert isinstance(RandomAgent(random.Random(0)), Agent)


def test_a_structurally_matching_stub_satisfies_the_protocol_too() -> None:
    assert isinstance(_StubAgent(), Agent)


def test_an_object_without_choose_move_does_not_satisfy_the_protocol() -> None:
    assert not isinstance(object(), Agent)
