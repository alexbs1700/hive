"""Every Cell has exactly six distinct neighbors, and adjacency is symmetric."""

from hive.coordinates import ALL_DIRECTIONS, AxialCoordinate, common_neighbors


def test_a_cell_has_six_distinct_neighbors() -> None:
    origin = AxialCoordinate(0, 0)
    neighbor_cells = origin.neighbor_set()
    assert len(neighbor_cells) == 6


def test_direction_and_its_opposite_are_mutually_reachable() -> None:
    origin = AxialCoordinate(0, 0)
    for direction in ALL_DIRECTIONS:
        neighbor = origin.neighbor(direction)
        assert neighbor.neighbor(direction.opposite) == origin


def test_is_adjacent_to_is_symmetric() -> None:
    origin = AxialCoordinate(0, 0)
    for _, neighbor in origin.neighbors():
        assert origin.is_adjacent_to(neighbor)
        assert neighbor.is_adjacent_to(origin)


def test_a_cell_is_not_adjacent_to_itself() -> None:
    origin = AxialCoordinate(0, 0)
    assert not origin.is_adjacent_to(origin)


def test_direction_to_round_trips_with_neighbor() -> None:
    origin = AxialCoordinate(2, -3)
    for direction in ALL_DIRECTIONS:
        neighbor = origin.neighbor(direction)
        assert origin.direction_to(neighbor) is direction


def test_direction_to_is_none_for_non_adjacent_cells() -> None:
    origin = AxialCoordinate(0, 0)
    far_away = AxialCoordinate(10, 10)
    assert origin.direction_to(far_away) is None


def test_two_adjacent_cells_have_exactly_two_common_neighbors() -> None:
    origin = AxialCoordinate(0, 0)
    for _, neighbor in origin.neighbors():
        assert len(common_neighbors(origin, neighbor)) == 2


def test_common_neighbors_are_mutual_neighbors_of_both_cells() -> None:
    origin = AxialCoordinate(0, 0)
    _, neighbor = origin.neighbors()[0]
    for common in common_neighbors(origin, neighbor):
        assert origin.is_adjacent_to(common)
        assert neighbor.is_adjacent_to(common)
