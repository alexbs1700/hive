"""Axial hex-grid coordinates: the addressing scheme for every Cell on the Board.

The Board is unbounded, so coordinates are plain integers with no range limit.
Orientation is "pointy-top": each Cell has exactly six neighbors, reached by
the six `Direction` values below.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Direction(Enum):
    """One of the six directions from a Cell to a neighboring Cell.

    Names and the (delta_q, delta_r) offsets follow the pointy-top axial
    convention. These also double as the six directions encoded by a Move
    Notation Direction Marker (see notation.py).
    """

    EAST = "E"
    NORTHEAST = "NE"
    NORTHWEST = "NW"
    WEST = "W"
    SOUTHWEST = "SW"
    SOUTHEAST = "SE"

    @property
    def offset(self) -> tuple[int, int]:
        return _DIRECTION_OFFSETS[self]

    @property
    def opposite(self) -> Direction:
        return _OPPOSITE_DIRECTIONS[self]


_DIRECTION_OFFSETS: dict[Direction, tuple[int, int]] = {
    Direction.EAST: (1, 0),
    Direction.NORTHEAST: (1, -1),
    Direction.NORTHWEST: (0, -1),
    Direction.WEST: (-1, 0),
    Direction.SOUTHWEST: (-1, 1),
    Direction.SOUTHEAST: (0, 1),
}

_OPPOSITE_DIRECTIONS: dict[Direction, Direction] = {
    Direction.EAST: Direction.WEST,
    Direction.WEST: Direction.EAST,
    Direction.NORTHEAST: Direction.SOUTHWEST,
    Direction.SOUTHWEST: Direction.NORTHEAST,
    Direction.NORTHWEST: Direction.SOUTHEAST,
    Direction.SOUTHEAST: Direction.NORTHWEST,
}

ALL_DIRECTIONS: tuple[Direction, ...] = tuple(Direction)


@dataclass(frozen=True, slots=True)
class AxialCoordinate:
    """A single Cell's position on the unbounded hex Board, as axial (q, r) coordinates."""

    q: int
    r: int

    def neighbor(self, direction: Direction) -> AxialCoordinate:
        """The Cell one step away from this one, in the given Direction."""
        delta_q, delta_r = direction.offset
        return AxialCoordinate(self.q + delta_q, self.r + delta_r)

    def neighbors(self) -> tuple[tuple[Direction, AxialCoordinate], ...]:
        """All six neighboring Cells, paired with the Direction that reaches each one."""
        return tuple((direction, self.neighbor(direction)) for direction in ALL_DIRECTIONS)

    def neighbor_set(self) -> frozenset[AxialCoordinate]:
        """The six neighboring Cells, without their Directions."""
        return frozenset(cell for _, cell in self.neighbors())

    def is_adjacent_to(self, other: AxialCoordinate) -> bool:
        return other in self.neighbor_set()

    def direction_to(self, other: AxialCoordinate) -> Direction | None:
        """The Direction from this Cell to `other`, or None if they aren't adjacent."""
        for direction, neighbor in self.neighbors():
            if neighbor == other:
                return direction
        return None


def common_neighbors(a: AxialCoordinate, b: AxialCoordinate) -> frozenset[AxialCoordinate]:
    """The Cells adjacent to both `a` and `b`.

    For two adjacent Cells on a hex grid there are always exactly two such
    Cells: the pair that flanks the shared edge, used by the Freedom to Move
    Rule's narrow-gate check.
    """
    return a.neighbor_set() & b.neighbor_set()
