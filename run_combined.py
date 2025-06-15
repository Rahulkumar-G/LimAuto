import subprocess
import sys
from pathlib import Path


def main() -> None:
    frontend_dir = Path(__file__).resolve().parent / "frontend"
    backend = subprocess.Popen([sys.executable, "-m", "BookLLM.src.api"])
    try:
        subprocess.call(
            [sys.executable, "-m", "http.server", "3000", "--directory", str(frontend_dir)]
        )
    finally:
        backend.terminate()


if __name__ == "__main__":
    main()

