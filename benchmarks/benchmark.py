"""A deterministic micro-benchmark for schema-constrained generation.

Compiles a schema and reports the fraction of valid outputs with and without the
constraint over many random models, plus the constraint's selectivity.
Deterministic and offline; run with:

    uv run python benchmarks/benchmark.py
"""

from __future__ import annotations

import time

from constrained_generation_library.evaluation import validity_report
from constrained_generation_library.schema import Property, compile_schema, schema_to_pattern


def main() -> None:
    schema = [
        Property("name", "string", max_length=10),
        Property("age", "integer", max_length=3),
        Property("active", "boolean"),
        Property("role", "enum", ("admin", "user", "guest")),
    ]
    print(f"Pattern: {schema_to_pattern(schema)}")
    regex = compile_schema(schema)
    start = time.perf_counter()
    report = validity_report(regex, trials=200)
    elapsed = time.perf_counter() - start
    print(f"Over {report.trials} random models ({elapsed:.1f} s):")
    print(f"  constrained valid: {report.constrained_rate:.3f}")
    print(f"  unconstrained valid: {report.unconstrained_rate:.3f}")
    print(f"  mean allowed fraction of the vocabulary per step: {report.mean_allowed_fraction:.3f}")


if __name__ == "__main__":
    main()
