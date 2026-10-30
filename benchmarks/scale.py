"""A large-workload scaling benchmark for constrained generation.

Compiles schemas of increasing size and runs many constrained generations,
reporting wall-clock time, generation throughput, and the fraction of outputs
that are valid JSON by construction, plus a one-off peak-memory measurement. This
is a pure-Python decoder, so the throughput measures how the masking machinery
scales, not competitive speed against a production constrained-decoding
framework. Deterministic and offline; run with:

    uv run python benchmarks/scale.py
"""

from __future__ import annotations

import time
import tracemalloc

from constrained_generation_library.constrainer import constrained_generate
from constrained_generation_library.data import default_vocab, random_model
from constrained_generation_library.schema import Property, compile_schema

_TYPES = ("string", "integer", "boolean", "enum")


def _schema(n_properties: int) -> list[Property]:
    properties: list[Property] = []
    for index in range(n_properties):
        kind = _TYPES[index % len(_TYPES)]
        values = ("red", "green", "blue") if kind == "enum" else ()
        properties.append(Property(name=f"field{index}", type=kind, values=values))
    return properties


def main() -> None:
    vocab = default_vocab()
    print(
        "Constrained generation at scale (pure-Python masking; throughput measures "
        "scaling, not competitive speed against a production framework):"
    )
    for n_properties, trials in ((4, 60), (8, 40), (12, 30), (16, 20)):
        regex = compile_schema(_schema(n_properties))
        start = time.perf_counter()
        valid = 0
        for seed in range(trials):
            result = constrained_generate(regex, vocab, random_model(seed), max_tokens=400)
            if regex.fullmatch(result.text):
                valid += 1
        elapsed = time.perf_counter() - start
        throughput = trials / elapsed if elapsed else 0.0
        print(
            f"  {n_properties:>2} fields x {trials:>3} generations: {elapsed:6.2f}s "
            f"({throughput:6.1f} gen/sec), valid JSON {valid}/{trials}"
        )

    # Measure peak memory once (tracemalloc adds too much overhead for the timed loop).
    regex = compile_schema(_schema(16))
    tracemalloc.start()
    constrained_generate(regex, vocab, random_model(0), max_tokens=400)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"  peak memory for one 16-field generation: {peak / 1024:.0f} KiB")


if __name__ == "__main__":
    main()
