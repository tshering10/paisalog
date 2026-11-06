import asyncio
import logging

from starlette.requests import Request

from app.core.observability import (
    JsonFormatter,
    get_pool_metrics,
    get_request_metrics,
    handle_unexpected_error,
    log_security_event,
    record_suspicious_activity,
    request_id_context,
    reset_activity_metrics,
    reset_request_metrics,
)


def test_request_id_is_returned(client):
    reset_request_metrics()
    request_id = "test-request-123"

    response = client.get(
        "/api/v1/health",
        headers={"X-Request-ID": request_id},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id


def test_request_metrics_capture_route_latency(client):
    reset_request_metrics()

    response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    metric = next(
        item
        for item in get_request_metrics()["routes"]
        if item["route"] == "/api/v1/health/live"
    )
    assert metric["method"] == "GET"
    assert metric["request_count"] == 1
    assert metric["error_count"] == 0
    assert metric["total_duration_ms"] >= 0
    assert metric["max_duration_ms"] >= 0


def test_metrics_endpoint_is_disabled_without_api_key(client):
    response = client.get("/api/v1/metrics")

    assert response.status_code == 404


def test_pool_metrics_report_utilization():
    class FakePool:
        def size(self):
            return 10

        def checkedin(self):
            return 8

        def checkedout(self):
            return 2

        def overflow(self):
            return 0

    assert get_pool_metrics(FakePool(), 20) == {
        "size": 10,
        "checked_in": 8,
        "checked_out": 2,
        "overflow": 0,
        "checked_out_limit": 30,
    }


def test_suspicious_activity_logs_at_threshold(caplog):
    reset_activity_metrics()

    with caplog.at_level("WARNING", logger="app.security"):
        for _ in range(5):
            record_suspicious_activity(
                "failed_login",
                subject_hash="hashed-subject",
            )

    warning = next(
        record
        for record in caplog.records
        if record.message == "suspicious_activity_detected"
    )
    assert warning.activity_type == "failed_login"
    assert warning.event_count == 5
    assert warning.subject_hash == "hashed-subject"


def test_liveness_check_does_not_require_database(client):
    response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_check_confirms_database(client):
    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_invalid_request_id_is_replaced(client):
    response = client.get(
        "/api/v1/health",
        headers={"X-Request-ID": "bad request\nwith secrets"},
    )

    request_id = response.headers["X-Request-ID"]
    assert request_id != "bad request\nwith secrets"
    assert len(request_id) == 36


def test_json_formatter_contains_safe_request_fields():
    record = logging.LogRecord(
        name="app.request",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="request_completed",
        args=(),
        exc_info=None,
    )
    record.request_id = "test-request-123"
    record.method = "GET"
    record.path = "/api/v1/health"
    record.status_code = 200
    record.duration_ms = 12.34

    serialized = JsonFormatter().format(record)

    assert '"request_id":"test-request-123"' in serialized
    assert '"method":"GET"' in serialized
    assert '"path":"/api/v1/health"' in serialized
    assert '"status_code":200' in serialized
    assert '"duration_ms":12.34' in serialized
    assert "password" not in serialized.lower()
    assert "access_token" not in serialized.lower()


def test_security_event_hashes_email_and_excludes_raw_value(monkeypatch):
    captured: dict[str, object] = {}

    class FakeLogger:
        def info(self, message: str, *, extra: dict[str, object]) -> None:
            captured["message"] = message
            captured.update(extra)

    original_get_logger = logging.getLogger

    def get_logger(name: str | None = None):
        return FakeLogger() if name == "app.security" else original_get_logger(name)

    monkeypatch.setattr("app.core.observability.logging.getLogger", get_logger)
    token = request_id_context.set("security-request-123")
    try:
        log_security_event(
            "login_failed",
            email="User@example.com",
            reason="invalid_credentials",
        )
    finally:
        request_id_context.reset(token)

    assert captured["message"] == "login_failed"
    assert captured["request_id"] == "security-request-123"
    assert captured["reason"] == "invalid_credentials"
    assert captured["email_hash"] != "User@example.com"
    assert "@" not in captured["email_hash"]


def test_unexpected_error_response_is_safe():
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/health",
            "headers": [],
        }
    )

    response = asyncio.run(
        handle_unexpected_error(request, RuntimeError("database secret"))
    )

    assert response.status_code == 500
    assert response.body == (
        b'{"detail":"Internal server error","request_id":"-"}'
    )
    assert response.headers["X-Request-ID"] == "-"
