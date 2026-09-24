"""Arena: plays any two Agents against each other without caring how either decides."""

import random

import pytest

from hive.agents.arena import MatchOutcome, play_game, play_match
from hive.agents.random_agent import RandomAgent
from hive.game import Game
from hive.moves import Move, Pass
from hive.pieces import Color


def test_play_game_between_two_random_agents_completes() -> None:
    record = play_game(RandomAgent(random.Random(1)), RandomAgent(random.Random(2)), max_moves=50)

    assert isinstance(record.outcome, MatchOutcome)
    assert 0 < record.move_count <= 50
    if record.outcome is MatchOutcome.WIN:
        assert record.winner in (Color.WHITE, Color.BLACK)
    else:
        assert record.winner is None


def test_play_game_rejects_an_agent_that_chooses_an_illegal_move() -> None:
    class _CheatingAgent:
        def choose_move(self, game: Game) -> Move:
            return Pass(game.current_turn.opponent)  # never a legal move for the mover's own turn

    with pytest.raises(ValueError, match="illegal move"):
        play_game(_CheatingAgent(), RandomAgent(random.Random(0)))


def test_play_match_tallies_every_game_into_exactly_one_bucket() -> None:
    summary = play_match(
        RandomAgent(random.Random(1)),
        RandomAgent(random.Random(2)),
        num_games=6,
        label_a="alpha",
        label_b="beta",
        max_moves_per_game=30,
    )

    assert summary.games_played == 6
    assert len(summary.records) == 6
    assert sum(summary.wins.values()) + summary.draws + summary.inconclusive == 6
    assert set(summary.wins) == {"alpha", "beta"}


def test_play_match_alternates_which_label_plays_white() -> None:
    colors_seen: list[Color] = []

    class _SpyAgent:
        def __init__(self, rng: random.Random) -> None:
            self._inner = RandomAgent(rng)

        def choose_move(self, game: Game) -> Move:
            colors_seen.append(game.current_turn)
            return self._inner.choose_move(game)

    play_match(
        _SpyAgent(random.Random(1)),
        RandomAgent(random.Random(2)),
        num_games=4,
        max_moves_per_game=20,
    )

    # One color per game for the spy (agent_a): collapse consecutive repeats within a game.
    per_game_colors = [c for i, c in enumerate(colors_seen) if i == 0 or c != colors_seen[i - 1]]
    assert per_game_colors == [Color.WHITE, Color.BLACK, Color.WHITE, Color.BLACK]
