import subprocess
import signal
import sys
import time

print("Python executable:", sys.executable, flush=True)
print("sys.path", sys.path, flush=True)


def start_subprocess(cmd):
    try:
        return subprocess.Popen(cmd)
    except Exception as e:
        print(f"Failed to start {cmd}: {e}")
        return None


"""Start both scripts as subprocesses"""
p1 = start_subprocess([sys.executable, "telegram_client.py"])
time.sleep(2)
p2 = start_subprocess([sys.executable, "reddit_client.py"])


def handle_exit(sig, frame):
    print("\nStopping both scripts...")
    for p in (p1, p2):
        if p and p.poll() is None:
            try:
                p.terminate()
            except Exception:
                pass
    # wait with timeout
    for p in (p1, p2):
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


"""Register Ctrl+C (SIGINT) handler"""
signal.signal(signal.SIGINT, handle_exit)

print("Both scripts started. Press Ctrl+C to stop.")

"""Keep main.py alive while subprocesses run"""
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    handle_exit(None, None)
