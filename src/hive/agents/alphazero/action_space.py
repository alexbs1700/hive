"""action_space.py: the policy head's shape — piece slot x destination cell in the encoding window.

Chess/Go AlphaZero use a fixed action space because their boards are fixed
size. Hive's isn't, so the policy is factored as (which Piece) x (which
Cell in encoding.py's window) instead of one output per absolute board
cell on an unbounded board. "Which Piece" is bounded regardless of board
size — each side has exactly 14 Pieces — so this stays a fixed-size output
no matter how far a game spreads, as long as the destination itself falls
inside the window (see encoding.py's WINDOW_RADIUS derivation).

This uniformly covers Placement, Movement, and Throw: all three are
"a Piece ends up at a Cell" (for Throw, the acted-on Piece is the one
relocated, not the Pillbug doing the throwing — see CONTEXT.md's Move
taxonomy). Pass has no destination Cell, so it isn't part of this spatial
tensor at all; a network exposes it as a separate scalar output.

A Throw can target either side's Piece, so there are 28 slots total: 14 for
the mover's own Pieces, 14 for the opponent's — mirroring encoding.py's
mine/opponent channel split rather than a fixed White/Black one.
"""

from __future__ import annotations

from hive.agents.alphazero import encoding
from hive.game import Game
from hive.moves import Move, Pass
from hive.pieces import STARTING_COUNTS, BugType, Color, Piece


def _generate_piece_slots() -> tuple[tuple[BugType, int | None], ...]:
    slots: list[tuple[BugType, int | None]] = []
    for bug_type, count in STARTING_COUNTS.items():
        if count == 1:
            slots.append((bug_type, None))
        else:
            slots.extend((bug_type, number) for number in range(1, count + 1))
    return tuple(slots)


PIECE_SLOTS: tuple[tuple[BugType, int | None], ...] = _generate_piece_slots()
NUM_PIECE_SLOTS_PER_SIDE = len(PIECE_SLOTS)  # 14
NUM_PIECE_SLOTS = NUM_PIECE_SLOTS_PER_SIDE * 2  # 28: 14 "mine" + 14 "opponent's"

ACTION_SHAPE = (NUM_PIECE_SLOTS, encoding.WINDOW_SIZE, encoding.WINDOW_SIZE)

_SLOT_INDEX: dict[tuple[BugType, int | None], int] = {
    slot: index for index, slot in enumerate(PIECE_SLOTS)
}


def slot_index_for_piece(piece: Piece, my_color: Color) -> int:
    """0-13 if `piece` belongs to `my_color`, 14-27 if it's the opponent's.

    A Throw can target either side's Piece, hence both ranges existing.
    """
    base = 0 if piece.color is my_color else NUM_PIECE_SLOTS_PER_SIDE
    return base + _SLOT_INDEX[(piece.bug_type, piece.number)]


def action_index_for_move(move: Move, game: Game) -> tuple[int, int, int] | None:
    """(slot, row, col) for `move`, or None if `move` is a Pass (no destination Cell to index).

    Raises ValueError if `move`'s destination falls outside the encoding
    window — expected to be exceedingly rare given WINDOW_RADIUS, but
    silently mis-indexing a training target would be worse than failing
    loudly so the caller can decide how to handle it (e.g. skip the sample).
    """
    if isinstance(move, Pass):
        return None

    slot = slot_index_for_piece(move.piece, game.current_turn)
    center = encoding.compute_window_center(game.state.board.occupied_cells())
    coords = encoding.cell_to_window_coords(move.destination, center)
    if coords is None:
        raise ValueError(f"{move!r} destination falls outside the encoding window")
    row, col = coords
    return slot, row, col


def legal_action_map(game: Game) -> dict[tuple[int, int, int] | None, list[Move]]:
    """Every legal Move in `game`, grouped by its action index.

    More than one Move can legitimately share an index: a Piece reachable
    by both its own Movement and a Pillbug's Throw to the same Cell ends up
    in the same place either way (see the web UI's identical move-resolution
    pattern in notation.py), so the policy only needs to represent "this
    Piece ends up here," not which mechanism got it there.
    """
    action_map: dict[tuple[int, int, int] | None, list[Move]] = {}
    for move in game.legal_moves():
        index = action_index_for_move(move, game)
        action_map.setdefault(index, []).append(move)
    return action_map
