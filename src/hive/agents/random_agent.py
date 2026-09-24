"""RandomAgent: picks uniformly among the legal moves.

The baseline every other Agent is measured against.
"""

from __future__ import annotations

import random

from hive.game import Game
from hive.moves import Move


class RandomAgent:
    """An Agent that satisfies protocol.Agent by choosing uniformly at random."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng if rng is not None else random.Random()

    def choose_move(self, game: Game) -> Move:
        return self._rng.choice(game.legal_moves())
