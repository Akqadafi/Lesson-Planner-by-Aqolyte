from pathlib import Path
import subprocess
import sys


APP_DIR = Path(__file__).resolve().parent
VENV_DIR = APP_DIR / ".venv"


def main() -> None:
    subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
    python = VENV_DIR / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    subprocess.run([str(python), "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run(
        [str(python), "-m", "pip", "install", "-r", str(APP_DIR / "requirements.txt")],
        check=True,
    )
    print(f"Environment ready: {VENV_DIR}")
    print("Copy .env.example to .env and add your secrets before starting the app.")


if __name__ == "__main__":
    main()
