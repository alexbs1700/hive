"""Game: turn order, the Queen Bee placement window, apply/undo round trips, outcomes."""

from hive.coordinates import AxialCoordinate as Cell
from hive.game import Game, Outcome
from hive.moves import Movement, Pass, Placement
from hive.pieces import BugType, Color, Piece
from hive.state import GameState


def test_the_games_very_first_move_is_a_placement_at_the_origin_and_never_the_queen() -> None:
    game = Game()
    moves = game.legal_moves()

    assert all(isinstance(move, Placement) and move.destination == Cell(0, 0) for move in moves)
    bug_types = {move.piece.bug_type for move in moves}
    assert BugType.QUEEN_BEE not in bug_types
    assert len(bug_types) == 7  # every Bug Type except the Queen Bee


def test_a_players_second_turn_may_place_the_queen_bee() -> None:
    game = Game()
    game.apply_move(Placement(Piece(Color.WHITE, BugType.SOLDIER_ANT, 1), Cell(0, 0)))
    game.apply_move(Placement(Piece(Color.BLACK, BugType.SOLDIER_ANT, 1), Cell(1, 0)))

    bug_types = {move.piece.bug_type for move in game.legal_moves() if isinstance(move, Placement)}
    assert BugType.QUEEN_BEE in bug_types


def test_movement_and_throws_are_unavailable_before_a_players_own_queen_is_placed() -> None:
    game = Game()
    game.apply_move(Placement(Piece(Color.WHITE, BugType.SOLDIER_ANT, 1), Cell(0, 0)))
    game.apply_move(Placement(Piece(Color.BLACK, BugType.SOLDIER_ANT, 1), Cell(1, 0)))

    assert all(isinstance(move, Placement) for move in game.legal_moves())


def test_a_player_must_place_their_queen_on_their_fourth_turn() -> None:
    game = Game()
    non_queen_types = [BugType.SOLDIER_ANT, BugType.SPIDER, BugType.GRASSHOPPER]
    cell = Cell(0, 0)
    for index, bug_type in enumerate(non_queen_types):
        piece = Piece(Color.WHITE, bug_type, 1)
        game.state.board.place(cell, piece)
        game.state.reserves[Color.WHITE].remove(piece)
        game.state.turns_taken[Color.WHITE] = index + 1

    bug_types = {move.piece.bug_type for move in game.legal_moves() if isinstance(move, Placement)}
    assert bug_types == {BugType.QUEEN_BEE}


def test_applying_a_placement_then_undoing_it_restores_the_prior_state() -> None:
    game = Game()
    # `return_to_reserve` appends rather than re-inserting in place, so the
    # Reserve's exact order isn't preserved — only its contents are.
    before_reserve = set(game.state.reserves[Color.WHITE])
    before_turn = game.state.current_turn
    before_turns_taken = dict(game.state.turns_taken)

    move = Placement(Piece(Color.WHITE, BugType.SOLDIER_ANT, 1), Cell(0, 0))
    game.apply_move(move)
    game.undo_move()

    assert game.state.board.is_empty()
    assert set(game.state.reserves[Color.WHITE]) == before_reserve
    assert game.state.current_turn == before_turn
    assert game.state.turns_taken == before_turns_taken
    assert game.state.last_moved_piece is None


def test_applying_a_movement_then_undoing_it_restores_the_prior_state() -> None:
    game = Game()
    queen = Piece(Color.WHITE, BugType.QUEEN_BEE)
    other = Piece(Color.BLACK, BugType.QUEEN_BEE)
    game.state.board.place(Cell(0, 0), queen)
    game.state.board.place(Cell(1, 0), other)
    game.state.reserves[Color.WHITE].remove(queen)
    game.state.reserves[Color.BLACK].remove(other)

    move = Movement(queen, Cell(0, 0), Cell(1, -1))
    game.apply_move(move)
    assert game.state.last_moved_piece == queen
    assert game.state.board.find(queen) == Cell(1, -1)

    game.undo_move()
    assert game.state.board.find(queen) == Cell(0, 0)
    assert game.state.last_moved_piece is None


