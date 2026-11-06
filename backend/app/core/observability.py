import contextvars
import hashlib
import json
import logging
import threading
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

request_id_context: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id",
    default="-",
)
_metrics_lock = threading.Lock()
_metrics: dict[tuple[str, str], dict[str, float | int]] = {}
_activity_lock = threading.Lock()
_activity: dict[tuple[str, str], deque[float]] = defaultdict(deque)
_ACTIVITY_RULES = {
    "failed_login": (5, 15 * 60),
    "unauthorized_response": (20, 10 * 60),
    "csv_export": (10, 10 * 60),
}


def record_request_metric(
    *,
    method: str,
    route: str,
    status_code: int,
    duration_ms: float,
) -> None:
    key = (method, route)
    with _metrics_lock:
        metric = _metrics.setdefault(
            key,
            {
                "request_count": 0,
                "error_count": 0,
                "total_duration_ms": 0.0,
                "max_duration_ms": 0.0,
            },
        )
        metric["request_count"] += 1
        if status_code >= 500:
            metric["error_count"] += 1
        metric["total_duration_ms"] += duration_ms
        metric["max_duration_ms"] = max(metric["max_duration_ms"], duration_ms)


def get_request_metrics() -> dict[str, object]:
    with _metrics_lock:
        routes = [
            {
                "method": method,
                "route": route,
                **{
                    key: round(value, 2) if isinstance(value, float) else value
                    for key, value in metric.items()
                },
            }
            for (method, route), metric in sorted(_metrics.items())
        ]
    return {"routes": routes}


def reset_request_metrics() -> None:
    with _metrics_lock:
        _metrics.clear()


def reset_activity_metrics() -> None:
    with _activity_lock:
        _activity.clear()


def record_suspicious_activity(
    activity_type: str,
    *,
    subject_hash: str,
) -> None:
    limit, window_seconds = _ACTIVITY_RULES[activity_type]
    now = time.monotonic()
    key = (activity_type, subject_hash)
    with _activity_lock:
        events = _activity[key]
        while events and now - events[0] > window_seconds:
            events.popleft()
        events.append(now)
        count = len(events)
    if count == limit:
        logging.getLogger("app.security").warning(
            "suspicious_activity_detected",
            extra={
                "activity_type": activity_type,
                "subject_hash": subject_hash,
                "event_count": count,
                "window_seconds": window_seconds,
                "request_id": request_id_context.get(),
            },
        )


def get_pool_metrics(pool: object, max_overflow: int) -> dict[str, int | str]:
    return {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "checked_out_limit": pool.size() + max_overflow,
    }


def log_security_event(
    event: str,
    *,
    email: str | None = None,
    user_id: int | None = None,
    reason: str | None = None,
    request: Request | None = None,
) -> None:
    extra: dict[str, object] = {"request_id": request_id_context.get()}
    if email is not None:
        extra["email_hash"] = hashlib.sha256(email.lower().encode()).hexdigest()
    if user_id is not None:
        extra["user_id"] = user_id
    if reason is not None:
        extra["reason"] = reason
    if request is not None:
        extra["ip_address"] = request.client.host if request.client else None
        extra["user_agent"] = request.headers.get("user-agent")
    logging.getLogger("app.security").info(event, extra=extra)
    if event == "login_failed" and email is not None:
        record_suspicious_activity(
            "failed_login",
            subject_hash=extra["email_hash"],
        )


async def handle_unexpected_error(request: Request, error: Exception) -> JSONResponse:
    request_id = request_id_context.get()
    logging.getLogger("app.error").exception(
        "unhandled_exception",
        exc_info=(type(error), error, error.__traceback__),
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
        },
    )
    response = JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "request_id": request_id,
        },
    )
    response.headers["X-Request-ID"] = request_id
    return response


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(
                record,
                "request_id",
                request_id_context.get(),
            ),
        }
        for field in (
            "method",
            "path",
            "status_code",
            "duration_ms",
            "email_hash",
            "user_id",
            "reason",
            "ip_address",
            "user_agent",
            "activity_type",
            "subject_hash",
            "event_count",
            "window_seconds",
        ):
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        return json.dumps(payload, separators=(",", ":"), ensure_ascii=True)


def configure_logging() -> None:
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.INFO)
    if app_logger.handlers:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    app_logger.addHandler(handler)
    app_logger.propagate = False


def _request_id(request: Request) -> str:
    incoming = request.headers.get("X-Request-ID", "").strip()
    if incoming and len(incoming) <= 128 and all(
        character.isalnum() or character in "-._" for character in incoming
    ):
        return incoming
    return str(uuid.uuid4())


async def log_request(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = _request_id(request)
    token = request_id_context.set(request_id)
    started_at = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        route = request.scope.get("route")
        record_request_metric(
            method=request.method,
            route=getattr(route, "path", request.url.path),
            status_code=500,
            duration_ms=duration_ms,
        )
        logging.getLogger("app.request").exception(
            "request_failed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration_ms,
            },
        )
        raise
    else:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        route = request.scope.get("route")
        record_request_metric(
            method=request.method,
            route=getattr(route, "path", request.url.path),
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        if response.status_code in (401, 403):
            subject = request.client.host if request.client else "unknown"
            record_suspicious_activity(
                "unauthorized_response",
                subject_hash=hashlib.sha256(subject.encode()).hexdigest(),
            )
        if request.url.path == "/api/v1/transactions/export.csv":
            subject = request.client.host if request.client else "unknown"
            record_suspicious_activity(
                "csv_export",
                subject_hash=hashlib.sha256(subject.encode()).hexdigest(),
            )
        logging.getLogger("app.request").info(
            "request_completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        request_id_context.reset(token)
