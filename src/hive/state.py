"""GameState: the mutable board-plus-bookkeeping a Game makes and unmakes Moves against."""

from __future__ import annotations

from dataclasses import dataclass, field

from hive.board import Board
from hive.pieces import BugType, Color, Piece, reserve_pieces


@dataclass
class GameState:
    """Everything about a Hive game in progress, besides the rules for what's legal.

    `history` is a stack of snapshots of the fields that change on every
    Move (`last_moved_piece`, `current_turn`, `turns_taken`), pushed by
    `push_history` before a Move is applied and popped to undo it. The
    Board and Reserves are restored separately, by reversing the specific
    Placement/Movement/Throw that was made.
    """

    board: Board = field(default_factory=Board)
    reserves: dict[Color, list[Piece]] = field(
        default_factory=lambda: {color: reserve_pieces(color) for color in Color}
    )
    current_turn: Color = Color.WHITE
    turns_taken: dict[Color, int] = field(default_factory=lambda: dict.fromkeys(Color, 0))
    last_moved_piece: Piece | None = None
    history: list[tuple[Piece | None, Color, dict[Color, int]]] = field(default_factory=list)

    def has_placed_queen(self, color: Color) -> bool:
        return not any(piece.bug_type is BugType.QUEEN_BEE for piece in self.reserves[color])

    def must_place_queen_this_turn(self, color: Color) -> bool:
        """True on a Player's 4th Turn if their Queen Bee still isn't on the Board."""
        return self.turns_taken[color] == 3 and not self.has_placed_queen(color)

    def peek_from_reserve(self, color: Color, bug_type: BugType) -> Piece:
        """The next `bug_type` Piece `take_from_reserve` would return, without removing it."""
        for candidate in self.reserves[color]:
            if candidate.bug_type is bug_type:
                return candidate
        raise ValueError(f"{color} has no {bug_type.name} left in Reserve")

    def take_from_reserve(self, color: Color, bug_type: BugType) -> Piece:
        piece = self.peek_from_reserve(color, bug_type)
        self.reserves[color].remove(piece)
        return piece

    def return_to_reserve(self, piece: Piece) -> None:
        self.reserves[piece.color].append(piece)

    def push_history(self) -> None:
        self.history.append((self.last_moved_piece, self.current_turn, dict(self.turns_taken)))

    def pop_history(self) -> None:
        self.last_moved_piece, self.current_turn, turns_taken = self.history.pop()
        self.turns_taken = turns_taken

    def advance_turn(self, new_last_moved_piece: Piece | None) -> None:
        self.turns_taken[self.current_turn] += 1
        self.last_moved_piece = new_last_moved_piece
        self.current_turn = self.current_turn.opponent
