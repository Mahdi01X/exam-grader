import logging
import re
import sys

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


class PIIRedactor(logging.Filter):
    """Strip obvious PII (emails) from log records.

    Logs go through this filter so we never leak student or professor emails
    into operational logs.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = EMAIL_RE.sub("[redacted-email]", record.msg)
        if record.args:
            try:
                record.args = tuple(
                    EMAIL_RE.sub("[redacted-email]", a) if isinstance(a, str) else a
                    for a in record.args
                )
            except Exception:
                pass
        return True


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s | %(message)s")
    )
    handler.addFilter(PIIRedactor())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
