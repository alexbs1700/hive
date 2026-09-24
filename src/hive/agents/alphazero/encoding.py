"""encoding.py: a Game's current position as a fixed-size tensor.

The Board is unbounded, so this crops to a window centered on the hive's
own centroid, recomputed from the current position every time — not a
fixed world coordinate. A long game can in principle drift arbitrarily far
from wherever the first piece happened to land (any piece, including the
first one placed, can walk away over enough turns), so re-centering on the
hive's own centroid each time is the only choice that stays correct
regardless of game length.

WINDOW_RADIUS was picked from real data, not guessed: sampling 60 random
`hive-demo`-style games (up to the 400-move cap) found a max Cell distance
of 11 from the game's own origin. WINDOW_RADIUS=14 leaves comfortable
margin over that, and centroid-centering (tighter than origin-centering)
gives more room still.

The encoding is always from the current Player's own perspective — "my"
Bug Type planes and "opponent's" Bug Type planes, never hardcoded to
White/Black — so the network only ever has to learn one side's strategy.
"""

from __future__ import annotations

import numpy as np

from hive.coordinates import AxialCoordinate
from hive.game import Game
from hive.pieces import BugType, Color

WINDOW_RADIUS = 14
WINDOW_SIZE = 2 * WINDOW_RADIUS + 1

_BUG_TYPES: tuple[BugType, ...] = tuple(BugType)  # stable declaration order: 8 types
_NUM_BUG_TYPES = len(_BUG_TYPES)
_BUG_TYPE_INDEX: dict[BugType, int] = {bug_type: i for i, bug_type in enumerate(_BUG_TYPES)}

# Channels: [my 8 Bug Type planes][opponent's 8][stack height][my Queen placed]
# [opponent's Queen placed][turn number][Last-Moved Piece marker].
STACK_HEIGHT_CHANNEL = _NUM_BUG_TYPES * 2
MY_QUEEN_PLACED_CHANNEL = STACK_HEIGHT_CHANNEL + 1
OPPONENT_QUEEN_PLACED_CHANNEL = STACK_HEIGHT_CHANNEL + 2
TURN_NUMBER_CHANNEL = STACK_HEIGHT_CHANNEL + 3
LAST_MOVED_CHANNEL = STACK_HEIGHT_CHANNEL + 4
NUM_CHANNELS = LAST_MOVED_CHANNEL + 1

_MAX_STACK_HEIGHT_FOR_NORMALIZATION = 5.0  # a Beetle/Mosquito Stack rarely exceeds this
_MAX_TURN_FOR_NORMALIZATION = 200.0  # generous headroom; only keeps the scalar plane in [0, 1]


def compute_window_center(occupied_cells: frozenset[AxialCoordinate]) -> tuple[int, int]:
    """The (q, r) the encoding window is centered on: the hive's own centroid, rounded."""
    if not occupied_cells:
        return 0, 0
    mean_q = sum(cell.q for cell in occupied_cells) / len(occupied_cells)
    mean_r = sum(cell.r for cell in occupied_cells) / len(occupied_cells)
    return round(mean_q), round(mean_r)


def cell_to_window_coords(cell: AxialCoordinate, center: tuple[int, int]) -> tuple[int, int] | None:
    """(row, col) for `cell` within the window centered on `center`, or None if it falls outside."""
    center_q, center_r = center
    row = cell.r - center_r + WINDOW_RADIUS
    col = cell.q - center_q + WINDOW_RADIUS
    if 0 <= row < WINDOW_SIZE and 0 <= col < WINDOW_SIZE:
        return row, col
    return None


def encode(game: Game) -> np.ndarray:
    """The current position as a (NUM_CHANNELS, WINDOW_SIZE, WINDOW_SIZE) float32 array."""
    board = game.state.board
    my_color = game.current_turn
    opponent_color = my_color.opponent
    occupied = board.occupied_cells()
    center = compute_window_center(occupied)

    tensor = np.zeros((NUM_CHANNELS, WINDOW_SIZE, WINDOW_SIZE), dtype=np.float32)

    for cell in occupied:
        coords = cell_to_window_coords(cell, center)
        if coords is None:
            continue  # position outgrew the window; drop the cell rather than crash
        row, col = coords
        piece = board.top_piece(cell)
        assert piece is not None
        color_offset = 0 if piece.color is my_color else _NUM_BUG_TYPES
        tensor[color_offset + _BUG_TYPE_INDEX[piece.bug_type], row, col] = 1.0
        tensor[STACK_HEIGHT_CHANNEL, row, col] = (
            board.height(cell) / _MAX_STACK_HEIGHT_FOR_NORMALIZATION
        )

    tensor[MY_QUEEN_PLACED_CHANNEL, :, :] = float(game.state.has_placed_queen(my_color))
    tensor[OPPONENT_QUEEN_PLACED_CHANNEL, :, :] = float(game.state.has_placed_queen(opponent_color))
    total_turns = game.state.turns_taken[Color.WHITE] + game.state.turns_taken[Color.BLACK]
    tensor[TURN_NUMBER_CHANNEL, :, :] = min(total_turns / _MAX_TURN_FOR_NORMALIZATION, 1.0)

    last_moved = game.state.last_moved_piece
    if last_moved is not None:
        last_moved_cell = board.find(last_moved)
        if last_moved_cell is not None:
            coords = cell_to_window_coords(last_moved_cell, center)
            if coords is not None:
                tensor[LAST_MOVED_CHANNEL, coords[0], coords[1]] = 1.0

    return tensor
