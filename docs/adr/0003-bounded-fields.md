# ADR-0003: Bounded schema fields so decoding completes

- **Status:** Accepted
- **Date:** 2026-01-01

## Context
A constraint guarantees that a generated prefix is always extendable to a valid document, but it
cannot force a model to finish an open-ended field. With an unbounded string or integer, a model
that keeps choosing to extend the field never closes it, so a valid complete document is not
guaranteed within a token budget.

## Decision
Bound the open-ended fields: strings have a maximum length and integers a maximum number of
digits, expressed by expanding into optional repetitions. This keeps the automaton finite and
guarantees that every path reaches an accepting state within a bounded number of tokens.

## Consequences
- Validity is about complete documents, not just prefixes: constrained decoding produces a finished
  valid document regardless of the model.
- The regular-expression engine needs no ``{n,m}`` counting syntax; bounded repetition is built
  from the ``?`` quantifier.
- Very long field values are not representable; the bound is a schema parameter the caller sets.
