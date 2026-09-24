"""Agent: the interface every move-choosing implementation satisfies.

`Game` in, `Move` out — nothing about *how* the decision gets made (tensor
inference, a text prompt to an LLM, a plain random draw) is visible outside
the agent's own package. This is what lets `arena.py` play any two
implementations against each other without knowing which is which. See
docs/agent-roadmap.md for the full design rationale.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from hive.game import Game
from hive.moves import Move


@runtime_checkable
class Agent(Protocol):
    """Chooses a Move from `game.legal_moves()` for whichever Color is on turn."""

    def choose_move(self, game: Game) -> Move: ...
