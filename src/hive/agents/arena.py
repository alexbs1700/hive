"""Arena: plays any two Agents against each other and reports the result.

The one evaluation harness every agent implementation shares (see
docs/agent-roadmap.md) — it only relies on `Agent.choose_move`, never on how
either side actually decides. `Outcome`/`Draw` follow Game's own rulebook
meaning; `Inconclusive` is this module's own move-cap cutoff, the same
distinction ADR-0001 establishes for hive.demo, and is never conflated with
a real Draw for the same reason: a cutoff carries no game-theoretic signal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from hive.agents.protocol import Agent
from hive.demo import DEFAULT_MAX_MOVES_PER_GAME
from hive.game import Game, Outcome
from hive.pieces import Color


class MatchOutcome(Enum):
    WIN = "win"
    DRAW = "draw"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True, slots=True)
class GameRecord:
    outcome: MatchOutcome
    winner: Color | None  # only set when outcome is WIN
    move_count: int


def play_game(
    white: Agent, black: Agent, max_moves: int = DEFAULT_MAX_MOVES_PER_GAME
) -> GameRecord:
    """Plays one game: `white` acts for Color.WHITE, `black` for Color.BLACK."""
    game = Game()
    agents = {Color.WHITE: white, Color.BLACK: black}
    moves_played = 0
    while not game.is_over() and moves_played < max_moves:
        agent = agents[game.current_turn]
        move = agent.choose_move(game)
        if move not in game.legal_moves():
            raise ValueError(f"{agent!r} chose an illegal move for {game.current_turn}: {move!r}")
        game.apply_move(move)
        moves_played += 1

    result = game.result()
    if result.outcome is Outcome.WIN:
        return GameRecord(MatchOutcome.WIN, result.winner, moves_played)
    if result.outcome is Outcome.DRAW:
        return GameRecord(MatchOutcome.DRAW, None, moves_played)
    return GameRecord(MatchOutcome.INCONCLUSIVE, None, moves_played)


@dataclass(frozen=True, slots=True)
class MatchSummary:
    games_played: int
    wins: dict[str, int]  # keyed by caller-supplied label, not Color — an Agent plays both sides
    draws: int = 0
    inconclusive: int = 0
    records: list[GameRecord] = field(default_factory=list)


def play_match(
    agent_a: Agent,
    agent_b: Agent,
    num_games: int,
    *,
    label_a: str = "a",
    label_b: str = "b",
    max_moves_per_game: int = DEFAULT_MAX_MOVES_PER_GAME,
) -> MatchSummary:
    """Plays `num_games`, alternating who's White so neither label is favored by going first."""
    wins = {label_a: 0, label_b: 0}
    draws = 0
    inconclusive = 0
    records: list[GameRecord] = []

    for game_index in range(num_games):
        agent_a_is_white = game_index % 2 == 0
        white, black = (agent_a, agent_b) if agent_a_is_white else (agent_b, agent_a)
        white_label, black_label = (label_a, label_b) if agent_a_is_white else (label_b, label_a)

        record = play_game(white, black, max_moves=max_moves_per_game)
        records.append(record)
        if record.outcome is MatchOutcome.WIN:
            winner_label = white_label if record.winner is Color.WHITE else black_label
            wins[winner_label] += 1
        elif record.outcome is MatchOutcome.DRAW:
            draws += 1
        else:
            inconclusive += 1

    return MatchSummary(
        games_played=num_games, wins=wins, draws=draws, inconclusive=inconclusive, records=records
    )
