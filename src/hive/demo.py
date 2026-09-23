"""A random-move self-play demo: an engine smoke test, not a rules concept.

Runs many games of two random legal-move Players against each other and
reports summary stats. Its own `max_moves_per_game` safety cap is entirely
separate from the (uncapped) core Game/rules engine — see
docs/adr/0001-separate-inconclusive-outcome-from-draw.md. A game that hits
the cap is reported Inconclusive, never as a Draw.
"""

from __future__ import annotations

import argparse
import random
import statistics
from dataclasses import dataclass
from enum import Enum

from hive.game import Game, Outcome

DEFAULT_MAX_MOVES_PER_GAME = 400


class DemoOutcome(Enum):
    WIN = "win"
    DRAW = "draw"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True, slots=True)
class DemoResult:
    outcome: DemoOutcome
    winner_name: str | None
    move_count: int


@dataclass(frozen=True, slots=True)
class DemoSummary:
    games_played: int
    outcome_counts: dict[DemoOutcome, int]
    win_counts_by_color: dict[str, int]
    average_move_count: float


def play_random_game(max_moves_per_game: int, rng: random.Random) -> DemoResult:
    game = Game()
    moves_played = 0
    while not game.is_over() and moves_played < max_moves_per_game:
        move = rng.choice(game.legal_moves())
        game.apply_move(move)
        moves_played += 1

    result = game.result()
    if result.outcome is Outcome.WIN:
        assert result.winner is not None
        return DemoResult(DemoOutcome.WIN, result.winner.name, moves_played)
    if result.outcome is Outcome.DRAW:
        return DemoResult(DemoOutcome.DRAW, None, moves_played)
    return DemoResult(DemoOutcome.INCONCLUSIVE, None, moves_played)


def run_demo(
    num_games: int, max_moves_per_game: int = DEFAULT_MAX_MOVES_PER_GAME, seed: int | None = None
) -> DemoSummary:
    rng = random.Random(seed)
    outcome_counts: dict[DemoOutcome, int] = dict.fromkeys(DemoOutcome, 0)
    win_counts_by_color: dict[str, int] = {}
    move_counts: list[int] = []

    for _ in range(num_games):
        result = play_random_game(max_moves_per_game, rng)
        outcome_counts[result.outcome] += 1
        if result.outcome is DemoOutcome.WIN:
            assert result.winner_name is not None
            win_counts_by_color[result.winner_name] = (
                win_counts_by_color.get(result.winner_name, 0) + 1
            )
        move_counts.append(result.move_count)

    return DemoSummary(
        games_played=num_games,
        outcome_counts=outcome_counts,
        win_counts_by_color=win_counts_by_color,
        average_move_count=statistics.fmean(move_counts) if move_counts else 0.0,
    )


def _print_summary(summary: DemoSummary) -> None:
    print(f"Played {summary.games_played} random-move self-play games.")
    for outcome in DemoOutcome:
        print(f"  {outcome.value}: {summary.outcome_counts[outcome]}")
    for color_name, count in sorted(summary.win_counts_by_color.items()):
        print(f"    {color_name} wins: {count}")
    print(f"  average moves per game: {summary.average_move_count:.1f}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run random-move self-play Hive games as an engine smoke test."
    )
    parser.add_argument("--games", type=int, default=100, help="number of games to play")
    parser.add_argument(
        "--max-moves",
        type=int,
        default=DEFAULT_MAX_MOVES_PER_GAME,
        help="per-game safety cap; a game hitting it is reported Inconclusive",
    )
    parser.add_argument("--seed", type=int, default=None, help="random seed, for reproducibility")
    args = parser.parse_args()

    summary = run_demo(args.games, args.max_moves, args.seed)
    _print_summary(summary)


if __name__ == "__main__":
    main()
