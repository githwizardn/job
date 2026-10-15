"""საერთო logger — ჩუმად გადაყლაპული შეცდომების ჩასაწერად."""
import logging
import os
import sys

from config import OUTPUT_DIR

_configured = False


def _safe_stream() -> logging.StreamHandler:
    """StreamHandler, რომელიც Windows-ის charmap-ზე არ ვარდება Unicode-ზე."""
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    return logging.StreamHandler(sys.stdout)


def get_logger(name: str = "jobradar") -> logging.Logger:
    global _configured
    logger = logging.getLogger(name)
    if _configured:
        return logger

    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                            datefmt="%H:%M:%S")

    stream = _safe_stream()
    stream.setFormatter(fmt)
    logger.addHandler(stream)

    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        fh = logging.FileHandler(os.path.join(OUTPUT_DIR, "jobradar.log"),
                                 encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except OSError:
        pass

    logger.propagate = False
    _configured = True
    return logger
