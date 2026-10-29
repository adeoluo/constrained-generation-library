# Threat Model - Constrained Generation Library

## Assets
- The HTTP service's availability and the integrity of its responses.

## Trust boundaries
- The only external input is the JSON body and path of a request. The schema, automaton, and model
  are in-process and trusted.

## Entry points and mitigations

### `POST /validate`
- **Malformed JSON** is rejected with 400 before routing.
- **Validation:** the text must be a string within a length bound; oversized or wrong-type input
  returns 400 with a message.

### `POST /generate`
- The seed must be a non-negative integer within a bound; booleans and out-of-range values are
  rejected explicitly. Generation is capped by a maximum token count, so a request cannot run
  unbounded.

### `GET` routes
- `/health`, `/ready`, `/report`, and `/metrics` take no user input and return fixed-shape
  payloads. `/metrics` exposes only aggregate counters.

## Non-threats (by construction)
- **No secrets:** the service holds no credentials and makes no outbound calls.
- **No persistence:** state is the in-memory compiled schema; nothing is written on the request path.
- **No code execution:** inputs are text and integers; no user-supplied string is evaluated as code,
  and user text is matched by the automaton, not by the host regular-expression engine.

## Supply chain
- Zero runtime dependencies. Development tooling is pinned via `uv.lock`. CodeQL and dependency
  scanning run in CI.

## Residual risk
- Generation is CPU-intensive; a flood of `/generate` requests could exhaust CPU. A production
  deployment would add a rate limiter behind a reverse proxy.
