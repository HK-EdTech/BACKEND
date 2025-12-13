# utils/logger.py
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys

def get_logger(
    name: str | None = None,
    log_level: str = "INFO",
    log_dir: str | Path = "logs",
    console: bool = True,
) -> logging.Logger:
    """
    Returns a logger that writes to logs/<module_name>.log
    Call once at the top of every module:
        logger = get_logger(__name__)
    """
    logger_name = name or __name__
    if logger_name == "__main__":
        logger_name = "main"

    logger = logging.getLogger(logger_name)

    # Prevent adding handlers multiple times (idempotent)
    if logger.handlers:
        return logger

    logger.setLevel(log_level.upper())

    # Ensure log directory exists
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # File goes to logs/your.module.name.log
    log_file = log_dir / f"{logger_name.replace('.', '_')}.log"

    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s [from %(filename)s:%(lineno)d]",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File handler — one file per module
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,   # 10 MB
        backupCount=10,
        encoding="utf-8"
    )
    file_handler.setLevel(log_level.upper())
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Optional console output
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level.upper())
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    logger.propagate = False
    return logger


# Test block
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-level", default="DEBUG")
    parser.add_argument("--no-console", action="store_true")
    args = parser.parse_args()

    logger = get_logger("test_direct_run", log_level=args.log_level, console=not args.no_console)
    logger.debug("Debug from direct run")
    logger.info("Info from direct run")
    logger.warning("This goes to logs/test_direct_run.log")