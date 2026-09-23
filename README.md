# hive

A from-scratch Python implementation of the board game [Hive](https://gen42.com/games/hive) (base game plus the Mosquito, Ladybug, and Pillbug expansions), built as the future environment for a self-play-trained GANN.

This phase covers the rules engine and a basic terminal UI only — no ML/training code yet. See [CONTEXT.md](CONTEXT.md) for the project's vocabulary and [docs/adr/](docs/adr/) for recorded design decisions.

## Setup

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Play

```bash
uv run hive-play
```

Two people take turns at one keyboard. Moves are entered in this project's Move Notation (see [CONTEXT.md](CONTEXT.md#notation)) — e.g. `wS1` for the game's opening placement, then `bA1 wS1-` to place Black's first Ant touching the east side of White's Spider. Type `moves` at any prompt to list every legal move, or `quit` to exit.

## Run the self-play demo

A smoke test that plays many games of random-legal-move self-play and reports outcome statistics — useful for confirming the engine runs to completion without crashing or hanging, ahead of any real training:

```bash
uv run hive-demo --games 100 --max-moves 400 --seed 42
```

`--max-moves` is a safety cap specific to this demo runner (not a rule of Hive — the engine itself is unbounded); a game that hits it is reported `inconclusive`, never `draw`.

## Development

```bash
uv run pytest       # run the test suite
uv run ruff check .   # lint
uv run ruff format .  # format
```

### A local environment quirk

In at least one sandboxed execution environment this project was developed in, Python's `.pth`-based editable install mechanism silently doesn't run (confirmed with a fresh, unrelated `uv venv` too, so it isn't specific to this project). `uv run pytest` isn't affected — `pyproject.toml` sets `pythonpath = ["src"]`, which is pytest's own mechanism, independent of `.pth` processing. But if `uv run hive-play` or `uv run hive-demo` fails with `ModuleNotFoundError: No module named 'hive'`, prefix the command with `PYTHONPATH=src`:

```bash
PYTHONPATH=src uv run hive-play
```

If your terminal doesn't hit this (most won't), you can ignore this section entirely.
