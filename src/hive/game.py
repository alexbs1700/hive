"""Game: the public API — legal_moves(), apply_move(), undo_move(), outcome().

Combines GameState (the mutable board-plus-bookkeeping) with rules.py (the
pure per-Bug-Type legality queries) into the make-move/undo-move engine
described in CONTEXT.md. Deliberately not a Gym/Gymnasium-style RL API yet:
that can be layered on top of this later without touching it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from hive import rules
from hive.moves import Move, Movement, Pass, Placement, Throw
from hive.pieces import BugType, Color
from hive.state import GameState


class Outcome(Enum):
    """A Game's status: still going, a rulebook Win, or a rulebook Draw.

    Never conflated with a demo runner's Inconclusive cutoff (see
    docs/adr/0001-separate-inconclusive-outcome-from-draw.md) — that concept
    doesn't exist at this layer at all.
    """

    IN_PROGRESS = "in_progress"
    WIN = "win"
    DRAW = "draw"


@dataclass(frozen=True, slots=True)
class Result:
    outcome: Outcome
    winner: Color | None = None


class Game:
    """One Hive game in progress, playable via legal_moves()/apply_move()/undo_move()."""

    def __init__(self) -> None:
        self.state = GameState()
        self._applied_moves: list[Move] = []

    @property
    def current_turn(self) -> Color:
        return self.state.current_turn

    def result(self) -> Result:
        white_surrounded = self._is_queen_surrounded(Color.WHITE)
        black_surrounded = self._is_queen_surrounded(Color.BLACK)
        if white_surrounded and black_surrounded:
            return Result(Outcome.DRAW)
        if white_surrounded:
            return Result(Outcome.WIN, winner=Color.BLACK)
        if black_surrounded:
            return Result(Outcome.WIN, winner=Color.WHITE)
        return Result(Outcome.IN_PROGRESS)

    def is_over(self) -> bool:
        return self.result().outcome is not Outcome.IN_PROGRESS

    def _is_queen_surrounded(self, color: Color) -> bool:
        board = self.state.board
        queen = next(
            (
                piece
                for cell in board.occupied_cells()
                for piece in board.stack_at(cell)
                if piece.color is color and piece.bug_type is BugType.QUEEN_BEE
            ),
            None,
        )
        if queen is None:
            return False
        queen_cell = board.find(queen)
        assert queen_cell is not None
        return len(board.occupied_neighbors(queen_cell)) == 6

    def legal_moves(self) -> list[Move]:
        """Every legal Move for the Player to act, or a single Pass if there are none."""
        if self.is_over():
            return []

        color = self.state.current_turn
        board = self.state.board
        moves: list[Move] = []

        if self.state.must_place_queen_this_turn(color):
            available_bug_types = {BugType.QUEEN_BEE}
        else:
            available_bug_types = {piece.bug_type for piece in self.state.reserves[color]}
            if self.state.turns_taken[color] == 0:
                # A Player's very first Placement may never be their Queen Bee.
                available_bug_types.discard(BugType.QUEEN_BEE)
        placement_cells = rules.placement_destinations(board, color)
        for bug_type in available_bug_types:
            piece = self.state.peek_from_reserve(color, bug_type)
            moves.extend(Placement(piece, cell) for cell in placement_cells)

        if self.state.has_placed_queen(color):
            for cell in board.occupied_cells():
                piece = board.top_piece(cell)
                if piece is None or piece.color is not color:
                    continue
                moves.extend(
                    Movement(piece, cell, destination)
                    for destination in rules.movement_destinations(
                        board, piece, self.state.last_moved_piece
                    )
                )
                moves.extend(rules.legal_throws(board, piece, self.state.last_moved_piece))

        return moves if moves else [Pass(color)]

    def apply_move(self, move: Move) -> None:
        self.state.push_history()
        match move:
            case Placement(piece, destination):
                taken = self.state.take_from_reserve(piece.color, piece.bug_type)
                assert taken == piece
                self.state.board.place(destination, piece)
                self.state.advance_turn(new_last_moved_piece=None)
            case Movement(piece, origin, destination):
                removed = self.state.board.remove_top(origin)
                assert removed == piece
                self.state.board.place(destination, piece)
                self.state.advance_turn(new_last_moved_piece=piece)
            case Throw(piece=piece, origin=origin, destination=destination):
                removed = self.state.board.remove_top(origin)
                assert removed == piece
                self.state.board.place(destination, piece)
                self.state.advance_turn(new_last_moved_piece=piece)
            case Pass():
                self.state.advance_turn(new_last_moved_piece=None)
            case _:
                raise TypeError(f"unknown Move type: {move!r}")
        self._applied_moves.append(move)

    def undo_move(self) -> None:
        """Reverse the most recently applied Move."""
        move = self._applied_moves.pop()
        match move:
            case Placement(piece, destination):
                removed = self.state.board.remove_top(destination)
                assert removed == piece
                self.state.return_to_reserve(piece)
            case (
                Movement(piece, origin, destination)
                | Throw(piece=piece, origin=origin, destination=destination)
            ):
                removed = self.state.board.remove_top(destination)
                assert removed == piece
                self.state.board.place(origin, piece)
            case Pass():
                pass
            case _:
                raise TypeError(f"unknown Move type: {move!r}")
        self.state.pop_history()
