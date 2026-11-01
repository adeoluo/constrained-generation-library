"""Adversarial and property tests for the regex engine and schema compiler.

These exercise boundaries that structured-generation grammars tend to get wrong:
exact repetition bounds, empty objects, deeply nested grouping and alternation,
negated classes, and non-ASCII (unicode) keys and values. They use no
third-party dependency - the independent ``jsonschema`` differential lives in
``test_jsonschema_parity.py``.
"""

from __future__ import annotations

import json

import pytest

from constrained_generation_library.regex import Regex, RegexParseError
from constrained_generation_library.schema import (
    Property,
    compile_schema,
    schema_to_pattern,
)


def test_empty_object_schema() -> None:
    assert schema_to_pattern([]) == r"\{\}"
    regex = compile_schema([])
    assert regex.fullmatch("{}")
    assert not regex.fullmatch("{ }")
    assert not regex.fullmatch('{"a":1}')


@pytest.mark.parametrize("length", [0, 1, 2, 3, 4])
def test_string_length_boundaries(length: int) -> None:
    max_length = 3
    regex = compile_schema([Property("s", "string", max_length=max_length)])
    value = "a" * length
    document = json.dumps({"s": value}, ensure_ascii=False, separators=(",", ":"))
    assert bool(regex.fullmatch(document)) == (length <= max_length)


@pytest.mark.parametrize(
    ("value", "ok"),
    [("0", True), ("9", True), ("99", True), ("-99", True), ("100", False), ("-100", False)],
)
def test_integer_digit_boundaries(value: str, ok: bool) -> None:
    regex = compile_schema([Property("n", "integer", max_length=2)])
    assert bool(regex.fullmatch('{"n":' + value + "}")) == ok


def test_integer_rejects_leading_zero() -> None:
    regex = compile_schema([Property("n", "integer", max_length=3)])
    assert regex.fullmatch('{"n":0}')
    assert not regex.fullmatch('{"n":01}')
    assert not regex.fullmatch('{"n":007}')


def test_number_fractional_boundary() -> None:
    regex = compile_schema([Property("x", "number", max_length=2)])
    assert regex.fullmatch('{"x":1.5}')
    assert regex.fullmatch('{"x":-1.2345}')  # up to four fractional digits
    assert not regex.fullmatch('{"x":1.23456}')  # five is too many
    assert not regex.fullmatch('{"x":1.}')


def test_unicode_key_and_enum_and_value() -> None:
    regex = compile_schema(
        [
            Property("café", "string", max_length=8),
            Property("categoría", "enum", ("rojo", "verde", "azul")),
        ]
    )
    document = json.dumps(
        {"café": "résumé", "categoría": "verde"}, ensure_ascii=False, separators=(",", ":")
    )
    assert regex.fullmatch(document)
    wrong = json.dumps(
        {"café": "résumé", "categoría": "naranja"}, ensure_ascii=False, separators=(",", ":")
    )
    assert not regex.fullmatch(wrong)


def test_nested_escaping_in_keys_and_enums() -> None:
    # Keys and enum values packed with characters JSON must escape, nested with
    # regex metacharacters, must match only their exact serialization.
    names = ['a"b\\c', "x\ty\nz", 'quote"back\\slash', r"meta.*+?[]()|^$"]
    for name in names:
        regex = compile_schema([Property(name, "boolean")])
        serialized = json.dumps({name: True}, ensure_ascii=False, separators=(",", ":"))
        assert regex.fullmatch(serialized), serialized
        assert not regex.fullmatch(serialized.replace("true", "false") + "x")


def test_regex_metacharacters_treated_as_literals_via_escape() -> None:
    assert Regex(r"a\.b").fullmatch("a.b")
    assert not Regex(r"a\.b").fullmatch("axb")
    assert Regex(r"\(\)").fullmatch("()")
    assert Regex(r"\[\]").fullmatch("[]")
    assert Regex(r"\*\+\?").fullmatch("*+?")


def test_deeply_nested_grouping_and_alternation() -> None:
    pattern = "((a|b)(c|d))+"
    regex = Regex(pattern)
    assert regex.fullmatch("acbd")
    assert regex.fullmatch("ad")
    assert not regex.fullmatch("a")
    assert not regex.fullmatch("ae")


def test_negated_class_with_ranges_and_escapes() -> None:
    regex = Regex(r"[^0-9\s]+")
    assert regex.fullmatch("abcDEF")
    assert not regex.fullmatch("abc1")
    assert not regex.fullmatch("ab c")


def test_class_with_literal_hyphen_and_caret() -> None:
    assert Regex(r"[a\-z]+").fullmatch("a-z")  # hyphen escaped is literal
    assert Regex(r"[-a]+").fullmatch("-a")  # leading hyphen is literal
    assert Regex(r"[a^]+").fullmatch("a^")  # caret not leading is literal


def test_star_matches_empty_and_many() -> None:
    regex = Regex("a*")
    assert regex.fullmatch("")
    assert regex.fullmatch("aaaaa")
    assert not regex.fullmatch("b")


def test_alternation_with_empty_branch() -> None:
    regex = Regex("(a|)")
    assert regex.fullmatch("a")
    assert regex.fullmatch("")


@pytest.mark.parametrize("bad", ["(", ")", "[", "a|(", "*abc", "a++", "[a-"])
def test_malformed_patterns_raise(bad: str) -> None:
    with pytest.raises(RegexParseError):
        Regex(bad)


def test_dangling_escape_raises() -> None:
    with pytest.raises(RegexParseError):
        Regex("abc\\")
