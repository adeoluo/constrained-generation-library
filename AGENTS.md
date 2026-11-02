# AGENTS.md

Working notes for coding agents and contributors in **Constrained Generation Library**. The [README](README.md)
explains what the project does and why; this file explains how to change it safely.

## Project

A structured-generation library built from scratch in Python that compiles a JSON Schema into a finite automaton and masks a model's tokens so the output is schema-valid by construction.

## Layout

- `benchmarks/`: benchmark scripts and recorded results
- `docker-compose.yml`: local container setup
- `docs/`: documentation, architecture diagram source and render, design records
- `src/`: library and service source
- `tests/`: test suite

Key modules:

- `src/constrained_generation_library/__init__.py`: Constrained Generation Library - schema-constrained decoding from scratch.
- `src/constrained_generation_library/cli.py`: Command line interface for the constrained generation library.
- `src/constrained_generation_library/constrainer.py`: Token-level constraint masking and constrained decoding.
- `src/constrained_generation_library/data.py`: A token vocabulary and deterministic fake models for demonstration.
- `src/constrained_generation_library/evaluation.py`: Evaluation: validity rate with and without the constraint, and selectivity.
- `src/constrained_generation_library/observability.py`: In-process request metrics for the HTTP service (Prometheus text exposition).
- `src/constrained_generation_library/regex.py`: A small regular-expression engine: parse to an NFA, then run a lazy DFA.
- `src/constrained_generation_library/schema.py`: Compile a small JSON Schema into a regular expression for compact JSON.
- `src/constrained_generation_library/service.py`: A standard-library HTTP service for schema-constrained generation.

## Commands

| Command | Purpose |
|---|---|
| `make help` | Show this help |
| `make setup` | Install dependencies and pre-commit hooks |
| `make format` | Format automatically |
| `make lint` | Lint (no fixes) |
| `make type` | Type-check |
| `make test` | Run tests |
| `make coverage` | Tests with coverage gate |
| `make evaluation` | Reproduce the results table |
| `make run` | Run the HTTP service |
| `make diagram` | Render architecture diagram to SVG |
| `make docker-build` | Build the image |
| `make docker-up` | Run via docker compose |
| `make clean` | Remove caches and artifacts |
| `make all` | Full local gate (mirror of continuous integration) |
| `make changelog` | Regenerate CHANGELOG.md from Conventional Commits (git-cliff) |
| `make cut-release` | Cut a release locally: version bump, changelog, tag, GitHub release (RELEASE_VERSION=vX.Y.Z optional) |

Run the full local gate (`make all`) before committing; CI runs the same checks.

## Conventions

- Commits follow Conventional Commits (`feat:`, `fix:`, `perf:`, `refactor:`, `docs:`, `test:`, `ci:`, `chore:`).
  The changelog and the next version number are derived from them.
- Every number quoted in the README is produced by a command in this repository. When behavior
  changes, rerun that command and update the number in the same commit.
- When a component is added, removed or renamed, update `docs/architecture/architecture.mmd`
  and re-render `architecture.svg` so the diagram matches the code.
- README sections keep their fixed order. Prose avoids em and en dashes and promotional wording.
- Tests accompany behavior changes; a bug fix comes with a test that fails without it.
- Releases are cut by the maintainer with `make cut-release`, never from CI.

## Python notes

- Python is managed with `uv`; run commands through `uv run` so the locked environment is used.
- Lint and format with `ruff`; type-check with `mypy`; tests use `pytest`.
- Public functions carry type hints and a docstring that states the contract, not the steps.
