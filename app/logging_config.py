"""
Merkezi loglama yapılandırması — nlp-server mimarisine uyumlu.

- Stdout'a tek satır JSON yazar (container/infra log toplayıcılarıyla uyumlu).
- PIIRedactFilter her log kaydını filtreler; PII yanlışlıkla mesaja karışsa bile
  dışarı çıkmaz.
- setup_logging() uygulamanın en başında bir kez çağrılır.
"""
import json
import logging
from typing import Any

_BUILTIN_ATTRS: frozenset[str] = frozenset({
    "name", "msg", "args", "levelname", "levelno", "pathname",
    "filename", "module", "exc_info", "exc_text", "stack_info",
    "lineno", "funcName", "created", "msecs", "relativeCreated",
    "thread", "threadName", "processName", "process", "message",
    "taskName",
})


# ── JSON formatter ─────────────────────────────────────────────────────────────

class _JsonFormatter(logging.Formatter):
    """
    Her LogRecord'u tek satır JSON'a dönüştürür.

    Sabit alanlar:
        ts     – YYYY-MM-DDTHH:MM:SS
        level  – DEBUG / INFO / WARNING / ERROR / CRITICAL
        logger – logger adı
        msg    – formatlanmış mesaj
        exc    – "ExcType: mesaj" (exc_info varsa), aksi hâlde null

    logger.xxx(..., extra={"key": "value"}) ile gelen alanlar otomatik eklenir.
    Tam traceback loglanmaz — local değişkenlerde PII olabilir.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts":     self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level":  record.levelname,
            "logger": record.name,
            "msg":    record.getMessage(),
            "exc":    None,
        }

        if record.exc_info:
            exc_type, exc_value, _ = record.exc_info
            if exc_type is not None:
                payload["exc"] = f"{exc_type.__name__}: {exc_value}"

        for key, value in record.__dict__.items():
            if key not in _BUILTIN_ATTRS and not key.startswith("_"):
                payload[key] = value

        return json.dumps(payload, ensure_ascii=False, default=str)


# ── PII redaction filter ───────────────────────────────────────────────────────

class PIIRedactFilter(logging.Filter):
    """
    Her LogRecord mesajını ve extra alanlarını PII açısından tarar, maskeler.
    record.msg'yi yerinde değiştirir — tüm formatter'larla uyumludur.
    """

    def _scrub(self, text: str) -> str:
        from app.sanitizer import _PATTERNS
        for pattern, label in _PATTERNS:
            text = pattern.sub(label, text)
        return text

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self._scrub(str(record.msg))

        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: self._scrub(v) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            else:
                record.args = tuple(
                    self._scrub(a) if isinstance(a, str) else a
                    for a in record.args
                )

        for key, value in list(record.__dict__.items()):
            if key not in _BUILTIN_ATTRS and not key.startswith("_") and isinstance(value, str):
                setattr(record, key, self._scrub(value))

        return True


# ── Public entry point ─────────────────────────────────────────────────────────

def setup_logging(level: str = "INFO") -> None:
    """
    Root logger'ı yapılandırır. main.py'de uygulama başlarken bir kez çağrılır.

    Args:
        level: Log seviyesi ("DEBUG", "INFO", "WARNING", "ERROR").
               LOG_LEVEL env değişkeninden okunur.
    """
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()

    handler = logging.StreamHandler()
    handler.setFormatter(_JsonFormatter())
    handler.addFilter(PIIRedactFilter())
    root.addHandler(handler)

    # uvicorn.access kendi access log'unu yazar; middleware'deki http_request logu
    # ile çakışmaması için kapatıyoruz.
    logging.getLogger("uvicorn.access").propagate = False

    logging.getLogger(__name__).info(
        "Logging başlatıldı", extra={"level": level}
    )
