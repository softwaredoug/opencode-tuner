# rel-optimization

Use `opencode` to optimize search relevance in a kind of autoresearch way
on the Wayfair WANDS dataset by experimenting with
ranking strategies built on top of `searcharray` BM25 indices.

This repo is a small, runnable harness that loads a custom `NewSearch` class,
evaluates it on a training/validation split, and records experiments that beat
the current validation best.

## Requirements

- Python 3.12+
- `uv` for dependency management

## Setup

```bash
uv sync
```

## Run an experiment

### With opencode (primary harness)

Optimization runs are intended to be driven by `opencode`, which limits edits
to `rel_optimization/`, runs the validation guardrails, and iterates to improve
search relevance.

```bash
OPENCODE_OPTIIMZATION=1 opencode
```

When prompted, tell it to run the instructions in `rel_optimization/prompt.md`.

### Manually

Create a strategy module that exports `NewSearch` (see `rel_optimization/exp0_baseline.py`
or `rel_optimization/new_strategy.py` for a starting point), then run:

```bash
uv run python main.py \
  --experiment-description "BM25 baseline" \
  --test-module "rel_optimization/exp0_baseline.py"
```

The runner will:

- load your `NewSearch` class
- compute NDCG on a training sample and validation holdout
- reject runs that do not beat the current validation SOTA
- append successful results to `rel_optimization/experiments.csv`

## Create a new strategy

1. Add a new file under `rel_optimization/` (one file per experiment).
2. Define a `NewSearch` class with a `search(self, query, k=10)` method.
3. Use the existing experiments as references for tokenization, field boosts,
   and feature ideas.

## Tests

```bash
uv run pytest
```

## Project layout

- `main.py`: experiment runner and logging
- `rel_optimization/`: strategies and experiment modules
- `rel_optimization/experiments.csv`: experiment log
- `tests/`: basic guard tests for the CLI
