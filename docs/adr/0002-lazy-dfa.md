# ADR-0002: A lazy DFA over NFA state sets

- **Status:** Accepted
- **Date:** 2026-01-01

## Context
Token masking asks, for the current automaton state and a candidate token, whether consuming the
token's characters can still reach an accepting state. This needs fast character transitions. A
fully materialized DFA would require enumerating the alphabet and could be large; a plain NFA
simulation repeats epsilon-closure work.

## Decision
Parse the pattern into a Thompson NFA, then run it as a lazy DFA: a DFA state is the epsilon-closed
set of NFA states, and transitions are computed on demand for the specific characters that appear
in tokens. Epsilon closures are memoized.

## Consequences
- Transitions are only ever computed for characters that occur, so the alphabet is never
  enumerated, which matters for byte-like vocabularies.
- The same automaton answers both validation (does a string match) and masking (which tokens keep
  the state alive), so there is one code path to trust.
- Worst-case state blow-up is possible for pathological patterns, but the schemas this library
  compiles stay small.
