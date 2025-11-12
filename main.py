import subprocess
import signal
import sys
import time
from typing import Optional
import types
import os

from db.session import init_db  # ensure db creation


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
        print(f"Failed to start module {module}: {e}")
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
    print("\nStopping both scripts...")

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

    print("Both scripts stopped.")
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

    print("Both scripts started. Press Ctrl+C to stop.")

    # Keep main alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        handle_exit(signal.SIGINT, None, processes)
