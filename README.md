# hive

A from-scratch Python implementation of the board game [Hive](https://gen42.com/games/hive) (base game plus the Mosquito, Ladybug, and Pillbug expansions), built as the future environment for a self-play-trained GANN.

This phase covers the rules engine plus a terminal and a browser UI — no ML/training code yet. See [CONTEXT.md](CONTEXT.md) for the project's vocabulary and [docs/adr/](docs/adr/) for recorded design decisions. Piece icons in the browser UI are third-party artwork — see [CREDITS.md](CREDITS.md).

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

## Play in a browser

```bash
uv run hive-web
```

Then open <http://127.0.0.1:5183>. A click-to-play board: click a piece (on the board, or in a Reserve tray) to see where it can legally go, highlighted on the board, then click a highlighted Cell to make that move. Works for Placement, Movement, and a Pillbug's Throw uniformly — clicking any piece, yours or the opponent's, just shows everywhere it could legally end up this turn. `Undo` and `New game` are always available. Pieces of the same Bug Type are visually distinct (see the [piece icons](src/hive/webapp/static/pieces/)); White is an ivory tile, Black a charcoal one.

This is one `Game` per server process, for one browser tab at a time — a local pass-and-play tool, not a multi-user service.

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

### Local environment quirks

**`.env`**: if your shell sets `UV_ENV_FILE` (check `echo $UV_ENV_FILE`, or look for it in `~/.zshrc`/`~/.bash_profile`), `uv run` requires that file to exist in every project. This repo ships a `.env` (gitignored — it's a local convenience, not project config) containing `PYTHONPATH=src` so `uv run` doesn't error. If you don't use `UV_ENV_FILE`, this file is inert and you can ignore it.

**`.pth` editable installs**: in at least one sandboxed execution environment this project was developed in, Python's `.pth`-based editable install mechanism silently doesn't run (confirmed with a fresh, unrelated `uv venv` too, so it isn't specific to this project). `uv run pytest` isn't affected — `pyproject.toml` sets `pythonpath = ["src"]`, which is pytest's own mechanism, independent of `.pth` processing. If `uv run hive-play`, `uv run hive-demo`, or `uv run hive-web` fails with `ModuleNotFoundError: No module named 'hive'`, the `.env` above already sets `PYTHONPATH=src` and should cover it; if you've deleted `.env`, prefix the command with `PYTHONPATH=src` directly.

If your terminal hits neither of these, both sections are inert.
