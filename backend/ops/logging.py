import json
import logging
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """
    Structured JSON formatter compatible with Google Cloud Logging.
    Emits one JSON object per line to stdout.
    """

    _SEVERITY = {
        'DEBUG': 'DEBUG',
        'INFO': 'INFO',
        'WARNING': 'WARNING',
        'ERROR': 'ERROR',
        'CRITICAL': 'CRITICAL',
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            'severity': self._SEVERITY.get(record.levelname, record.levelname),
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            'logger': record.name,
            'message': record.getMessage(),
        }
        if hasattr(record, 'data') and isinstance(record.data, dict):
            payload.update(record.data)
        if record.exc_info:
            payload['exception'] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)
