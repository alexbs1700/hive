"""Per-Bug-Type Movement patterns, Throw generation, and Placement adjacency.

Every function here is a pure query over a `Board` (plus a little context):
nothing here mutates state. `hive.game` is what actually applies a chosen
Move.

Movement pattern functions internally lift the mover off the Board (so the
Freedom to Move Rule's height formula and hive-contact checks see the
"in transit" position correctly), compute destinations, and restore it
before returning.
"""

from __future__ import annotations

from hive.board import Board
from hive.coordinates import AxialCoordinate, common_neighbors
from hive.moves import Throw
from hive.pieces import BugType, Color, Piece


def _step_targets(
    board: Board, origin: AxialCoordinate, *, allow_climbing: bool
) -> set[AxialCoordinate]:
    """Cells reachable from `origin` by one legal slide.

    `board` must already have the mover lifted off `origin`. When
    `allow_climbing` is False (every Bug Type except the Beetle, and a
    Mosquito copying one), a destination must be empty. When True, a
    destination may also be an occupied Cell, which is a climb.
    """
    targets: set[AxialCoordinate] = set()
    for _, neighbor in origin.neighbors():
        neighbor_is_occupied = board.is_occupied(neighbor)
        if neighbor_is_occupied and not allow_climbing:
            continue
        if board.gate_blocks_slide(origin, neighbor):
            continue
        if not neighbor_is_occupied and not board.occupied_neighbors(neighbor):
            continue
        targets.add(neighbor)
    return targets


class _Lifted:
    """Temporarily removes `piece` from `origin` on a Board, restoring it on exit."""

    def __init__(self, board: Board, piece: Piece, origin: AxialCoordinate) -> None:
        self._board = board
        self._piece = piece
        self._origin = origin

    def __enter__(self) -> None:
        removed = self._board.remove_top(self._origin)
        assert removed == self._piece

    def __exit__(self, *exc_info: object) -> None:
        self._board.place(self._origin, self._piece)


def _queen_bee_destinations(
    board: Board, origin: AxialCoordinate, piece: Piece
) -> frozenset[AxialCoordinate]:
    with _Lifted(board, piece, origin):
        return frozenset(_step_targets(board, origin, allow_climbing=False))


def _pillbug_own_destinations(
    board: Board, origin: AxialCoordinate, piece: Piece
) -> frozenset[AxialCoordinate]:
    return _queen_bee_destinations(board, origin, piece)


def _beetle_destinations(
    board: Board, origin: AxialCoordinate, piece: Piece
) -> frozenset[AxialCoordinate]:
    with _Lifted(board, piece, origin):
        return frozenset(_step_targets(board, origin, allow_climbing=True))


def _grasshopper_destinations(
    board: Board, origin: AxialCoordinate, piece: Piece
) -> frozenset[AxialCoordinate]:
    del piece  # the Grasshopper's jump needs no gate/lift handling
    destinations: set[AxialCoordinate] = set()
    for direction, first_neighbor in origin.neighbors():
        if not board.is_occupied(first_neighbor):
            continue
        cursor = first_neighbor
        while board.is_occupied(cursor):
            cursor = cursor.neighbor(direction)
        destinations.add(cursor)
    return frozenset(destinations)


def _soldier_ant_destinations(
    board: Board, origin: AxialCoordinate, piece: Piece
) -> frozenset[AxialCoordinate]:
    with _Lifted(board, piece, origin):
        reached: set[AxialCoordinate] = set()
        frontier = [origin]
        while frontier:
            current = frontier.pop()
            for target in _step_targets(board, current, allow_climbing=False):
                if target not in reached and target != origin:
                    reached.add(target)
                    frontier.append(target)
        return frozenset(reached)


def _spider_destinations(
    board: Board, origin: AxialCoordinate, piece: Piece
) -> frozenset[AxialCoordinate]:
    with _Lifted(board, piece, origin):
        destinations: set[AxialCoordinate] = set()

        def walk(
            position: AxialCoordinate, visited: frozenset[AxialCoordinate], steps_left: int
        ) -> None:
            if steps_left == 0:
                destinations.add(position)
                return
            for target in _step_targets(board, position, allow_climbing=False):
                if target not in visited:
                    walk(target, visited | {target}, steps_left - 1)

        walk(origin, frozenset({origin}), 3)
        destinations.discard(origin)
        return frozenset(destinations)


def _ladybug_destinations(
    board: Board, origin: AxialCoordinate, piece: Piece
) -> frozenset[AxialCoordinate]:
    with _Lifted(board, piece, origin):
        destinations: set[AxialCoordinate] = set()
        for _, first_climb in origin.neighbors():
            if not board.is_occupied(first_climb) or board.gate_blocks_slide(origin, first_climb):
                continue
            for _, second_climb in first_climb.neighbors():
                if second_climb == origin or not board.is_occupied(second_climb):
                    continue
                if board.gate_blocks_slide(first_climb, second_climb):
                    continue
                for _, landing in second_climb.neighbors():
                    if board.is_occupied(landing) or board.gate_blocks_slide(second_climb, landing):
                        continue
                    destinations.add(landing)
        destinations.discard(origin)
        return frozenset(destinations)


# Bug Types whose Movement is a fixed pattern independent of what they're touching.
_MOVEMENT_PATTERNS = {
    BugType.QUEEN_BEE: _queen_bee_destinations,
    BugType.BEETLE: _beetle_destinations,
    BugType.GRASSHOPPER: _grasshopper_destinations,
    BugType.SPIDER: _spider_destinations,
    BugType.SOLDIER_ANT: _soldier_ant_destinations,
    BugType.LADYBUG: _ladybug_destinations,
    BugType.PILLBUG: _pillbug_own_destinations,
}


