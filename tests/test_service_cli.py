"""Tests for the HTTP service routing and the CLI."""

from __future__ import annotations

from constrained_generation_library.cli import main
from constrained_generation_library.service import ConstraintService, handle

_SERVICE = ConstraintService.built()


def test_health_and_ready() -> None:
    status, payload = handle("GET", "/health", {}, _SERVICE)
    assert status == 200 and payload["pattern"].startswith("\\{")
    status, payload = handle("GET", "/ready", {}, _SERVICE)
    assert status == 200 and payload["status"] == "ready"


def test_generate_route_is_valid() -> None:
    status, payload = handle("POST", "/generate", {"seed": 5}, _SERVICE)
    assert status == 200
    assert payload["valid"] is True


def test_validate_route() -> None:
    status, payload = handle("POST", "/generate", {"seed": 1}, _SERVICE)
    text = payload["text"]
    status, payload = handle("POST", "/validate", {"text": text}, _SERVICE)
    assert status == 200 and payload["valid"] is True
    status, payload = handle("POST", "/validate", {"text": "not json"}, _SERVICE)
    assert status == 200 and payload["valid"] is False


def test_report_route_contrast() -> None:
    status, payload = handle("GET", "/report", {}, _SERVICE)
    assert status == 200
    assert payload["constrained_rate"] == 1.0
    assert payload["unconstrained_rate"] == 0.0


def test_validation_errors() -> None:
    status, _ = handle("POST", "/validate", {"text": 123}, _SERVICE)
    assert status == 400
    status, _ = handle("POST", "/generate", {"seed": -1}, _SERVICE)
    assert status == 400
    status, _ = handle("POST", "/generate", {"seed": True}, _SERVICE)
    assert status == 400


def test_unknown_route_and_metrics() -> None:
    status, _ = handle("GET", "/nope", {}, _SERVICE)
    assert status == 404
    handle("POST", "/generate", {"seed": 0}, _SERVICE)
    assert "service_requests_total" in _SERVICE.metrics.render_prometheus()


def test_cli_commands(capsys) -> None:  # type: ignore[no-untyped-def]
    main(["pattern"])
    main(["generate", "--seed", "2"])
    main(["report", "--trials", "20"])
    out = capsys.readouterr().out
    assert "\\{" in out
    assert "valid:" in out
    assert "constrained valid" in out
