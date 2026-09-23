"""Move Notation: this project's Hive text format, per CONTEXT.md.

Modeled on the Universal Hive Protocol (UHP) convention used by other Hive
engines: a Piece Code, then — for every Move after the game's first — a
Direction Marker attached to a reference Piece Code that's already on the
Board. The three marker symbols each mean one Direction as a suffix
(`ref-`, `ref/`, `ref\\`) and the opposite Direction as a prefix
(`-ref`, `/ref`, `\\ref`); no marker at all means "climb on top of ref".

Parsing resolves a Move by matching it against `Game.legal_moves()` rather
than reconstructing legality independently — Movement and Throw share the
same notation shape (a piece and where it ends up), so whichever one is
actually legal for that destination is what gets returned.
"""

from __future__ import annotations

from hive.board import Board
from hive.coordinates import Direction
from hive.game import Game
from hive.moves import Move, Pass, Placement
from hive.pieces import BugType, Color, Piece

_SUFFIX_DIRECTIONS: dict[str, Direction] = {
    "-": Direction.EAST,
    "/": Direction.NORTHEAST,
    "\\": Direction.SOUTHEAST,
}
_PREFIX_DIRECTIONS: dict[str, Direction] = {
    "-": Direction.WEST,
    "/": Direction.SOUTHWEST,
    "\\": Direction.NORTHWEST,
}
_SUFFIX_FOR_DIRECTION = {direction: symbol for symbol, direction in _SUFFIX_DIRECTIONS.items()}
_PREFIX_FOR_DIRECTION = {direction: symbol for symbol, direction in _PREFIX_DIRECTIONS.items()}

_BUG_TYPE_BY_LETTER = {bug_type.value: bug_type for bug_type in BugType}
_COLOR_BY_LETTER = {color.value: color for color in Color}


def parse_piece_code(code: str) -> tuple[Color, BugType, int | None]:
    """Parse a Piece Code like 'wA1' or 'bQ' into (Color, Bug Type, number)."""
    if len(code) < 2:
        raise ValueError(f"invalid Piece Code: {code!r}")
    color = _COLOR_BY_LETTER.get(code[0])
    bug_type = _BUG_TYPE_BY_LETTER.get(code[1])
    if color is None or bug_type is None:
        raise ValueError(f"invalid Piece Code: {code!r}")
    remainder = code[2:]
    number = int(remainder) if remainder else None
    return color, bug_type, number


def parse_reference(token: str) -> tuple[str, Direction | None]:
    """Split a reference token into its Piece Code and Direction Marker, if any."""
    if token[0] in _PREFIX_DIRECTIONS:
        return token[1:], _PREFIX_DIRECTIONS[token[0]]
    if token[-1] in _SUFFIX_DIRECTIONS:
        return token[:-1], _SUFFIX_DIRECTIONS[token[-1]]
    return token, None


def format_reference(piece_code: str, direction: Direction | None) -> str:
    if direction is None:
        return piece_code
    if direction in _SUFFIX_FOR_DIRECTION:
        return f"{piece_code}{_SUFFIX_FOR_DIRECTION[direction]}"
    return f"{_PREFIX_FOR_DIRECTION[direction]}{piece_code}"


def format_move(move: Move, board: Board) -> str:
    """Render `move` in Move Notation, given the Board's state *before* `move` is applied."""
    if isinstance(move, Pass):
        return "pass"
    if board.is_empty():
        return move.piece.code

    destination = move.destination
    excluded_cells = set() if isinstance(move, Placement) else {move.origin}

    if board.is_occupied(destination):
        reference_piece = board.top_piece(destination)
        assert reference_piece is not None
        return f"{move.piece.code} {reference_piece.code}"

    for direction, neighbor in destination.neighbors():
        if neighbor in excluded_cells or not board.is_occupied(neighbor):
            continue
        reference_piece = board.top_piece(neighbor)
        assert reference_piece is not None
        reference = format_reference(reference_piece.code, direction.opposite)
        return f"{move.piece.code} {reference}"

    raise ValueError(f"cannot format {move!r}: no reference Cell touches its destination")


def parse_move(text: str, game: Game) -> Move:
    """Resolve `text` to one of `game.legal_moves()`. Raises ValueError if none match."""
    text = text.strip()
    if text.lower() == "pass":
        return _find_legal_move(game, lambda move: isinstance(move, Pass))

    tokens = text.split()
    if len(tokens) == 1:
        color, bug_type, number = parse_piece_code(tokens[0])
        return _find_legal_move(game, lambda move: _piece_matches(move, color, bug_type, number))

    if len(tokens) != 2:
        raise ValueError(f"cannot parse Move Notation: {text!r}")

    piece_code, reference_token = tokens
    color, bug_type, number = parse_piece_code(piece_code)
    reference_code, direction = parse_reference(reference_token)
    reference_color, reference_bug_type, reference_number = parse_piece_code(reference_code)

    reference_piece = _find_piece_on_board(
        game.state.board, reference_color, reference_bug_type, reference_number
    )
    if reference_piece is None:
        raise ValueError(f"reference Piece {reference_code!r} is not on the Board")
    reference_cell = game.state.board.find(reference_piece)
    assert reference_cell is not None
    destination = reference_cell if direction is None else reference_cell.neighbor(direction)

    return _find_legal_move(
        game,
        lambda move: (
            _piece_matches(move, color, bug_type, number)
            and getattr(move, "destination", None) == destination
        ),
    )


def _piece_matches(move: Move, color: Color, bug_type: BugType, number: int | None) -> bool:
    piece: Piece | None = getattr(move, "piece", None)
    if piece is None:
        return False
    return piece.color is color and piece.bug_type is bug_type and piece.number == number


def _find_legal_move(game: Game, predicate) -> Move:
    for move in game.legal_moves():
        if predicate(move):
            return move
    raise ValueError("no legal Move matches that notation")


def _find_piece_on_board(
    board: Board, color: Color, bug_type: BugType, number: int | None
) -> Piece | None:
    for cell in board.occupied_cells():
        for piece in board.stack_at(cell):
            if piece.color is color and piece.bug_type is bug_type and piece.number == number:
                return piece
    return None


__all__ = [
    "format_move",
    "format_reference",
    "parse_move",
    "parse_piece_code",
    "parse_reference",
]
