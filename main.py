import os
import signal
import subprocess
import sys
import time
import types
from typing import Optional
import logging
from logging.handlers import RotatingFileHandler

from db.session import init_db  # ensure db creation


logger = logging.getLogger("reddit_watcher")

console_handler = logging.StreamHandler()
rotating_file_handler = RotatingFileHandler(
    filename="bot.log", maxBytes=2000, backupCount=5
)

console_handler.setLevel(logging.INFO)
rotating_file_handler.setLevel(logging.ERROR)

logging_format = logging.Formatter(
    "%(asctime)s - %(levelname)s - [%(name)s] - %(filename)s:%(lineno)d in %(funcName)s() - %(message)s"
)

console_handler.setFormatter(logging_format)
rotating_file_handler.setFormatter(logging_format)

logger.addHandler(console_handler)
logger.addHandler(rotating_file_handler)


# -------------------------
# Start subprocess helper
# -------------------------
def start_subprocess(module: str) -> Optional[subprocess.Popen]:
    """
    Start a Python module as a subprocess, ensuring the project root is in cwd.
    """
    project_root = os.path.dirname(os.path.abspath(__file__))
    try:
        return subprocess.Popen(
            [sys.executable, "-m", module],
            cwd=project_root,
            env={**os.environ, "PYTHONPATH": project_root},
        )
    except Exception as e:
        logger.error(f"Failed to start module {module}: {e}")
        return None


# -------------------------
# Graceful shutdown
# -------------------------
def handle_exit(
    sig: int,
    frame: Optional[types.FrameType],
    processes: list[Optional[subprocess.Popen]],
) -> None:
    """Gracefully terminate subprocesses on exit signal."""
    logger.info("Stopping both scripts...")

    for p in processes:
        if p and p.poll() is None:
            try:
                p.terminate()
            except Exception:
                pass

    for p in processes:
        if p:
            try:
                p.wait(timeout=5)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass

    logger.info("Both scripts stopped.")
    sys.exit(0)


# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    # Ensure database exists
    init_db()

    # Start both scripts as modules
    telegram_process = start_subprocess("telegram_bot.handlers")
    time.sleep(2)  # give telegram bot a moment to start
    reddit_process = start_subprocess("reddit_bot.reddit_client")

    processes: list[Optional[subprocess.Popen]] = [telegram_process, reddit_process]

    # Handle Ctrl+C
    signal.signal(signal.SIGINT, lambda sig, frame: handle_exit(sig, frame, processes))

    logger.info("Both scripts started. Press Ctrl+C to stop.")

    # Keep main alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        handle_exit(signal.SIGINT, None, processes)
