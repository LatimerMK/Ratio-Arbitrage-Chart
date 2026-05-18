import webview
import sys
import os
import logging
from datetime import datetime
from ui.template import HTML_CODE
from core.api import API
from core.config import LOG_LEVEL


# ==========================================
# PATHS
# ==========================================

# Root of the bundled app (_MEIPASS) or project directory when running from source
BUNDLE_DIR = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))

# Directory where the .exe lives (or project root when running from source)
EXE_DIR = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(os.path.dirname(__file__))


# ==========================================
# VERSION
# ==========================================

def read_version() -> str:
    """Reads version from version.txt bundled into the build (_MEIPASS)."""
    version_path = os.path.join(BUNDLE_DIR, "version.txt")
    try:
        with open(version_path, 'r') as f:
            return f.read().strip()
    except Exception as e:
        print(f"[main.read_version] Error: {e}")
        return "unknown"

APP_VERSION = read_version()
APP_TITLE   = f"Ratio Arbitrage Chart {APP_VERSION}"


# ==========================================
# LOGGING SETUP
# ==========================================

def setup_logging() -> str:
    """
    Creates logs/ folder next to the .exe and configures logging with today's date.
    Output goes to BOTH the log file and the console (stdout).

    Log level is controlled by LOG_LEVEL in core/config.py:
      INFO  — app messages only: init, market counts, errors (default, recommended)
      DEBUG — full ccxt HTTP request/response dumps (use for troubleshooting only)
      WARNING — errors and warnings only

    Regardless of LOG_LEVEL, ccxt's own HTTP loggers are capped at WARNING
    to prevent raw API response bodies from flooding the output.
    """
    logs_dir = os.path.join(EXE_DIR, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    log_filename = datetime.now().strftime("%Y-%m-%d") + ".log"
    log_path = os.path.join(logs_dir, log_filename)

    log_format = "%(asctime)s [%(levelname)s] %(message)s"
    date_format = "%H:%M:%S"

    # Resolve numeric level from the string in config
    numeric_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)

    # File handler — logs go to the daily log file
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

    # Console handler — same output mirrored to original stdout
    console_handler = logging.StreamHandler(sys.__stdout__)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

    logging.basicConfig(level=numeric_level, handlers=[file_handler, console_handler])

    # Silence ccxt's verbose HTTP loggers (request/response dumps) regardless of LOG_LEVEL.
    # These fire at DEBUG and would flood the output even at INFO if not capped explicitly.
    for noisy_logger in (
        "ccxt",
        "ccxt.base.exchange",
        "ccxt.async_support",
        "urllib3",
        "urllib3.connectionpool",
        "asyncio",
    ):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

    # Redirect print() to a tee so it appears in both the log file and the console
    class _Tee:
        """Writes to both the log file and the original stream."""
        def __init__(self, file, original):
            self._file = file
            self._original = original

        def write(self, data):
            self._file.write(data)
            self._original.write(data)

        def flush(self):
            self._file.flush()
            self._original.flush()

    log_file = open(log_path, "a", encoding="utf-8", buffering=1)
    sys.stdout = _Tee(log_file, sys.__stdout__)
    sys.stderr = _Tee(log_file, sys.__stderr__)

    logging.info(f"[main.setup_logging] Log level: {LOG_LEVEL} | Log file: {log_path}")
    return log_path


# ==========================================
# ENTRY POINT
# ==========================================

if __name__ == "__main__":
    setup_logging()

    try:
        logging.info(f"[main] Starting {APP_TITLE}")
        api = API()
        window = webview.create_window(
            APP_TITLE,
            html=HTML_CODE,
            js_api=api,
            width=1280,
            height=750,
            background_color='#0d0f14'
        )
        api.window = window
        webview.start(debug=False)
        logging.info("[main] Application closed normally")

    except Exception as e:
        logging.exception(f"[main] Fatal error: {e}")
        raise