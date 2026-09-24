# Agent Implementation Roadmap

Plan for the self-play-trained agent described in [CONTEXT.md](../CONTEXT.md) and flagged as "not built yet" in [CLAUDE.md](../CLAUDE.md). First implementation: AlphaZero-style — a policy+value network guided by MCTS, trained via self-play — not the genetic algorithm originally proposed (see conversation history for why). It will not be the only one: the intent is to try other agents later, possibly including a GenAI/LLM-based one, so the structure below is built around a common `Agent` interface rather than one hard-coded implementation.

## Design principle: multiple, swappable agents

Every agent implementation — AlphaZero-style, a GenAI-based one, a future genetic algorithm, even the existing random player from `hive-demo` — satisfies the same interface:

```python
class Agent(Protocol):
    def choose_move(self, game: Game) -> Move: ...
```

Given a `Game`, return one of `game.legal_moves()`. Nothing about *how* that decision is made is visible outside the agent's own package: an AlphaZero agent runs MCTS over tensor-encoded states, a GenAI agent serializes the position to text and parses a move back out of a completion, a random agent just calls `random.choice()`. This is the same shape `notation.parse_move` and the web UI's `/api/move` already use internally (resolve against `game.legal_moves()` rather than re-deriving legality), just pushed up to the agent level.

Two things fall out of this for free:

- **A shared arena.** One tournament/evaluation harness plays *any* two agents against each other and reports results — that's how you'd actually compare AlphaZero-so-far against a GenAI agent, not just against a fixed baseline. Evaluation stops being AlphaZero-specific.
- **`hive-demo`'s random player becomes just another `Agent`.** Worth unifying when the first real implementation lands (`agents/random_agent.py` wrapping the existing `rng.choice(game.legal_moves())` logic, with `demo.py` calling it), rather than duplicating the same pattern twice.

