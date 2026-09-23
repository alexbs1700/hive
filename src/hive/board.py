"""The Board: an unbounded hex grid of Cells, each optionally holding a Stack of Pieces."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable

from hive.coordinates import AxialCoordinate, Direction, common_neighbors
from hive.pieces import Piece


class Board:
    """Sparse hex Board: only occupied Cells are stored, each as a bottom-to-top Stack.

    Mutating methods (`place`, `remove_top`) mutate this Board in place, to
    support the make-move/undo-move state model described in CONTEXT.md.
    """

    def __init__(self) -> None:
        self._stacks: dict[AxialCoordinate, list[Piece]] = {}

    def stack_at(self, cell: AxialCoordinate) -> tuple[Piece, ...]:
        """The Pieces at `cell`, bottom to top. Empty if the Cell is unoccupied."""
        return tuple(self._stacks.get(cell, ()))

    def height(self, cell: AxialCoordinate) -> int:
        return len(self._stacks.get(cell, ()))

    def is_occupied(self, cell: AxialCoordinate) -> bool:
        return cell in self._stacks

    def top_piece(self, cell: AxialCoordinate) -> Piece | None:
        """The Piece currently in play at `cell` — the top of its Stack — or None."""
        stack = self._stacks.get(cell)
        return stack[-1] if stack else None

    def occupied_cells(self) -> frozenset[AxialCoordinate]:
        return frozenset(self._stacks.keys())

    def is_empty(self) -> bool:
        return not self._stacks

    def place(self, cell: AxialCoordinate, piece: Piece) -> None:
        """Push `piece` onto the top of the Stack at `cell` (creating it if empty)."""
        self._stacks.setdefault(cell, []).append(piece)

    def remove_top(self, cell: AxialCoordinate) -> Piece:
        """Pop and return the top Piece at `cell`. Raises if `cell` is unoccupied."""
        stack = self._stacks.get(cell)
        if not stack:
            raise ValueError(f"cannot remove from empty cell {cell}")
        piece = stack.pop()
        if not stack:
            del self._stacks[cell]
        return piece

    def find(self, piece: Piece) -> AxialCoordinate | None:
        """The Cell currently holding `piece`, wherever it sits in that Cell's Stack."""
        for cell, stack in self._stacks.items():
            if piece in stack:
                return cell
        return None

    def stack_level(self, piece: Piece) -> int | None:
        """`piece`'s 0-indexed position (bottom = 0) in its Stack, or None if not on the Board."""
        cell = self.find(piece)
        if cell is None:
            return None
        return self._stacks[cell].index(piece)

    def occupied_neighbors(self, cell: AxialCoordinate) -> tuple[AxialCoordinate, ...]:
        return tuple(neighbor for _, neighbor in cell.neighbors() if self.is_occupied(neighbor))

    def neighboring_top_pieces(self, cell: AxialCoordinate) -> tuple[Piece, ...]:
        """The in-play (topmost) Pieces at every occupied Cell touching `cell`."""
        return tuple(
            piece
            for neighbor in self.occupied_neighbors(cell)
            if (piece := self.top_piece(neighbor)) is not None
        )

    def is_connected(self, cells: Iterable[AxialCoordinate] | None = None) -> bool:
        """Whether `cells` (default: all occupied Cells) form a single connected group.

        An empty set of Cells counts as connected (there's nothing to split).
        """
        remaining = set(self._stacks.keys()) if cells is None else set(cells)
        if not remaining:
            return True
        start = next(iter(remaining))
        seen = {start}
        queue = deque([start])
        while queue:
            current = queue.popleft()
            for neighbor in current.neighbor_set():
                if neighbor in remaining and neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)
        return seen == remaining

    def would_disconnect_hive(self, cell: AxialCoordinate) -> bool:
        """Whether lifting the top Piece off `cell` would break the One Hive Rule.

        Only ever true for a Cell with exactly one Piece: lifting the top of a
        taller Stack always leaves a Piece behind to hold that Cell's place.
        """
        if self.height(cell) != 1:
            return False
        remaining_cells = self.occupied_cells() - {cell}
        return not self.is_connected(remaining_cells)

    def gate_blocks_slide(self, origin: AxialCoordinate, destination: AxialCoordinate) -> bool:
        """Whether the Freedom to Move Rule's narrow gate blocks a slide from origin to destination.

        `origin` is treated as already vacated (its mover is "in transit") and
        `destination` as not yet arrived at, so pass in a Board state where the
        mover has already been lifted off `origin`.

        A slide is blocked when both Cells flanking the origin-destination
        edge are tall enough to pinch it shut: formally, when both flanking
        heights are at least one more than the taller of the mover's
        before/after Stack heights. This single formula covers ground-level
        sliding and Beetle-style climbing alike (see docs/adr for the base
        game's worked examples in the rulebook).
        """
        origin_height = self.height(origin)
        destination_height = self.height(destination)
        required_clearance = max(origin_height, destination_height) + 1
        flank_a, flank_b = _common_neighbors(origin, destination)
        flanks_are_tall_enough_to_pinch_shut = (
            self.height(flank_a) >= required_clearance
            and self.height(flank_b) >= required_clearance
        )
        return flanks_are_tall_enough_to_pinch_shut

    def copy(self) -> Board:
        clone = Board()
        clone._stacks = {cell: list(stack) for cell, stack in self._stacks.items()}
        return clone


def _common_neighbors(
    a: AxialCoordinate, b: AxialCoordinate
) -> tuple[AxialCoordinate, AxialCoordinate]:
    neighbors = tuple(common_neighbors(a, b))
    if len(neighbors) != 2:
        raise ValueError(f"{a} and {b} are not adjacent Cells")
    return neighbors  # type: ignore[return-value]


__all__ = ["Board", "AxialCoordinate", "Direction"]
