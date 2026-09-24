# CLAUDE.md

Hive board-game engine (base game + Mosquito/Ladybug/Pillbug), future environment for a self-play GANN. Rules engine plus a terminal UI and a browser UI — no ML yet.

Vocabulary: [CONTEXT.md](CONTEXT.md). Recorded decisions: [docs/adr/](docs/adr/). Read both before changing behavior that touches either.

## Commands

`uv run pytest` / `uv run ruff check .` / `uv run ruff format .`

If `uv run hive-play`, `uv run hive-demo`, or `uv run hive-web` raises `ModuleNotFoundError: No module named 'hive'`, prefix `PYTHONPATH=src`. This sandbox's Python silently skips `.pth`-based editable installs (confirmed with a throwaway `uv venv` unrelated to this project, so it's environmental, not a project bug). Pytest is unaffected — `pyproject.toml`'s `pythonpath = ["src"]` sidesteps it already.

If `uv run` instead errors `No environment file found at: '.env'`, the user's shell exports `UV_ENV_FILE=.env` globally (their own `~/.zshrc` convention, unrelated to this project). The repo's gitignored `.env` (containing `PYTHONPATH=src`, so it also covers the line above) satisfies that — if it's missing, recreate it rather than touching their shell config.

## Geometry

Axial `(q, r)`, pointy-top. Six `Direction`s in `coordinates.py`; each has an `.offset` and an `.opposite`. `AxialCoordinate.neighbors()`/`.neighbor_set()` and `common_neighbors()` are `@cache`d — they're pure and get called millions of times per game (a 200-move game went 2.2s → 0.2s from this alone). Don't strip the cache without re-profiling.

## The lift-before-check pattern

Every movement/gate/contact/connectivity check in `rules.py` and `board.py` assumes the mover is already off the board. `rules._Lifted` is a context manager for this: it removes the piece from its origin Cell on `__enter__`, restores it on `__exit__`. Any new movement-pattern function needs this same wrapper — checking gate/contact/connectivity against a board that still has the mover sitting at its origin gives wrong answers (the mover blocks its own escape route).

## Module map

`coordinates.py` cells/directions · `pieces.py` Color/BugType/Piece · `board.py` Stack-based Board, One Hive cut-vertex check, Freedom to Move gate formula · `moves.py` the four Move dataclasses · `rules.py` per-Bug-Type movement, Throw, placement legality (pure Board queries, no mutation) · `state.py` mutable GameState (Reserves, turn order, last_moved_piece) · `game.py` the public API: `legal_moves()` / `apply_move()` / `undo_move()` / `result()` · `notation.py` parse/format Move Notation, resolved against `Game.legal_moves()` rather than re-deriving legality · `cli.py` / `demo.py` the two non-browser entry points · `webapp/server.py` the Flask JSON API (one `Game` singleton in server memory) + `webapp/static/` (`index.html`/`style.css`/`app.js`, third-party piece icons under `static/pieces/` — see [CREDITS.md](../CREDITS.md), most CC0 but the Pillbug's is CC BY 3.0 and requires attribution).

### The web UI's move-resolution pattern

Every API endpoint that changes state (`/api/move`) resolves its input against `game.legal_moves()` — same pattern as `notation.parse_move`, and for the same reason: Movement and Throw share a shape (a piece code + a destination Cell), so matching by `(piece.code, destination)` transparently returns whichever is actually legal without the frontend or the API layer needing to know which. `server._reserve_summary`'s `code` field must be the exact next-numbered Piece Code `Game.legal_moves()` would offer (via `state.peek_from_reserve`) — building it as `f"{color}{bug_type}"` without the number silently breaks every multi-count Bug Type's reserve click (shipped once; `tests/test_webapp.py`'s `test_reserve_codes_match...` pins it down now).

## Testing hex geometry

Hand arithmetic on multi-step axial paths (Spider, Ladybug, Ant) is error-prone enough that it isn't trustworthy alone. Before locking in an assertion for one of these, build the scenario and print `rules.movement_destinations(...)` interactively (`PYTHONPATH=src uv run python3 -c "..."`), cross-check the result against independent reasoning, *then* write the test. Existing tests in `tests/test_spider.py` etc. were built this way — follow the same discipline for new multi-step scenarios rather than trusting hand-derived coordinates directly.

## Not built yet

No Gym/Gymnasium-style RL API (deliberate — see CONTEXT.md's Special Ability/API surface decisions), no persistence/SQLite, no ML/training code, no automatic detection of the rulebook's forced-repetition Draw (documented as a known open edge case in CONTEXT.md's `Draw` entry). Don't assume any of these exist; don't add them without the user asking. When that work starts, [docs/agent-roadmap.md](docs/agent-roadmap.md) has the plan — a common `Agent` interface so multiple implementations (AlphaZero-style, a GenAI-based one, etc.) stay swappable and comparable via one shared arena, the `src/hive/agents/` folder structure, and per-track package lists (kept behind optional-dependency groups so the base engine/UI install stays ML-free).