Each implementation encodes the game its own way — an AlphaZero agent needs the tensor/action-space encoding described below; a GenAI agent needs a text encoding instead (this project's own Move Notation is a natural fit, since it's already a compact, human/LLM-readable text format — see [CONTEXT.md](../CONTEXT.md#notation)). Encoding strategy is therefore per-agent, not a shared module every implementation is forced through.

Two open design questions the AlphaZero track's Phase 0 needs to settle concretely before any code lands there:

1. **Board window size** — the fixed egocentric hex-radius the state encoding crops to. Too small clips real positions; too large wastes network capacity on empty cells.
2. **Action factorization** — piece × direction (6 directions + climb), reusing the shape of this project's own Move Notation. Needs a concrete indexing scheme (which piece slots, how Throw is represented) before `action_space.py` can be written.

Both are prototype decisions best settled by looking at real game-length/spread statistics from `hive-demo`'s random self-play data, not guessed in the abstract.

## Folder structure

```
src/hive/
  agents/
    __init__.py
    protocol.py            # the Agent interface every implementation satisfies
    arena.py                 # plays any two Agents against each other, reports results — shared across all tracks
    random_agent.py           # the existing hive-demo random player, as an Agent (unifies rather than duplicates)

    alphazero/                 # first implementation track
      __init__.py
      config.py                 # hyperparameters as plain dataclasses — no config framework yet
      encoding.py                # GameState -> bounded egocentric feature-plane tensor
      action_space.py            # factored (piece, direction) action indexing + legal-move masking
      network.py                  # policy+value architecture, forward pass only
      mcts.py                      # PUCT search on Game's make/unmake API
      selfplay.py                   # self-play games -> (state, policy, outcome) samples
      replay_buffer.py             # stores/samples self-play data (SQLite-backed)
      train.py                       # one training step: sample, gradient update, log, checkpoint
      evaluate.py                     # candidate vs. best-so-far / random baseline, via arena.py
      orchestrate.py                   # the outer self-play -> train -> evaluate -> promote loop

    genai/                      # second implementation track (see below)
      __init__.py
      prompting.py               # GameState -> prompt text (built on Move Notation)
      client.py                    # wraps whichever LLM API
      parsing.py                    # completion text -> Move, validated against game.legal_moves()

checkpoints/    # gitignored — saved AlphaZero network weights per generation
mlruns/          # gitignored — local MLflow tracking store
tests/
  test_agents_protocol.py    # any Agent, including a trivial stub, satisfies the interface
  test_agents_arena.py         # two stub agents play a full game via arena.py
  agents/
    test_alphazero_encoding.py
    test_alphazero_action_space.py
    test_alphazero_mcts.py    # e.g. MCTS + random weights reliably beats pure-random play
    test_genai_parsing.py       # malformed/illegal completions are rejected, not silently misapplied
```

Add entry points in `pyproject.toml` alongside the existing `hive-play`/`hive-demo`/`hive-web` as each track gets an orchestration script worth running directly (e.g. `hive-train-alphazero`) — and, once `arena.py` exists, something like `hive-arena` to run any two named agents against each other from the command line.

## AlphaZero track: phased roadmap

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
- Milestone: MCTS guided by an *untrained* (random-weight) network should already beat the random `Agent` consistently via `arena.py`. If it doesn't, the search or masking has a bug worth finding before training ever enters the picture.

### Phase 3 — Self-play data generation
- `selfplay.py`: play N games with the current network+MCTS on both sides; record `(state, MCTS visit-count policy, final outcome)` per position.
- `replay_buffer.py`: store these. A SQLite-backed buffer is a legitimate use of the SQL option flagged back in the original project brief — unlike the engine's own game state (deliberately kept SQL-free per [ADR-0001](adr/0001-separate-inconclusive-outcome-from-draw.md)'s spirit), training data is exactly the kind of growing, queryable dataset SQL is good for.

### Phase 4 — Training step
- `train.py`: sample the replay buffer, one gradient step (policy cross-entropy + value MSE, standard AlphaZero loss), log loss curves to MLflow, checkpoint weights as an MLflow artifact.

### Phase 5 — Evaluation / gating
- `evaluate.py`: candidate checkpoint plays a match against the current best checkpoint and against the random `Agent`, via `arena.py`. Only promote to "best" on a clear win-rate margin — prevents a noisy training step from silently regressing the agent.

### Phase 6 — Orchestration
- `orchestrate.py`: self-play → train → evaluate → promote → repeat, as one loop with configurable iteration counts.
- Start deliberately small (few self-play games per iteration, low MCTS simulation count, small network) to validate the *full pipeline* end-to-end on laptop-scale compute before scaling anything up. A working small loop beats a large one that's never finished an iteration.

### Phase 7 — Stretch
- Parallelize self-play (stdlib `multiprocessing` first; only reach for Ray/Dask if that's a genuine bottleneck).
- Hyperparameter sweeps as separate MLflow runs (network size, MCTS simulation count, learning rate).
- Opponent pool diversity (keep a few past checkpoints around as sparring partners, not just "current best"), if self-play against only the latest checkpoint starts cycling.

## GenAI track: what's different

A GenAI-based agent isn't a smaller version of the AlphaZero one — its whole shape is different, so it's its own package rather than a variant:

- **Encoding is text, not tensors.** `prompting.py` renders the board and reserve state as text (Move Notation is the natural building block, since it's already a compact way to describe a piece's position relative to the hive) plus the list of legal moves, and asks the model to pick one.
- **Output needs a validation boundary the AlphaZero track doesn't.** A neural net's policy head is masked to legal moves by construction; an LLM's text completion is not — it can hallucinate a move that's malformed or references a piece that isn't there. `parsing.py` must reject anything that doesn't resolve to a real entry in `game.legal_moves()` (reusing `notation.parse_move`'s resolution pattern) and have a defined fallback (retry with an error appended to the prompt, or fall back to a random legal move) rather than ever applying an unvalidated move.
- **Latency and cost are real constraints self-play doesn't usually have.** Thousands of self-play games the way the AlphaZero track wants aren't practical against a hosted LLM API. A GenAI agent is more likely to be evaluated in small matches (via `arena.py`, against AlphaZero checkpoints or a human) than trained via massive self-play — "training" here might mean prompt iteration, not gradient descent.
- **Determinism isn't guaranteed.** Worth logging full prompts/completions (as MLflow artifacts, same as everything else) specifically because a GenAI agent's behavior isn't reproducible from a seed the way the AlphaZero or random agents' is.

No phased build-out for this track yet — it's here so the folder structure and the `Agent` interface already have room for it when it's time, without a restructure.

## Packages

Base engine/UI (`uv sync`) stays exactly as it is — no ML or LLM dependency should be required just to play a game or run the demo. Everything below goes behind optional-dependency groups (`uv sync --extra alphazero`, `uv sync --extra genai`) so trying one track doesn't drag in the other's dependencies.

### `alphazero` extra

**Option A — DeepMind's own stack** (if that's literally what "DeepMind's infra" meant):
- `jax` — array/autodiff backend
- `dm-haiku` or `flax` — network definition (Haiku is closer to DeepMind's own historical AlphaZero-style code; Flax is more actively developed today)
- `optax` — DeepMind's optimizer library, pairs with either
- `mctx` — DeepMind's own JAX-native MCTS library; this is the one that most directly matches "AlphaZero-style search," and would let `mcts.py` be a thin wrapper rather than a from-scratch implementation
- `chex` (optional) — DeepMind's testing/assertion helpers for JAX code

**Option B — framework-agnostic** (simpler, more common default):
- `torch` — network + autodiff (solid Apple Silicon MPS backend, relevant given local hardware)
- `numpy` — feature-plane construction, general array prep

Either option: `mlflow` (experiment tracking, local file store), `tqdm` (progress bars).

### `genai` extra

- An LLM client — `anthropic` is the natural default given the rest of this workflow, but keep `client.py` thin enough that swapping providers doesn't touch `prompting.py`/`parsing.py`.
- `mlflow` again, for logging prompts/completions/match results the same way the AlphaZero track logs training runs.
- No tensor library needed at all for this track.

### Deliberately not adding yet

- **Ray / Dask** — self-play parallelizes fine with stdlib `multiprocessing` at prototype scale; reach for a real distributed framework only once that's a measured bottleneck.
- **Pydantic / Hydra** — plain dataclasses in `config.py` until config validation or sweeps genuinely need more.
- **PyTorch Lightning / similar** — a raw training loop is small enough at this scale that a framework would add more ceremony than it saves.
- **An agent-framework library** (LangChain, etc.) for the GenAI track — one prompt, one parsed response, one legality check doesn't need an orchestration framework on top of a plain LLM client call.

This mirrors the same discipline the engine itself was built with: no dependency, and no track, earns a place until the phase that actually needs it arrives.
