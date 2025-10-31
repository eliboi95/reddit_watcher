import subprocess
import signal
import sys
import time

"""Start both scripts as subprocesses"""
p1 = subprocess.Popen(["python3", "telegram_client.py"])
time.sleep(2)
p2 = subprocess.Popen(["python3", "reddit_client.py"])


def handle_exit(sig, frame):
    print("\nStopping both scripts...")

    """Gracefully terminate both processes"""
    p1.terminate()
    p2.terminate()

    """Wait a bit to let them shut down cleanly"""
    p1.wait(timeout=5)
    p2.wait(timeout=5)

    print("Both scripts stopped.")
    sys.exit(0)


"""Register Ctrl+C (SIGINT) handler"""
signal.signal(signal.SIGINT, handle_exit)

print("Both scripts started. Press Ctrl+C to stop.")

"""Keep main.py alive while subprocesses run"""
try:
    while True:
        pass
except KeyboardInterrupt:
    handle_exit(None, None)
