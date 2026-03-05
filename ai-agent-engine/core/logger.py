import logging
import sys
from pythonjsonlogger.json import JsonFormatter


class CustomJsonFormatter(JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = log_record.pop("asctime", self.formatTime(record))
        log_record["level"] = log_record.pop("levelname", record.levelname).upper()
        if "trace_id" not in log_record:
            log_record["trace_id"] = None
        if "duration_ms" not in log_record:
            log_record["duration_ms"] = None


def get_logger(name: str = "ai-agent") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = CustomJsonFormatter(
            fmt="%(asctime)s %(levelname)s %(message)s",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


logger = get_logger()
