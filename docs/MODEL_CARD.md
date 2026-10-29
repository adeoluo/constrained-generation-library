# Model / System Card - Constrained Generation Library

## Overview
- **What it is:** a from-scratch structured-generation library that compiles a JSON Schema into a
  finite automaton and masks a model's tokens so output is schema-valid by construction. No
  third-party dependencies.
- **Base model:** none. A deterministic fake model stands in for a language model so the mechanism
  can be demonstrated offline.
- **Version and date:** 0.1.0, 2026.

## Intended use
- **Primary use case:** guaranteeing that a decoder's output matches a schema, and a readable
  reference implementation of automaton-based constrained decoding.
- **Primary users:** engineers building structured-output or tool-calling pipelines.

## Out-of-scope / prohibited use
- Not a language model; it supplies the masking machinery a real decoder would call.
- The schema compiler covers flat objects with scalar types, not arbitrary JSON Schema.

## Performance
- 100% valid JSON under the constraint across 200 random models; 0% without it.
- Full method and tables: [`EVALUATION_REPORT.md`](EVALUATION_REPORT.md).

## Limitations and failure modes
- The regular-expression engine supports a practical subset (no backreferences or counted
  repetition); bounded repetition is expanded.
- Field values are bounded in length so decoding is guaranteed to complete.

## Ethical considerations
- No personal data, no network access, no external model. Inputs are schemas and seeds.
