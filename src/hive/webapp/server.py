"""A very basic local web UI for Hive: a JSON API over `Game`, plus a static frontend.

One `Game` lives in server memory for the lifetime of the process — this is
a local pass-and-play tool for one browser tab, not a multi-user service.
The frontend never re-derives legality; every click is validated against
`game.legal_moves()` on the server, the same way notation.py resolves
Move Notation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, send_from_directory

from hive.coordinates import AxialCoordinate
from hive.game import Game
from hive.moves import Move, Movement, Pass, Placement, Throw
from hive.pieces import BugType, Color

_STATIC_DIR = Path(__file__).parent / "static"

app = Flask(__name__, static_folder=str(_STATIC_DIR), static_url_path="/static")
game = Game()


def _serialize_move(move: Move) -> dict[str, Any]:
    if isinstance(move, Pass):
        return {"kind": "pass"}
    if isinstance(move, Placement):
        return {
            "kind": "placement",
            "piece": move.piece.code,
            "to": {"q": move.destination.q, "r": move.destination.r},
        }
    if isinstance(move, Movement):
        return {
            "kind": "movement",
            "piece": move.piece.code,
            "from": {"q": move.origin.q, "r": move.origin.r},
            "to": {"q": move.destination.q, "r": move.destination.r},
        }
    if isinstance(move, Throw):
        return {
            "kind": "throw",
            "thrower": move.thrower.code,
            "piece": move.piece.code,
            "from": {"q": move.origin.q, "r": move.origin.r},
            "to": {"q": move.destination.q, "r": move.destination.r},
        }
    raise TypeError(f"unknown Move type: {move!r}")


def _reserve_summary(color: Color) -> list[dict[str, Any]]:
    counts: dict[BugType, int] = {}
    for piece in game.state.reserves[color]:
        counts[piece.bug_type] = counts.get(piece.bug_type, 0) + 1
    # `code` must be the exact Piece Code Game.legal_moves() would offer for
    # a Placement of this Bug Type (the next-numbered Piece in Reserve), so
    # the frontend can match a reserve item against a legal move by code.
    return [
        {
            "bug_type": bug_type.name,
            "code": game.state.peek_from_reserve(color, bug_type).code,
            "count": count,
        }
        for bug_type, count in counts.items()
    ]


def serialize_state() -> dict[str, Any]:
    board = game.state.board
    board_cells = [
        {"q": cell.q, "r": cell.r, "stack": [piece.code for piece in board.stack_at(cell)]}
        for cell in board.occupied_cells()
    ]
    result = game.result()
    legal_moves = [] if game.is_over() else [_serialize_move(move) for move in game.legal_moves()]

    return {
        "board": board_cells,
        "reserves": {color.name.lower(): _reserve_summary(color) for color in Color},
        "current_turn": game.current_turn.name.lower(),
        "is_over": game.is_over(),
        "result": {
            "outcome": result.outcome.value,
            "winner": result.winner.name.lower() if result.winner is not None else None,
        },
        "legal_moves": legal_moves,
        "can_undo": game.can_undo,
    }


def _find_legal_move(payload: dict[str, Any]) -> Move | None:
    if payload.get("pass"):
        for move in game.legal_moves():
            if isinstance(move, Pass):
                return move
        return None

    piece_code = payload.get("piece")
    to = payload.get("to")
    if not piece_code or not isinstance(to, dict):
        return None
    try:
        destination = AxialCoordinate(int(to["q"]), int(to["r"]))
    except (KeyError, TypeError, ValueError):
        return None

    for move in game.legal_moves():
        move_piece = getattr(move, "piece", None)
        matches = move_piece is not None and move_piece.code == piece_code
        if matches and getattr(move, "destination", None) == destination:
            return move
    return None


@app.get("/")
def index() -> Any:
    return send_from_directory(_STATIC_DIR, "index.html")


@app.get("/api/state")
def api_state() -> Any:
    return jsonify(serialize_state())


@app.post("/api/move")
def api_move() -> Any:
    payload = request.get_json(force=True, silent=True) or {}
    move = _find_legal_move(payload)
    if move is None:
        return jsonify({"error": "that is not a legal move"}), 400
    game.apply_move(move)
    return jsonify(serialize_state())


@app.post("/api/undo")
def api_undo() -> Any:
    if game.can_undo:
        game.undo_move()
    return jsonify(serialize_state())


@app.post("/api/new_game")
def api_new_game() -> Any:
    global game
    game = Game()
    return jsonify(serialize_state())


def main() -> None:
    port = 5183
    print(f"Hive web UI running at http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=False)


if __name__ == "__main__":
    main()
