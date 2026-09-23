"""Move Notation: parse/format round trips, resolved against a live Game's legal Moves."""

from hive.coordinates import AxialCoordinate as Cell
from hive.game import Game
from hive.moves import Movement, Pass, Placement
from hive.notation import format_move, parse_move, parse_piece_code
from hive.pieces import BugType, Color
from hive.state import GameState


def test_parses_a_piece_code() -> None:
    assert parse_piece_code("wA1") == (Color.WHITE, BugType.SOLDIER_ANT, 1)
    assert parse_piece_code("bQ") == (Color.BLACK, BugType.QUEEN_BEE, None)


def test_the_games_first_move_is_notated_as_the_bare_piece_code() -> None:
    game = Game()
    move = parse_move("wS1", game)
    assert isinstance(move, Placement)
    assert move.piece.code == "wS1"
    assert move.destination == Cell(0, 0)
    assert format_move(move, game.state.board) == "wS1"


def test_a_placement_notation_round_trips_through_format_and_parse() -> None:
    game = Game()
    ant = game.state.peek_from_reserve(Color.WHITE, BugType.SOLDIER_ANT)
    game.apply_move(Placement(ant, Cell(0, 0)))

    for move in game.legal_moves():
        text = format_move(move, game.state.board)
        assert parse_move(text, game) == move


def test_a_movement_notation_round_trips_through_format_and_parse() -> None:
    game = Game()
    white_queen = game.state.peek_from_reserve(Color.WHITE, BugType.QUEEN_BEE)
    black_queen = game.state.peek_from_reserve(Color.BLACK, BugType.QUEEN_BEE)
    game.apply_move(Placement(white_queen, Cell(0, 0)))
    game.apply_move(Placement(black_queen, Cell(1, 0)))

    movement_moves = [move for move in game.legal_moves() if isinstance(move, Movement)]
    assert movement_moves
    for move in movement_moves:
        text = format_move(move, game.state.board)
        assert parse_move(text, game) == move


def test_pass_notation_round_trips() -> None:
    game = Game()
    game.state = GameState()
    queen = game.state.peek_from_reserve(Color.WHITE, BugType.QUEEN_BEE)
    game.state.board.place(Cell(0, 0), queen)
    game.state.reserves[Color.WHITE] = []
    game.state.last_moved_piece = queen

    move = parse_move("pass", game)
    assert move == Pass(Color.WHITE)
    assert format_move(move, game.state.board) == "pass"


def test_climbing_notation_has_no_direction_marker() -> None:
    game = Game()
    beetle = game.state.peek_from_reserve(Color.WHITE, BugType.BEETLE)
    other = game.state.peek_from_reserve(Color.BLACK, BugType.QUEEN_BEE)
    game.state.board.place(Cell(0, 0), beetle)
    game.state.board.place(Cell(1, 0), other)
    game.state.reserves[Color.WHITE].remove(beetle)
    game.state.reserves[Color.BLACK].remove(other)

    move = Movement(beetle, Cell(0, 0), Cell(1, 0))
    text = format_move(move, game.state.board)
    assert text == "wB1 bQ"