def test_last_moved_piece_reflects_only_the_immediately_preceding_turn() -> None:
    # last_moved_piece exists to block a Pillbug Throw's target (see
    # test_pillbug.py) for exactly one Turn. Since ordinary Movement only
    # ever acts on the mover's own color, and last_moved_piece is
    # overwritten every Turn, a Piece moved via ordinary Movement is never
    # actually prevented from moving again on its owner's own next turn —
    # by the time that turn comes around, last_moved_piece already reflects
    # whatever the opponent did in between.
    game = Game()
    white_queen = Piece(Color.WHITE, BugType.QUEEN_BEE)
    black_queen = Piece(Color.BLACK, BugType.QUEEN_BEE)
    game.state.board.place(Cell(0, 0), white_queen)
    game.state.board.place(Cell(1, 0), black_queen)
    game.state.reserves[Color.WHITE].remove(white_queen)
    game.state.reserves[Color.BLACK].remove(black_queen)

    game.apply_move(Movement(white_queen, Cell(0, 0), Cell(1, -1)))
    assert game.state.last_moved_piece == white_queen

    game.apply_move(Movement(black_queen, Cell(1, 0), Cell(0, -1)))
    assert game.state.last_moved_piece == black_queen

    white_queen_moves = [
        move
        for move in game.legal_moves()
        if isinstance(move, Movement) and move.piece == white_queen
    ]
    assert white_queen_moves != []


def test_last_moved_piece_clears_after_a_placement_or_a_pass() -> None:
    game = Game()
    queen = Piece(Color.WHITE, BugType.QUEEN_BEE)
    other = Piece(Color.BLACK, BugType.QUEEN_BEE)
    game.state.board.place(Cell(0, 0), queen)
    game.state.board.place(Cell(1, 0), other)
    game.state.reserves[Color.WHITE].remove(queen)
    game.state.reserves[Color.BLACK].remove(other)

    game.apply_move(Movement(queen, Cell(0, 0), Cell(1, -1)))
    assert game.state.last_moved_piece == queen

    game.apply_move(Pass(Color.BLACK))
    assert game.state.last_moved_piece is None


def test_a_player_with_no_legal_move_passes() -> None:
    # A lone Queen Bee, with nothing left in Reserve and no legal Movement
    # (it's the Last-Moved Piece), has no option but to Pass.
    game = Game()
    game.state = GameState()
    queen = Piece(Color.WHITE, BugType.QUEEN_BEE)
    game.state.board.place(Cell(0, 0), queen)
    game.state.reserves[Color.WHITE] = []
    game.state.last_moved_piece = queen

    assert game.legal_moves() == [Pass(Color.WHITE)]


def test_a_player_wins_when_only_the_opponents_queen_is_surrounded() -> None:
    game = Game()
    black_queen = Piece(Color.BLACK, BugType.QUEEN_BEE)
    game.state.board.place(Cell(0, 0), black_queen)
    for _, neighbor in Cell(0, 0).neighbors():
        game.state.board.place(neighbor, Piece(Color.WHITE, BugType.SOLDIER_ANT, 1))

    result = game.result()
    assert result.outcome is Outcome.WIN
    assert result.winner is Color.WHITE
    assert game.is_over()
    assert game.legal_moves() == []


def test_the_game_is_drawn_when_both_queens_are_surrounded_at_once() -> None:
    game = Game()
    white_queen = Piece(Color.WHITE, BugType.QUEEN_BEE)
    black_queen = Piece(Color.BLACK, BugType.QUEEN_BEE)
    game.state.board.place(Cell(0, 0), white_queen)
    game.state.board.place(Cell(2, 0), black_queen)
    for _, neighbor in Cell(0, 0).neighbors():
        if neighbor == Cell(1, 0):
            continue
        game.state.board.place(neighbor, Piece(Color.BLACK, BugType.SOLDIER_ANT, 1))
    for _, neighbor in Cell(2, 0).neighbors():
        if neighbor == Cell(1, 0):
            continue
        game.state.board.place(neighbor, Piece(Color.WHITE, BugType.SOLDIER_ANT, 2))
    game.state.board.place(Cell(1, 0), Piece(Color.WHITE, BugType.SOLDIER_ANT, 3))

    assert game.result().outcome is Outcome.DRAW
