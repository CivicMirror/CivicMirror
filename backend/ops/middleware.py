import json
import logging
import time
import uuid
from urllib.parse import parse_qs, urlencode

from django.http import StreamingHttpResponse

logger = logging.getLogger('civicmirror.request')

_SENSITIVE_KEYS = frozenset({
    'password', 'new_password', 'old_password', 'confirm_password',
    'token', 'access_token', 'refresh_token', 'id_token',
    'secret', 'api_key', 'apikey', 'authorization',
    'credit_card', 'card_number', 'cvv', 'ssn',
})

_SKIP_PATHS = frozenset({
    '/health/', '/healthz/', '/readyz/', '/ping/', '/favicon.ico',
})

_MAX_BODY_BYTES = 8_192


def _is_sensitive(key: str) -> bool:
    lower = key.lower().replace('-', '_')
    return lower in _SENSITIVE_KEYS or 'token' in lower or 'secret' in lower or 'password' in lower


def _redact(obj):
    """Recursively redact sensitive keys from dicts and lists."""
    if isinstance(obj, dict):
        return {k: '***' if _is_sensitive(k) else _redact(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_redact(item) for item in obj]
    return obj


def _parse_json(body_bytes: bytes):
    if not body_bytes:
        return None
    try:
        return _redact(json.loads(body_bytes))
    except (ValueError, UnicodeDecodeError):
        return None


def _redact_query(query_string: str) -> str:
    if not query_string:
        return ''
    params = parse_qs(query_string, keep_blank_values=True)
    redacted = {k: ['***'] if _is_sensitive(k) else v for k, v in params.items()}
    return urlencode(redacted, doseq=True)


def _client_ip(request) -> str:
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


class RequestResponseLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path in _SKIP_PATHS:
            return self.get_response(request)

        # Honour upstream request ID (Cloud Run / load balancer may set one)
        request_id = request.META.get('HTTP_X_REQUEST_ID') or str(uuid.uuid4())
        request.request_id = request_id

        # Capture request body — JSON only, guarded by Content-Length
        req_body = None
        content_length = int(request.META.get('CONTENT_LENGTH') or 0)
        if (
            'application/json' in (request.content_type or '')
            and 0 < content_length <= _MAX_BODY_BYTES
        ):
            try:
                req_body = _parse_json(request.body)
            except Exception:  # RawPostDataException, IOError, etc.
                pass

        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = round((time.monotonic() - start) * 1000, 2)

        # Capture response body — error responses only, non-streaming JSON under size limit
        resp_body = None
        is_error = response.status_code >= 400
        if (
            is_error
            and not isinstance(response, StreamingHttpResponse)
            and hasattr(response, 'content')
            and 'application/json' in response.get('Content-Type', '')
            and response.status_code not in (204, 304)
            and len(response.content) <= _MAX_BODY_BYTES
        ):
            resp_body = _parse_json(response.content)

        # user_id is read after get_response so DRF/Knox auth has run
        user_id = None
        if hasattr(request, 'user') and getattr(request.user, 'is_authenticated', False):
            user_id = request.user.pk

        record: dict = {
            'request_id': request_id,
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'duration_ms': duration_ms,
            'ip': _client_ip(request),
        }
        if query := _redact_query(request.META.get('QUERY_STRING', '')):
            record['query'] = query
        if user_id is not None:
            record['user_id'] = user_id
        if req_body is not None:
            record['request_body'] = req_body
        if resp_body is not None:
            record['response_body'] = resp_body

        level = logging.WARNING if is_error else logging.INFO
        logger.log(
            level,
            '%s %s → %s (%.0fms)',
            request.method, request.path, response.status_code, duration_ms,
            extra={'data': record},
        )

        response['X-Request-ID'] = request_id
        return response
