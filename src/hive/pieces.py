"""Piece identity: Color, Bug Type, and Piece, per CONTEXT.md."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Color(Enum):
    """A Player's side. Value is the letter used in every Piece Code."""

    WHITE = "w"
    BLACK = "b"

    @property
    def opponent(self) -> Color:
        return Color.BLACK if self is Color.WHITE else Color.WHITE


class BugType(Enum):
    """A Piece's species. Value is the letter used in every Piece Code."""

    QUEEN_BEE = "Q"
    BEETLE = "B"
    GRASSHOPPER = "G"
    SPIDER = "S"
    SOLDIER_ANT = "A"
    MOSQUITO = "M"
    LADYBUG = "L"
    PILLBUG = "P"


# How many of each Bug Type a Player's Reserve starts with. Totals 14 per color.
STARTING_COUNTS: dict[BugType, int] = {
    BugType.QUEEN_BEE: 1,
    BugType.BEETLE: 2,
    BugType.GRASSHOPPER: 3,
    BugType.SPIDER: 2,
    BugType.SOLDIER_ANT: 3,
    BugType.MOSQUITO: 1,
    BugType.LADYBUG: 1,
    BugType.PILLBUG: 1,
}

# Bug Types a player only ever has one of don't get a disambiguating number in their Piece Code.
_UNNUMBERED_BUG_TYPES = frozenset(
    bug_type for bug_type, count in STARTING_COUNTS.items() if count == 1
)


@dataclass(frozen=True, slots=True)
class Piece:
    """A single game Piece: one Bug Type belonging to one Player, with a Piece Code.

    `number` disambiguates Pieces of the same Color and Bug Type when a
    Player has more than one (e.g. wA1, wA2, wA3); it's assigned in the
    order each Piece of that type is placed, and is None for the four Bug
    Types a player only ever has one of.
    """

    color: Color
    bug_type: BugType
    number: int | None = None

    def __post_init__(self) -> None:
        is_unnumbered = self.bug_type in _UNNUMBERED_BUG_TYPES
        if is_unnumbered and self.number is not None:
            raise ValueError(f"{self.bug_type.name} does not take a disambiguating number")
        if not is_unnumbered and self.number is None:
            raise ValueError(f"{self.bug_type.name} requires a disambiguating number")

    @property
    def code(self) -> str:
        """This Piece's Piece Code, e.g. 'wA1' or 'bQ'."""
        suffix = "" if self.number is None else str(self.number)
        return f"{self.color.value}{self.bug_type.value}{suffix}"

    def __str__(self) -> str:
        return self.code


def reserve_pieces(color: Color) -> list[Piece]:
    """All 14 Pieces a Player of the given Color starts the game with, in their Reserve."""
    pieces: list[Piece] = []
    for bug_type, count in STARTING_COUNTS.items():
        if bug_type in _UNNUMBERED_BUG_TYPES:
            pieces.append(Piece(color, bug_type))
        else:
            pieces.extend(Piece(color, bug_type, number) for number in range(1, count + 1))
    return pieces
