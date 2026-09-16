"""
Shared logger for the CCAR-F exercises.

Import `logger` and call `logger.info(...)`, `logger.debug(...)`, etc. -
whichever level fits. Two handlers are attached:

  - console: prints just the plain message (like print() did), so the
    screen stays easy to read.
  - file: writes every level (including debug) to a rotating log file
    under the repo's `logs/` folder, named `ccarf-practise-YYYYMMDD.log`,
    with full detail - timestamp, level, file/line, function, memory usage.
    Once a file reaches 10 MB, RotatingFileHandler renames it and starts a
    fresh one, so no file grows forever.
"""

import logging
import os
from datetime import date
from logging.handlers import RotatingFileHandler
from pathlib import Path

import psutil

# logs/ lives at the workspace root, shared across all exercises.
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = WORKSPACE_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / f"ccarf-practise-{date.today():%Y%m%d}.log"

TEN_MB = 10 * 1024 * 1024

# Used to read this process's own memory usage for each log line.
_current_process = psutil.Process(os.getpid())


class _AddMemoryUsage(logging.Filter):
    """Attaches the current process's memory usage (in MB) to every log record."""

    def filter(self, record):
        record.memory_mb = _current_process.memory_info().rss / (1024 * 1024)
        return True


logger = logging.getLogger("ccarf")
logger.setLevel(logging.DEBUG)  # let every level through to the handlers below

# Guard against adding duplicate handlers if this module gets imported more
# than once (e.g. by different exercise scripts in the same run).
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=TEN_MB, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.addFilter(_AddMemoryUsage())
    # Order: timestamp, level, file:line, function, memory usage, message.
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-5s | %(filename)s:%(lineno)d | %(funcName)s() | %(memory_mb).1fMB | %(message)s"
        )
    )
    logger.addHandler(file_handler)
