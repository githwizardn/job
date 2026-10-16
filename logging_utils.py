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


def _configure_root() -> None:
    """ერთხელ აკონფიგურირებს მშობელ logger-ს 'jobradar'."""
    global _configured
    if _configured:
        return

    root = logging.getLogger("jobradar")
    root.setLevel(logging.INFO)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    stream = _safe_stream()
    stream.setFormatter(fmt)
    root.addHandler(stream)

    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        fh = logging.FileHandler(
            os.path.join(OUTPUT_DIR, "jobradar.log"), encoding="utf-8"
        )
        fh.setFormatter(fmt)
        root.addHandler(fh)
    except OSError:
        pass

    root.propagate = False
    _configured = True


def get_logger(name: str = "jobradar") -> logging.Logger:
    _configure_root()
    if name == "jobradar" or name.startswith("jobradar."):
        return logging.getLogger(name)
    return logging.getLogger(f"jobradar.{name}")