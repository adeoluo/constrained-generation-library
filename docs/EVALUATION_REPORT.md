# Evaluation Report - Constrained Generation Library

> Reproduce with `python -m constrained_generation_library report` and `benchmarks/benchmark.py`.
> Schemas, models, and generations are deterministic.

## Setup

- **Schema:** an object with a bounded string (name), a bounded integer (age), a boolean (active),
  and an enum (role) over three values.
- **Models:** deterministic fake models that assign scores to vocabulary tokens; a random model
  stands in for an unconstrained model that emits arbitrary tokens.
- **Metrics:** fraction of outputs that are valid JSON with and without the constraint, and the
  mean fraction of the vocabulary the automaton allows per step (its selectivity).
- **Hardware / cost:** CPU only; a report over 200 models runs in a couple of seconds. No external
  services.

## Correctness guarantee

Across 200 random models:

| Metric | Value |
|---|---:|
| constrained outputs valid as JSON | 200/200 (100%) |
| unconstrained outputs valid as JSON | 0/200 (0%) |
| mean fraction of vocabulary allowed per step | 0.168 |

Constrained decoding is valid every time because the automaton rejects any token that would make
the document impossible to complete, and the schema's bounded fields guarantee completion. The
same models, unconstrained, never produce valid JSON, because an arbitrary token stream almost
never happens to be a legal document. The automaton prunes about 83% of the vocabulary per step,
which is the mask doing its work.

## Correctness of the pieces

- The regular-expression engine is tested on literals, character classes, negation, escapes,
  quantifiers, alternation, and grouping, and on parse errors.
- The JSON Schema compiler respects the JSON number grammar: a dedicated test confirms that leading
  zeros (for example ``02``) are rejected while ``0`` and negative integers are accepted, and that
  every constrained generation parses with the standard-library ``json`` module.
- A biased model that targets a specific document reaches it exactly under the constraint, showing
  the mask permits the intended output rather than only forbidding bad output.

## Service performance

Each `/generate` call decodes a full document token by token, recomputing the allowed set at every
step. Under a concurrent stress benchmark the handler sustains tens of requests per second with p50
near 20 ms, which reflects pure-Python masking over the vocabulary at each step.

## Reproducibility

- Deterministic given a seed: schemas, models, and generations reproduce.
- No network access, no external data.
- Regenerate every number with the CLI and `benchmarks/benchmark.py`.
