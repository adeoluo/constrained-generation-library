<h1 align="center">Constrained Generation Library</h1>

<p align="center">
  <em>A structured-generation library built from scratch in pure Python. It compiles a JSON Schema into a finite automaton and masks a model's tokens so the output can only be valid. 100% valid JSON, by construction.</em>
</p>

<p align="center">
  <a href="https://github.com/adeoluo/constrained-generation-library/actions/workflows/ci.yml"><img alt="Continuous integration" src="https://github.com/adeoluo/constrained-generation-library/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Coverage" src="https://img.shields.io/badge/coverage-91%25-brightgreen">
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%20%7C%203.12-blue">
  <img alt="Type checked" src="https://img.shields.io/badge/mypy-strict-blue">
  <img alt="Runtime dependencies" src="https://img.shields.io/badge/runtime%20deps-0-brightgreen">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
</p>

---

## Motivation

Getting a language model to emit valid structured output (JSON matching a schema, a value from an
enum, a well-formed number) is usually attempted with prompting and retries, which fails
unpredictably. The reliable approach is to **constrain decoding**: at each step, only allow tokens
that keep the output on a path to a valid document. This library implements that from scratch. It
compiles a schema into a regular expression, compiles the expression into a finite automaton, and
uses the automaton to mask the model's vocabulary so **invalid output is impossible**, with **zero
runtime dependencies**.

The guarantee is not probabilistic. Across any model, constrained decoding here produces valid
JSON **100% of the time**; the same models unconstrained produce it **0% of the time**.

## Architecture

<p align="center">
  <img src="docs/architecture/architecture.svg" alt="System architecture" width="900">
</p>

A schema becomes a regular expression, which is parsed into a Thompson NFA and run as a lazy DFA
(each state is an epsilon-closed set of NFA states, transitions computed on demand). During
decoding, the automaton reports which tokens keep the output acceptable; the model's scores are
masked to that set. See the [ADRs](docs/adr/) for the key decisions.

## What it implements

- **A regular-expression engine** from scratch: parser, Thompson NFA construction, and a lazy DFA
  with literals, classes, the wildcard, escapes, ``* + ?``, alternation, and grouping.
- **A JSON Schema compiler** for objects with ordered typed properties (string, integer, number,
  boolean, enum), producing a regular expression for compact JSON that respects the JSON number
  grammar (no leading zeros).
- **Token-level masking**: a token is allowed only if feeding its characters never drives the
  automaton into a dead state; an end-of-sequence token is allowed only in an accepting state.
- **Constrained decoding** that masks any model's scores to the allowed set.

## Results

> Reproduce with `python -m constrained_generation_library report`. Each trial draws a different
> random model and generates a document with and without the constraint.

| Metric (200 random models) | Value |
|---|---:|
| **constrained outputs that are valid JSON** | **100% (200/200)** |
| unconstrained outputs that are valid JSON | 0% (0/200) |
| mean fraction of the vocabulary allowed per step | 0.168 |

Constrained decoding is valid **every time**; the same models, unconstrained, are valid **never**.
On average the automaton prunes about **83% of the vocabulary at each step**, which is exactly the
mask that keeps generation on a legal path.

## Demonstration

```text
$ python -m constrained_generation_library pattern
\{"name":"([^"])?...","age":-?(0|[1-9]\d?\d?),"active":(true|false),"role":("admin"|"user"|"guest")\}

$ python -m constrained_generation_library generate --seed 7
generated: {"name":",9GajsaR","age":0,"active":true,"role":"user"}
valid:     True
```

The generated document parses as real JSON and matches the schema, even though the underlying
"model" is assigning random scores to tokens.

## Quickstart

```bash
git clone https://github.com/adeoluo/constrained-generation-library.git && cd constrained-generation-library
make setup                      # install dev tooling + pre-commit hooks
make all                        # lint + type-check + test

python -m constrained_generation_library report      # validity with and without the constraint
python -m constrained_generation_library generate     # one schema-valid document
python -m constrained_generation_library pattern       # the compiled regular expression
python -m constrained_generation_library serve         # start the HTTP service on :8000
```

```python
from constrained_generation_library import (
    Property,
    compile_schema,
    constrained_generate,
    default_vocab,
    random_model,
)

schema = [Property("name", "string", max_length=10), Property("age", "integer", max_length=3)]
regex = compile_schema(schema)
result = constrained_generate(regex, default_vocab(), random_model(0))
assert regex.fullmatch(result.text)
```

## HTTP service

A standard-library HTTP service compiles the schema at startup, then validates and generates. The
routing logic is a pure function, tested without a socket.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | liveness and the active schema pattern |
| GET | `/ready` | readiness once the schema is compiled |
| GET | `/metrics` | per-route request, error, and latency metrics (Prometheus text) |
| POST | `/validate` | body `{"text": str}`; whether the text matches the schema |
| POST | `/generate` | body `{"seed": int?}`; a schema-valid document from a seeded model |
| GET | `/report` | validity rate with and without the constraint over random models |

## Design decisions

- **A lazy DFA over NFA state sets** - computing transitions on demand avoids enumerating the
  alphabet and is exactly what token masking needs. See [ADR 0002](docs/adr/0002-lazy-dfa.md).
- **Bounded schema fields** - bounding string length and integer digits keeps the automaton finite
  and guarantees that decoding completes, so validity is about complete documents, not just
  prefixes. See [ADR 0003](docs/adr/0003-bounded-fields.md).

## Evaluation

Schemas, models, and generations are deterministic, so every number reproduces offline. Full
method and tables: [`docs/EVALUATION_REPORT.md`](docs/EVALUATION_REPORT.md).

## Responsible AI

- **Model card:** [`docs/MODEL_CARD.md`](docs/MODEL_CARD.md)
- **Data card:** [`docs/DATA_CARD.md`](docs/DATA_CARD.md)
- **Threat model:** [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md)

## Limitations

- There is no language model here; a deterministic fake model stands in so the constraint can be
  demonstrated offline. The library is the masking machinery a real decoder would call.
- The regular-expression engine supports a practical subset, not the full syntax (no backreferences
  or ``{n,m}`` counts); bounded repetition is expressed by expansion.
- The JSON Schema compiler covers flat objects with the listed scalar types, not nested objects or
  arrays.

## Roadmap

- [ ] Support nested objects and arrays in the schema compiler.
- [ ] Add a context-free grammar front end for non-regular structure.
- [ ] Cache token masks per automaton state for faster decoding.

## License

[MIT](LICENSE)
