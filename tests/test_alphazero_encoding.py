"""encoding.py: GameState -> fixed-size tensor, egocentric and centroid-centered."""

import pytest

pytest.importorskip("numpy")

from hive.agents.alphazero import encoding  # noqa: E402
from hive.coordinates import AxialCoordinate as Cell  # noqa: E402
from hive.game import Game  # noqa: E402
from hive.moves import Movement  # noqa: E402
from hive.pieces import BugType, Color, Piece  # noqa: E402


def test_encode_has_the_documented_shape() -> None:
    tensor = encoding.encode(Game())
    assert tensor.shape == (encoding.NUM_CHANNELS, encoding.WINDOW_SIZE, encoding.WINDOW_SIZE)


def test_empty_board_centers_the_window_on_the_origin() -> None:
    assert encoding.compute_window_center(frozenset()) == (0, 0)


def test_window_centers_on_the_hives_own_centroid() -> None:
    occupied = frozenset({Cell(0, 0), Cell(10, 0)})
    assert encoding.compute_window_center(occupied) == (5, 0)


def test_encoding_is_from_the_current_players_own_perspective() -> None:
    # White places a Spider on turn 1, then it becomes Black's turn: the
    # Spider now belongs to the *opponent*, not "my" pieces, even though
    # nothing about the piece itself changed — only whose turn it is did.
    game = Game()
    place_spider = next(m for m in game.legal_moves() if m.piece.code == "wS1")
    game.apply_move(place_spider)
    assert game.current_turn is Color.BLACK

    tensor = encoding.encode(game)
    center = encoding.compute_window_center(game.state.board.occupied_cells())
    row, col = encoding.cell_to_window_coords(Cell(0, 0), center)
    spider_bug_index = tuple(BugType).index(BugType.SPIDER)

    assert tensor[spider_bug_index, row, col] == 0.0  # not in "mine"
    num_bug_types = len(tuple(BugType))
    assert tensor[num_bug_types + spider_bug_index, row, col] == 1.0  # in "opponent's"


def test_queen_placed_channels_reflect_each_sides_reserve() -> None:
    game = Game()
    tensor = encoding.encode(game)
    assert (tensor[encoding.MY_QUEEN_PLACED_CHANNEL] == 0.0).all()
    assert (tensor[encoding.OPPONENT_QUEEN_PLACED_CHANNEL] == 0.0).all()


def test_last_moved_piece_marks_exactly_one_cell() -> None:
    game = Game()
    white_queen = Piece(Color.WHITE, BugType.QUEEN_BEE)
    black_queen = Piece(Color.BLACK, BugType.QUEEN_BEE)
    game.state.board.place(Cell(0, 0), white_queen)
    game.state.board.place(Cell(1, 0), black_queen)
    game.state.reserves[Color.WHITE].remove(white_queen)
    game.state.reserves[Color.BLACK].remove(black_queen)
    game.apply_move(Movement(white_queen, Cell(0, 0), Cell(1, -1)))

    tensor = encoding.encode(game)
    center = encoding.compute_window_center(game.state.board.occupied_cells())
    row, col = encoding.cell_to_window_coords(Cell(1, -1), center)

    assert tensor[encoding.LAST_MOVED_CHANNEL, row, col] == 1.0
    assert tensor[encoding.LAST_MOVED_CHANNEL].sum() == 1.0


def test_stack_height_channel_reflects_a_climbed_beetle() -> None:
    game = Game()
    bottom = Piece(Color.WHITE, BugType.SOLDIER_ANT, 1)
    top = Piece(Color.WHITE, BugType.BEETLE, 1)
    game.state.board.place(Cell(0, 0), bottom)
    game.state.board.place(Cell(0, 0), top)

    tensor = encoding.encode(game)
    center = encoding.compute_window_center(game.state.board.occupied_cells())
    row, col = encoding.cell_to_window_coords(Cell(0, 0), center)

    assert tensor[encoding.STACK_HEIGHT_CHANNEL, row, col] > 0.0
