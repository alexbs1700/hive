"""RandomAgent: always returns one of the Game's own legal moves."""

import random

from hive.agents.random_agent import RandomAgent
from hive.game import Game


def test_chooses_a_move_from_the_games_own_legal_moves() -> None:
    game = Game()
    agent = RandomAgent(random.Random(0))

    move = agent.choose_move(game)

    assert move in game.legal_moves()


def test_is_deterministic_given_the_same_seeded_rng() -> None:
    game = Game()

    first = RandomAgent(random.Random(42)).choose_move(game)
    second = RandomAgent(random.Random(42)).choose_move(game)

    assert first == second
