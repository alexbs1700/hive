"""The Move kinds a Turn can consist of: Placement, Movement, Throw, or Pass.

Throw is kept distinct from Movement (see CONTEXT.md and ADR-0001's sibling
decision in the domain model) because it doesn't follow the acted-on piece's
own movement rule or the Freedom to Move Rule the way Movement does.
"""

from __future__ import annotations

from dataclasses import dataclass

from hive.coordinates import AxialCoordinate
from hive.pieces import Color, Piece


@dataclass(frozen=True, slots=True)
class Placement:
    """Introducing `piece` from Reserve onto the empty Cell `destination`."""

    piece: Piece
    destination: AxialCoordinate


@dataclass(frozen=True, slots=True)
class Movement:
    """Relocating `piece` from `origin` to `destination` under its own movement rule."""

    piece: Piece
    origin: AxialCoordinate
    destination: AxialCoordinate


@dataclass(frozen=True, slots=True)
class Throw:
    """A Pillbug's (or a Mosquito copying one's) Special Ability.

    `thrower` relocates `piece` (an adjacent Piece, friend or foe) from
    `origin` directly to `destination`, an empty Cell adjacent to `thrower`.
    """

    thrower: Piece
    piece: Piece
    origin: AxialCoordinate
    destination: AxialCoordinate


@dataclass(frozen=True, slots=True)
class Pass:
    """The Turn taken by `color` when no Placement, Movement, or Throw is available."""

    color: Color


Move = Placement | Movement | Throw | Pass
