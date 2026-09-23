"""The web UI's JSON API: serialization, move resolution, and state mutation."""

import pytest

from hive.coordinates import AxialCoordinate
from hive.pieces import BugType, Color, Piece
from hive.webapp import server as webapp_server


@pytest.fixture(autouse=True)
def _fresh_game():
    webapp_server.game = webapp_server.Game()
    yield


@pytest.fixture
def client():
    webapp_server.app.testing = True
    return webapp_server.app.test_client()


def test_index_serves_the_page(client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert b"<title>Hive</title>" in response.data


def test_initial_state_offers_seven_non_queen_placements_at_the_origin(client) -> None:
    state = client.get("/api/state").get_json()
    assert state["current_turn"] == "white"
    assert state["can_undo"] is False
    placements = [move for move in state["legal_moves"] if move["kind"] == "placement"]
    assert len(placements) == 7
    assert all(move["to"] == {"q": 0, "r": 0} for move in placements)
    assert all(move["piece"][1] != "Q" for move in placements)


def test_reserve_codes_match_the_piece_codes_legal_moves_actually_uses(client) -> None:
    # Regression test: reserve display codes were built without the
    # disambiguating number (e.g. "wA" instead of "wA1"), so every
    # multi-count Bug Type silently never matched a legal placement.
    state = client.get("/api/state").get_json()
    placements = [move for move in state["legal_moves"] if move["kind"] == "placement"]
    placement_codes = {move["piece"] for move in placements}
    reserve_codes = {item["code"] for item in state["reserves"]["white"]}
    assert placement_codes <= reserve_codes


def test_move_endpoint_applies_a_legal_placement(client) -> None:
    response = client.post("/api/move", json={"piece": "wS1", "to": {"q": 0, "r": 0}})
    assert response.status_code == 200
    state = response.get_json()
    assert state["current_turn"] == "black"
    assert state["board"] == [{"q": 0, "r": 0, "stack": ["wS1"]}]
    assert state["can_undo"] is True


def test_move_endpoint_rejects_an_illegal_move(client) -> None:
    response = client.post("/api/move", json={"piece": "wQ", "to": {"q": 5, "r": 5}})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_undo_endpoint_reverses_the_last_move(client) -> None:
    client.post("/api/move", json={"piece": "wS1", "to": {"q": 0, "r": 0}})
    response = client.post("/api/undo")
    state = response.get_json()
    assert state["board"] == []
    assert state["current_turn"] == "white"
    assert state["can_undo"] is False


def test_undo_endpoint_is_a_no_op_with_nothing_to_undo(client) -> None:
    response = client.post("/api/undo")
    assert response.status_code == 200
    assert response.get_json()["can_undo"] is False


def test_new_game_endpoint_resets_state(client) -> None:
    client.post("/api/move", json={"piece": "wS1", "to": {"q": 0, "r": 0}})
    response = client.post("/api/new_game")
    state = response.get_json()
    assert state["board"] == []
    assert state["current_turn"] == "white"


def test_pass_move_is_resolved_when_it_is_the_only_legal_move(client) -> None:
    webapp_server.game.state.reserves[Color.WHITE] = []
    queen = Piece(Color.WHITE, BugType.QUEEN_BEE)
    webapp_server.game.state.board.place(AxialCoordinate(0, 0), queen)
    webapp_server.game.state.last_moved_piece = queen

    response = client.post("/api/move", json={"pass": True})
    assert response.status_code == 200
    assert response.get_json()["current_turn"] == "black"
