# Agent Implementation Roadmap

Plan for the self-play-trained agent described in [CONTEXT.md](../CONTEXT.md) and flagged as "not built yet" in [CLAUDE.md](../CLAUDE.md). Approach: AlphaZero-style — a policy+value network guided by MCTS, trained via self-play — not the genetic algorithm originally proposed (see conversation history for why).

Two open design questions from earlier discussion that Phase 0 needs to settle concretely before any code lands:

1. **Board window size** — the fixed egocentric hex-radius the state encoding crops to. Too small clips real positions; too large wastes network capacity on empty cells.
2. **Action factorization** — piece × direction (6 directions + climb), reusing the shape of this project's own Move Notation. Needs a concrete indexing scheme (which piece slots, how Throw is represented) before `action_space.py` can be written.

Both are prototype decisions best settled by looking at real game-length/spread statistics from `hive-demo`'s random self-play data, not guessed in the abstract.

## Phased roadmap

### Phase 0 — Encoding & action space
- `encoding.py`: `GameState` → fixed-size feature-plane tensor (one plane per (Color, Bug Type) occupancy, plus scalar planes for whose turn, each side's Queen-placed flag, turn count).
- `action_space.py`: the piece × direction factorization; masks a raw policy output down to whatever `Game.legal_moves()` actually allows this turn.
- Tests: encode → decode round-trips; every legal `Move` maps to exactly one action index and back.

### Phase 1 — Network, inference only
- `network.py`: small CNN or MLP over the windowed board, policy head + value head. No training loop yet.
- Sanity check: a randomly-initialized network runs on a real `GameState`, output shapes are right, and the policy is correctly zero-masked to legal moves only.
- Wire up MLflow (local file store) now, even with nothing to train — logging becomes a habit from the first real run instead of retrofitted later.

### Phase 2 — MCTS
- `mcts.py`: PUCT-style search built directly on `Game.apply_move()` / `Game.undo_move()` — the make/unmake architecture this engine already has is exactly what MCTS wants; no state-copying needed per simulation.
- Milestone: MCTS guided by an *untrained* (random-weight) network should already beat `hive-demo`'s pure-random player consistently. If it doesn't, the search or masking has a bug worth finding before training ever enters the picture.

### Phase 3 — Self-play data generation
- `selfplay.py`: play N games with the current network+MCTS on both sides; record `(state, MCTS visit-count policy, final outcome)` per position.
- `replay_buffer.py`: store these. A SQLite-backed buffer is a legitimate use of the SQL option flagged back in the original project brief — unlike the engine's own game state (deliberately kept SQL-free per [ADR-0001](adr/0001-separate-inconclusive-outcome-from-draw.md)'s spirit), training data is exactly the kind of growing, queryable dataset SQL is good for.

### Phase 4 — Training step
- `train.py`: sample the replay buffer, one gradient step (policy cross-entropy + value MSE, standard AlphaZero loss), log loss curves to MLflow, checkpoint weights as an MLflow artifact.

### Phase 5 — Evaluation / gating
- `evaluate.py`: candidate checkpoint plays a match against the current best checkpoint and against the random baseline. Only promote to "best" on a clear win-rate margin — prevents a noisy training step from silently regressing the agent.

### Phase 6 — Orchestration
- `orchestrate.py`: self-play → train → evaluate → promote → repeat, as one loop with configurable iteration counts.
- Start deliberately small (few self-play games per iteration, low MCTS simulation count, small network) to validate the *full pipeline* end-to-end on laptop-scale compute before scaling anything up. A working small loop beats a large one that's never finished an iteration.

### Phase 7 — Stretch
- Parallelize self-play (stdlib `multiprocessing` first; only reach for Ray/Dask if that's a genuine bottleneck).
- Hyperparameter sweeps as separate MLflow runs (network size, MCTS simulation count, learning rate).
- Opponent pool diversity (keep a few past checkpoints around as sparring partners, not just "current best"), if self-play against only the latest checkpoint starts cycling.

## Folder structure

```
src/hive/
  agent/
    __init__.py
    config.py           # hyperparameters as plain dataclasses — no config framework yet
    encoding.py          # GameState -> bounded egocentric feature-plane tensor
    action_space.py      # factored (piece, direction) action indexing + legal-move masking
    network.py            # policy+value architecture, forward pass only
    mcts.py                # PUCT search on Game's make/unmake API
    selfplay.py             # self-play games -> (state, policy, outcome) samples
    replay_buffer.py       # stores/samples self-play data (SQLite-backed)
    train.py                 # one training step: sample, gradient update, log, checkpoint
    evaluate.py              # candidate vs. best-so-far / random baseline
    orchestrate.py            # the outer self-play -> train -> evaluate -> promote loop
checkpoints/    # gitignored — saved network weights per generation
mlruns/          # gitignored — local MLflow tracking store
tests/
  test_agent_encoding.py
  test_agent_action_space.py
  test_agent_mcts.py    # e.g. MCTS + random weights reliably beats pure-random play
```

Add a `hive-train` (or similar) entry point in `pyproject.toml` alongside the existing `hive-play`/`hive-demo`/`hive-web`, once `orchestrate.py` exists.

## Packages

Base engine/UI (`uv sync`) stays exactly as it is — no ML dependency should be required just to play a game or run the demo. Everything below goes behind a new `agent` optional-dependency group (`uv sync --extra agent`).

### Option A — DeepMind's own stack (if that's literally what you meant)

- `jax` — array/autodiff backend
- `dm-haiku` or `flax` — network definition (Haiku is closer to DeepMind's own historical AlphaZero-style code; Flax is more actively developed today)
- `optax` — DeepMind's optimizer library, pairs with either
- `mctx` — DeepMind's own JAX-native MCTS library; this is the one that most directly matches "AlphaZero-style search," and would let `mcts.py` be a thin wrapper rather than a from-scratch implementation
- `chex` (optional) — DeepMind's testing/assertion helpers for JAX code

### Option B — Framework-agnostic (simpler, more common default)

- `torch` — network + autodiff (solid Apple Silicon MPS backend, relevant given local hardware)
- `numpy` — feature-plane construction, general array prep

### Shared regardless of A vs. B

- `mlflow` — experiment tracking (local file store — see the earlier discussion on why not to spawn a server)
- `tqdm` — progress bars for self-play/training loops

### Deliberately not adding yet

- **Ray / Dask** — self-play parallelizes fine with stdlib `multiprocessing` at prototype scale; reach for a real distributed framework only once that's a measured bottleneck.
- **Pydantic / Hydra** — plain dataclasses in `config.py` until config validation or sweeps genuinely need more.
- **PyTorch Lightning / similar** — a raw training loop is small enough at this scale that a framework would add more ceremony than it saves.

This mirrors the same discipline the engine itself was built with: no dependency earns a place until the phase that actually needs it arrives.
