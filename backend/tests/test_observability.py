"""F10 observability: JSON logging + request-id middleware + health endpoints."""

from __future__ import annotations

import json
import logging

from app.utils.logging import JsonFormatter, configure_logging, get_logger


def test_json_formatter_emits_required_fields():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )
    record.request_id = "abc-123"
    output = formatter.format(record)
    payload = json.loads(output)
    assert payload["message"] == "hello world"
    assert payload["level"] == "INFO"
    assert payload["logger"] == "test"
    assert payload["request_id"] == "abc-123"
    assert "ts" in payload


def test_json_formatter_includes_extras_only():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="x",
        level=logging.WARNING,
        pathname=__file__,
        lineno=1,
        msg="event",
        args=None,
        exc_info=None,
    )
    record.farm_id = "f-1"
    output = formatter.format(record)
    payload = json.loads(output)
    assert payload["farm_id"] == "f-1"


def test_json_formatter_serialises_non_jsonable_extra():
    formatter = JsonFormatter()

    class Opaque:
        def __repr__(self) -> str:
            return "<opaque>"

    record = logging.LogRecord(
        name="x",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="m",
        args=None,
        exc_info=None,
    )
    record.thing = Opaque()
    output = formatter.format(record)
    payload = json.loads(output)
    assert payload["thing"] == "<opaque>"


def test_configure_logging_idempotent():
    root = logging.getLogger()
    before = len(root.handlers)
    configure_logging("INFO")
    configure_logging("INFO")
    after = len(root.handlers)
    assert before == after or after == 1


def test_get_logger_returns_named_logger():
    log = get_logger("agribud.test")
    assert log.name == "agribud.test"


def test_request_id_middleware_sets_header():
    from starlette.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        response = client.get("/health", headers={"X-Request-ID": "trace-1"})
        assert response.headers.get("x-request-id") == "trace-1"


def test_request_id_middleware_generates_id_when_absent():
    from starlette.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        response = client.get("/health")
        rid = response.headers.get("x-request-id")
        assert rid and len(rid) > 8


def test_readyz_returns_checks():
    from starlette.testclient import TestClient

    from app.main import app

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/readyz")
        assert response.status_code == 200
        body = response.json()
        assert "checks" in body
        assert "database" in body["checks"]


def test_healthz_returns_ok():
    from starlette.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_metrics_returns_process_info():
    from starlette.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        response = client.get("/metrics")
        assert response.status_code == 200
        body = response.json()
        assert "process" in body
        assert "pid" in body["process"]
        assert body["app"]["name"] == "AgriPulse AI API"