def is_pinned(board: Board, piece: Piece, last_moved_piece: Piece | None) -> bool:
    """Whether `piece` currently cannot be the subject of a Movement or a Throw.

    True when it's covered, is the Last-Moved Piece, or removing it would
    break the One Hive Rule.
    """
    origin = board.find(piece)
    if origin is None or board.top_piece(origin) != piece:
        return True
    if piece == last_moved_piece:
        return True
    return board.would_disconnect_hive(origin)


def movement_destinations(
    board: Board, piece: Piece, last_moved_piece: Piece | None
) -> frozenset[AxialCoordinate]:
    """Every Cell `piece` could legally Move to right now. Empty if it's Pinned."""
    if is_pinned(board, piece, last_moved_piece):
        return frozenset()
    origin = board.find(piece)
    assert origin is not None

    if piece.bug_type is BugType.MOSQUITO:
        return _mosquito_destinations(board, origin, piece)

    pattern = _MOVEMENT_PATTERNS[piece.bug_type]
    return pattern(board, origin, piece)


def _mosquito_destinations(
    board: Board, origin: AxialCoordinate, piece: Piece
) -> frozenset[AxialCoordinate]:
    """A Mosquito copies the movement of every distinct Bug Type it's touching.

    While it's on top of the Hive (it climbed there, so it must have copied a
    Beetle to get there) it keeps moving as a Beetle only, until it climbs
    back down. Touching only other Mosquitoes yields no movement at all.
    """
    is_on_top_of_hive = (board.stack_level(piece) or 0) > 0
    if is_on_top_of_hive:
        return _beetle_destinations(board, origin, piece)

    touched_bug_types = {
        neighbor_piece.bug_type for neighbor_piece in board.neighboring_top_pieces(origin)
    }
    touched_bug_types.discard(BugType.MOSQUITO)
    if not touched_bug_types:
        return frozenset()

    destinations: set[AxialCoordinate] = set()
    for bug_type in touched_bug_types:
        pattern = _MOVEMENT_PATTERNS[bug_type]
        destinations |= pattern(board, origin, piece)
    return frozenset(destinations)


def legal_throws(board: Board, actor: Piece, last_moved_piece: Piece | None) -> frozenset[Throw]:
    """Every legal Throw `actor` (a Pillbug, or a Mosquito copying one) can make right now."""
    origin = board.find(actor)
    if origin is None or board.top_piece(origin) != actor:
        return frozenset()  # covered pieces cannot act at all

    if actor.bug_type is BugType.MOSQUITO:
        is_on_top_of_hive = (board.stack_level(actor) or 0) > 0
        if is_on_top_of_hive:
            return frozenset()
        touching_a_pillbug = any(
            neighbor_piece.bug_type is BugType.PILLBUG
            for neighbor_piece in board.neighboring_top_pieces(origin)
        )
        if not touching_a_pillbug:
            return frozenset()
    elif actor.bug_type is not BugType.PILLBUG:
        return frozenset()

    throws: set[Throw] = set()
    for target_piece in board.neighboring_top_pieces(origin):
        target_cell = board.find(target_piece)
        assert target_cell is not None
        if target_piece == actor:
            continue
        if board.height(target_cell) != 1:
            continue  # cannot throw a piece that is part of a taller Stack
        if target_piece == last_moved_piece:
            continue
        if board.would_disconnect_hive(target_cell):
            continue

        with _Lifted(board, target_piece, target_cell):
            for _, destination in origin.neighbors():
                if destination == target_cell or board.is_occupied(destination):
                    continue
                if _throw_gate_blocks(board, origin, destination):
                    continue
                throws.add(Throw(actor, target_piece, target_cell, destination))
    return frozenset(throws)


def _throw_gate_blocks(
    board: Board, actor_cell: AxialCoordinate, destination: AxialCoordinate
) -> bool:
    """The Freedom to Move Rule applied to a Throw's final drop, from atop the actor."""
    actor_height_with_thrown_piece = board.height(actor_cell) + 1
    required_clearance = max(actor_height_with_thrown_piece, board.height(destination)) + 1
    flank_a, flank_b = tuple(common_neighbors(actor_cell, destination))
    return (
        board.height(flank_a) >= required_clearance and board.height(flank_b) >= required_clearance
    )


def placement_destinations(board: Board, color: Color) -> frozenset[AxialCoordinate]:
    """Every empty Cell `color` could legally Place a new Piece onto right now."""
    if board.is_empty():
        return frozenset({AxialCoordinate(0, 0)})

    has_placed_before = any(placed.color is color for placed in _all_placed_pieces(board))
    empty_cells_touching_hive = {
        neighbor
        for occupied in board.occupied_cells()
        for neighbor in occupied.neighbor_set()
        if not board.is_occupied(neighbor)
    }

    if not has_placed_before:
        return frozenset(empty_cells_touching_hive)

    return frozenset(
        cell
        for cell in empty_cells_touching_hive
        if all(piece.color is color for piece in board.neighboring_top_pieces(cell))
    )


def _all_placed_pieces(board: Board) -> tuple[Piece, ...]:
    return tuple(board.top_piece(cell) for cell in board.occupied_cells()) + tuple(
        piece for cell in board.occupied_cells() for piece in board.stack_at(cell)[:-1]
    )
