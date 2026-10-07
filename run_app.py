from __future__ import annotations

import subprocess
import sys
import time


def main() -> None:
    api = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "app.main:app",
        "--host", "127.0.0.1", "--port", "8000"
    ])
    try:
        time.sleep(2)
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app/streamlit_app.py",
            "--server.address", "127.0.0.1", "--server.port", "8501"
        ], check=False)
    finally:
        api.terminate()
        try:
            api.wait(timeout=5)
        except subprocess.TimeoutExpired:
            api.kill()


if __name__ == "__main__":
    main()
