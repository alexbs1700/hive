"""config.py: AlphaZero hyperparameters as a plain dataclass — no config framework yet.

Revisit only once sweeping these genuinely needs more than "construct a
NetworkConfig with different numbers" (see docs/agent-roadmap.md's
"deliberately not adding yet" list).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NetworkConfig:
    """Shape of the policy+value network. Kept deliberately small to start (see Phase 6's plan)."""

    residual_channels: int = 64
    num_residual_blocks: int = 4
    value_head_hidden_units: int = 64
