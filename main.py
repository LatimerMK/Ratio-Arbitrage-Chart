import webview
import sys
import os
import logging
from datetime import datetime
from ui.template import HTML_CODE
from core.api import API


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
    Creates logs/ folder next to the .exe and configures file logging with today's date.
    All print() output and errors are redirected to logs/YYYY-MM-DD.log
    """
    logs_dir = os.path.join(EXE_DIR, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    log_filename = datetime.now().strftime("%Y-%m-%d") + ".log"
    log_path = os.path.join(logs_dir, log_filename)

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
        ]
    )

    # Redirect stdout (print) and stderr to the log file
    log_file = open(log_path, "a", encoding="utf-8", buffering=1)
    sys.stdout = log_file
    sys.stderr = log_file

    logging.info(f"[main.setup_logging] Log started: {log_path}")
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