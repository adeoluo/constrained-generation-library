"""Tests for the regex engine, schema compilation, and constrained decoding."""

from __future__ import annotations

import json

import pytest

from constrained_generation_library.constrainer import (
    Constraint,
    constrained_generate,
    unconstrained_generate,
)
from constrained_generation_library.data import biased_model, default_vocab, random_model
from constrained_generation_library.evaluation import validity_report
from constrained_generation_library.regex import Regex, RegexParseError
from constrained_generation_library.schema import Property, compile_schema, schema_to_pattern


def test_regex_literals_and_classes() -> None:
    assert Regex("abc").fullmatch("abc")
    assert not Regex("abc").fullmatch("abd")
    assert Regex(r"a[0-9]+b").fullmatch("a123b")
    assert not Regex(r"a[0-9]+b").fullmatch("ab")


def test_regex_alternation_and_quantifiers() -> None:
    assert Regex("(cat|dog)").fullmatch("dog")
    assert not Regex("(cat|dog)").fullmatch("cow")
    assert Regex(r"-?\d+").fullmatch("-42")
    assert not Regex(r"-?\d+").fullmatch("--4")
    assert Regex("ab?c").fullmatch("ac")
    assert Regex("ab?c").fullmatch("abc")


def test_regex_negated_class_and_escapes() -> None:
    assert Regex(r"[^,]+").fullmatch("abc")
    assert not Regex(r"[^,]+").fullmatch("a,b")
    assert Regex(r'"\w+"').fullmatch('"hello_1"')
    assert not Regex(r'"\w+"').fullmatch('"no space"')


def test_regex_parse_errors() -> None:
    with pytest.raises(RegexParseError):
        Regex("(unclosed")
    with pytest.raises(RegexParseError):
        Regex("[unclosed")


def test_schema_pattern_shape() -> None:
    props = [Property("id", "integer", max_length=2), Property("ok", "boolean")]
    pattern = schema_to_pattern(props)
    assert pattern.startswith(r"\{")
    assert pattern.endswith(r"\}")
    regex = compile_schema(props)
    assert regex.fullmatch('{"id":5,"ok":true}')
    assert not regex.fullmatch('{"id":5,"ok":maybe}')


def test_enum_requires_values() -> None:
    with pytest.raises(ValueError, match="enum"):
        schema_to_pattern([Property("role", "enum")])


def test_unsupported_type() -> None:
    with pytest.raises(ValueError, match="unsupported"):
        schema_to_pattern([Property("x", "array")])


def _schema() -> list[Property]:
    return [
        Property("name", "string", max_length=8),
        Property("age", "integer", max_length=3),
        Property("active", "boolean"),
        Property("role", "enum", ("admin", "user", "guest")),
    ]


def test_constrained_generation_is_always_valid_json() -> None:
    regex = compile_schema(_schema())
    vocab = default_vocab()
    for seed in range(40):
        result = constrained_generate(regex, vocab, random_model(seed), max_tokens=120)
        assert regex.fullmatch(result.text)
        json.loads(result.text)  # also parses as real JSON


def test_unconstrained_generation_is_usually_invalid() -> None:
    regex = compile_schema(_schema())
    vocab = default_vocab()
    valid = sum(
        1
        for seed in range(40)
        if regex.fullmatch(unconstrained_generate(vocab, random_model(seed), max_tokens=120))
    )
    assert valid == 0


def test_validity_report_contrast() -> None:
    report = validity_report(compile_schema(_schema()), trials=30)
    assert report.constrained_rate == 1.0
    assert report.unconstrained_rate == 0.0
    assert 0.0 < report.mean_allowed_fraction < 1.0


def test_biased_model_reaches_its_target() -> None:
    schema = [Property("name", "string", max_length=12), Property("age", "integer", max_length=3)]
    regex = compile_schema(schema)
    vocab = default_vocab()
    target = '{"name":"ada","age":42}'
    result = constrained_generate(regex, vocab, biased_model(target), max_tokens=120)
    assert result.text == target
    assert regex.fullmatch(result.text)


def test_constraint_rejects_disallowed_token() -> None:
    regex = compile_schema([Property("ok", "boolean")])
    vocab = default_vocab()
    constraint = Constraint(regex=regex, vocab=vocab)
    # The very first character must be '{', so a letter token is not allowed.
    allowed = {vocab[i] for i in constraint.allowed_ids()}
    assert "{" in allowed
    assert "a" not in allowed


def test_determinism() -> None:
    regex = compile_schema(_schema())
    vocab = default_vocab()
    a = constrained_generate(regex, vocab, random_model(1), max_tokens=120)
    b = constrained_generate(regex, vocab, random_model(1), max_tokens=120)
    assert a.text == b.text
