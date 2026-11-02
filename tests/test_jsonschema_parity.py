"""Independent differential validation against the ``jsonschema`` library.

The library compiles a small schema into a finite automaton and masks tokens so
output is valid by construction. This test checks that guarantee against an
*independent* oracle - the standard ``jsonschema`` validator - rather than only
against the library's own regex:

1. **Constrained outputs validate.** For a battery of varied schemas and random
   models, every constrained generation is parsed as JSON and validated against
   the equivalent real JSON Schema. If the automaton agreed only with itself a
   bug could pass unnoticed; agreeing with ``jsonschema`` shows the compiled
   grammar matches a standard validator's notion of the schema.
2. **The automaton accepts exactly what jsonschema accepts.** On a battery of
   positive and negative canonical-JSON examples, the compiled regex's
   ``fullmatch`` decision agrees document-for-document with ``jsonschema``.

``jsonschema`` is an optional ``validation`` dependency, not a runtime
dependency, so this test is skipped when it is not installed; the core
library does not require it.
"""

from __future__ import annotations

import json
import random
from typing import Any

import pytest

pytest.importorskip("jsonschema")

import jsonschema

from constrained_generation_library.constrainer import constrained_generate
from constrained_generation_library.data import default_vocab, random_model
from constrained_generation_library.schema import Property, compile_schema


def to_json_schema(properties: list[Property]) -> dict[str, Any]:
    """Return the Draft 2020-12 JSON Schema equivalent to ``properties``.

    The bounds mirror the regular-expression value grammar exactly: a bounded
    run of non-quote characters becomes ``maxLength``; an integer with up to
    ``max_length`` digits becomes a symmetric ``minimum``/``maximum``; an enum
    becomes a string ``enum``. ``additionalProperties`` is false and every key is
    required, matching the closed, ordered object the automaton accepts.
    """

    props: dict[str, Any] = {}
    required: list[str] = []
    for prop in properties:
        required.append(prop.name)
        if prop.type == "string":
            props[prop.name] = {"type": "string", "maxLength": prop.max_length}
        elif prop.type == "integer":
            bound = 10**prop.max_length - 1
            props[prop.name] = {"type": "integer", "minimum": -bound, "maximum": bound}
        elif prop.type == "number":
            props[prop.name] = {"type": "number"}
        elif prop.type == "boolean":
            props[prop.name] = {"type": "boolean"}
        elif prop.type == "enum":
            props[prop.name] = {"type": "string", "enum": list(prop.values)}
        else:  # pragma: no cover - defensive, unsupported types raise earlier
            raise ValueError(f"unsupported type: {prop.type!r}")
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": props,
        "required": required,
        "additionalProperties": False,
    }


def _schema_battery() -> list[list[Property]]:
    return [
        [
            Property("name", "string", max_length=8),
            Property("age", "integer", max_length=3),
            Property("active", "boolean"),
            Property("role", "enum", ("admin", "user", "guest")),
        ],
        [
            Property("id", "integer", max_length=4),
            Property("score", "number", max_length=3),
        ],
        [Property("label", "enum", ("red", "green", "blue"))],
        [
            Property("title", "string", max_length=12),
            Property("ok", "boolean"),
            Property("count", "integer", max_length=2),
        ],
        [Property("note", "string", max_length=5)],
        [],
    ]


def test_every_constrained_output_validates_against_jsonschema() -> None:
    """Direction 1: constrained generations validate against the real schema."""

    vocab = default_vocab()
    total = 0
    valid = 0
    for properties in _schema_battery():
        regex = compile_schema(properties)
        validator = jsonschema.Draft202012Validator(to_json_schema(properties))
        for seed in range(40):
            result = constrained_generate(regex, vocab, random_model(seed), max_tokens=160)
            # The automaton already guarantees its own regex matches.
            assert regex.fullmatch(result.text), result.text
            document = json.loads(result.text)
            total += 1
            if validator.is_valid(document):
                valid += 1
    assert total > 0
    assert valid == total, f"only {valid}/{total} constrained outputs validated"


def _canonical(document: dict[str, Any], properties: list[Property]) -> str:
    """Serialize ``document`` as compact JSON in the schema's key order."""

    ordered = {prop.name: document[prop.name] for prop in properties}
    return json.dumps(ordered, ensure_ascii=False, separators=(",", ":"))


def _agreement_cases() -> list[tuple[list[Property], dict[str, Any], bool]]:
    """Positive and negative (object, should_match) cases over exact-bound types.

    Restricted to string/integer/boolean/enum so the JSON Schema bounds capture
    the regex grammar exactly and compact serialization introduces no escapes
    (strings use a quote-free, backslash-free alphabet).
    """

    schema = [
        Property("name", "string", max_length=4),
        Property("age", "integer", max_length=2),
        Property("active", "boolean"),
        Property("role", "enum", ("admin", "user")),
    ]
    cases: list[tuple[list[Property], dict[str, Any], bool]] = [
        # Valid documents.
        (schema, {"name": "ada", "age": 42, "active": True, "role": "user"}, True),
        (schema, {"name": "", "age": 0, "active": False, "role": "admin"}, True),
        (schema, {"name": "abcd", "age": -99, "active": True, "role": "admin"}, True),
        # String too long (maxLength 4).
        (schema, {"name": "abcde", "age": 1, "active": True, "role": "user"}, False),
        # Integer out of the two-digit magnitude bound.
        (schema, {"name": "ab", "age": 100, "active": True, "role": "user"}, False),
        (schema, {"name": "ab", "age": -100, "active": True, "role": "user"}, False),
        # Value not in the enum.
        (schema, {"name": "ab", "age": 7, "active": True, "role": "root"}, False),
        # Wrong scalar type for a boolean field.
        (schema, {"name": "ab", "age": 7, "active": "yes", "role": "user"}, False),
    ]
    return cases


def test_automaton_agrees_with_jsonschema_on_examples() -> None:
    """Direction 2: fullmatch agrees with jsonschema document-for-document."""

    for properties, document, _ in _agreement_cases():
        regex = compile_schema(properties)
        validator = jsonschema.Draft202012Validator(to_json_schema(properties))
        serialized = _canonical(document, properties)
        regex_accepts = bool(regex.fullmatch(serialized))
        schema_accepts = validator.is_valid(document)
        assert regex_accepts == schema_accepts, (
            f"disagreement on {serialized!r}: regex={regex_accepts} jsonschema={schema_accepts}"
        )


def test_randomized_agreement_with_jsonschema() -> None:
    """Randomized battery: the regex and jsonschema never disagree."""

    schema = [
        Property("name", "string", max_length=3),
        Property("age", "integer", max_length=2),
        Property("active", "boolean"),
        Property("role", "enum", ("admin", "user", "guest")),
    ]
    regex = compile_schema(schema)
    validator = jsonschema.Draft202012Validator(to_json_schema(schema))
    rng = random.Random(1234)
    alphabet = "abcDE_ 09"  # quote-free, backslash-free: no JSON escaping
    disagreements = 0
    checked = 0
    for _ in range(2000):
        document = {
            "name": "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 5))),
            "age": rng.randint(-150, 150),
            "active": rng.choice([True, False]),
            "role": rng.choice(["admin", "user", "guest", "root", "USER", ""]),
        }
        serialized = _canonical(document, schema)
        checked += 1
        if bool(regex.fullmatch(serialized)) != validator.is_valid(document):
            disagreements += 1
    assert checked == 2000
    assert disagreements == 0, f"{disagreements} regex/jsonschema disagreements"
