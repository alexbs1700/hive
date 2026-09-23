"""A deliberately basic terminal UI for Hive: human vs human, via Move Notation.

Two entry points (see pyproject.toml's [project.scripts]):
- `hive-play`  (this module's `main`) — two people take turns at one keyboard.
- `hive-demo`  (hive.demo's `main`)   — a random-move self-play smoke test.
"""

from __future__ import annotations

from hive.board import Board
from hive.coordinates import AxialCoordinate
from hive.game import Game, Outcome
from hive.moves import Move
from hive.notation import format_move, parse_move
from hive.pieces import Piece

_CELL_WIDTH = 6


def render_board(board: Board) -> str:
    """A simple offset-row ASCII rendering of the Board, skewed by row like a hex grid."""
    occupied = board.occupied_cells()
    if not occupied:
        return "(empty board)"

    min_q = min(cell.q for cell in occupied) - 1
    max_q = max(cell.q for cell in occupied) + 1
    min_r = min(cell.r for cell in occupied) - 1
    max_r = max(cell.r for cell in occupied) + 1

    lines = []
    for r in range(min_r, max_r + 1):
        indent = " " * ((r - min_r) * (_CELL_WIDTH // 2))
        row_cells = []
        for q in range(min_q, max_q + 1):
            cell = AxialCoordinate(q, r)
            top = board.top_piece(cell)
            label = "." if top is None else top.code
            height = board.height(cell)
            if height > 1:
                label += f"^{height}"
            row_cells.append(f"{label:<{_CELL_WIDTH}}")
        lines.append(indent + "".join(row_cells).rstrip())
    return "\n".join(lines)


def _format_reserve(pieces: list[Piece]) -> str:
    if not pieces:
        return "(empty)"
    ordered = sorted(pieces, key=lambda piece: (piece.bug_type.value, piece.number or 0))
    return ", ".join(piece.code for piece in ordered)


def _print_status(game: Game) -> None:
    print()
    print(render_board(game.state.board))
    print()
    print(f"{game.current_turn.name}'s turn.")
    print(f"  Reserve: {_format_reserve(game.state.reserves[game.current_turn])}")


def _prompt_move(game: Game) -> Move:
    legal_moves = game.legal_moves()
    while True:
        try:
            text = input(
                "Move (Move Notation, 'moves' to list legal moves, 'quit' to exit): "
            ).strip()
        except EOFError:
            raise SystemExit(0) from None

        if text.lower() in {"quit", "exit"}:
            raise SystemExit(0)
        if text.lower() == "moves":
            for move in legal_moves:
                print(f"  {format_move(move, game.state.board)}")
            continue

        try:
            return parse_move(text, game)
        except ValueError as error:
            print(f"  {error}")


def _print_result(game: Game) -> None:
    print()
    print(render_board(game.state.board))
    print()
    result = game.result()
    if result.outcome is Outcome.DRAW:
        print("Draw: both Queen Bees were surrounded at once.")
    elif result.outcome is Outcome.WIN:
        assert result.winner is not None
        print(f"{result.winner.name} wins!")


def play() -> None:
    game = Game()
    print("Hive — terminal UI. Type 'moves' to list legal moves, 'quit' to exit.")
    while not game.is_over():
        _print_status(game)
        move = _prompt_move(game)
        text = format_move(move, game.state.board)
        game.apply_move(move)
        print(f"-> {text}")
    _print_result(game)


def main() -> None:
    play()


if __name__ == "__main__":
    main()
