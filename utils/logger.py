"""
Shared logger for the CCAR-F exercises.

Import `logger` and call `logger.info(...)`, `logger.debug(...)`, etc. -
whichever level fits. Two handlers are attached:

  - console: prints just the plain message (like print() did), so the
    screen stays easy to read.
  - file: writes every level (including debug) to a log file, with full
    detail - timestamp, level, file/line, function, memory usage.

Where the log file lives:
  Each exercise runs as `python <script>.py` from inside its own submodule
  folder (e.g. 01-agentic-architecture-and-orchestration/01-agentic-loops/).
  The log is written right there, next to that script, named after it
  (`<script>.log`) - not in a shared workspace-level `logs/` folder - so
  each exercise's run log travels with its code and gets committed
  alongside it.

Overwrite vs. append (parametrised via `configure()`):
  - Default (`configure(append=False)`, applied automatically on import):
    every run starts a clean file (`mode="w"`). The log then always
    reflects exactly one run - the most recent one - rather than a mix of
    old and new, which is what you want for a committed, single-run log.
  - Opt in to the old always-append behaviour with `configure(append=True)`,
    called once right after import and before any logging calls: keeps
    adding to the same file and only rotates to a new one (keeping up to 5
    backups) once it passes 10MB.

Security: a filter on the logger redacts anything that looks like an
Anthropic API key (`sk-ant-...`) from every log message before it reaches
either handler, so a key can never end up on screen or on disk even if a
future step accidentally logs raw headers/env values.
"""

import logging
import os
import re
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

import psutil

TEN_MB = 10 * 1024 * 1024

# Used to read this process's own memory usage for each log line.
_current_process = psutil.Process(os.getpid())

# Matches Anthropic API keys wherever they might show up in a log message.
_SECRET_PATTERN = re.compile(r"sk-ant-[A-Za-z0-9\-_]{10,}")


def _running_script_path() -> Path | None:
    """Path of the script actually invoked via `python <script>.py`, i.e.
    the exercise script itself - not this utils/logger.py module."""
    main_module = sys.modules.get("__main__")
    main_file = getattr(main_module, "__file__", None)
    return Path(main_file).resolve() if main_file else None


def _default_log_file() -> Path:
    """<exercise folder>/<script name>.log - falls back to the current
    working directory if run in a context with no __main__ file (e.g. a
    REPL)."""
    script_path = _running_script_path()
    if script_path is not None:
        return script_path.parent / f"{script_path.stem}.log"
    return Path.cwd() / "ccarf.log"


LOG_FILE = _default_log_file()


class _AddMemoryUsage(logging.Filter):
    """Attaches the current process's memory usage (in MB) to every log record."""

    def filter(self, record):
        record.memory_mb = _current_process.memory_info().rss / (1024 * 1024)
        return True


class _RedactSecrets(logging.Filter):
    """Scrubs anything that looks like an API key out of the message text
    before it reaches any handler (console or file)."""

    def filter(self, record):
        record.msg = _SECRET_PATTERN.sub("[REDACTED_API_KEY]", str(record.msg))
        record.args = ()  # msg is now a plain string; args would break %-formatting
        return True


logger = logging.getLogger("ccarf")
logger.setLevel(logging.DEBUG)  # let every level through to the handlers below

_file_handler: logging.Handler | None = None


def _build_file_handler(append: bool) -> logging.Handler:
    # delay=True: don't open (and for mode="w", truncate) the file until the
    # first actual log call. Without this, importing the module would
    # immediately truncate the file even if the script calls
    # configure(append=True) right afterwards, before logging anything.
    if append:
        handler = RotatingFileHandler(
            LOG_FILE, maxBytes=TEN_MB, backupCount=5, mode="a", encoding="utf-8", delay=True
        )
    else:
        handler = logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8", delay=True)
    handler.setLevel(logging.DEBUG)
    handler.addFilter(_AddMemoryUsage())
    # Order: timestamp, level, file:line, function, memory usage, message.
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-5s | %(filename)s:%(lineno)d | %(funcName)s() | %(memory_mb).1fMB | %(message)s"
        )
    )
    return handler


def configure(append: bool = False) -> None:
    """
    Choose how the log file for this run is written.

    append=False (default): start from a clean file every run - the log
        always shows exactly the most recent run.
    append=True: keep adding to the existing file, rotating to a new one
        (up to 5 backups kept) once it passes 10MB - the old always-append
        behaviour, for when you actually want history across runs.

    Call this once, right after `from utils.logger import logger, configure`
    and before any logging calls, if you want append+rotate instead of the
    default overwrite.
    """
    global _file_handler
    if _file_handler is not None:
        logger.removeHandler(_file_handler)
        _file_handler.close()
    _file_handler = _build_file_handler(append)
    logger.addHandler(_file_handler)


# Guard against adding duplicate handlers/filters if this module gets
# imported more than once (e.g. by different exercise scripts in the same run).
if not logger.handlers:
    logger.addFilter(_RedactSecrets())

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(console_handler)

    configure(append=False)  # default: fresh log file every run
