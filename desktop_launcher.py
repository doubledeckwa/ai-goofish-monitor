"""
Desktop startup portal
use PyInstaller After packaging, it serves as the entry point of a single executable file and starts automatically. FastAPI Serve and open browser。
"""
import os
import sys
import time
import webbrowser
from pathlib import Path

import uvicorn

# PyInstaller Runtime resource directory：_MEIPASS；When not packaged, it is the directory where the current file is located.
BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


def _prepare_environment() -> None:
    """Make sure the working directory and module paths are correct"""
    os.chdir(BASE_DIR)
    if str(BASE_DIR) not in sys.path:
        sys.path.insert(0, str(BASE_DIR))


def run_app() -> None:
    """start up FastAPI Apply and automatically open the browser"""
    _prepare_environment()

    from src.app import app
    from src.infrastructure.config.settings import settings

    # Try opening the browser first and wait for the service to come up.
    url = f"http://127.0.0.1:{settings.server_port}"
    webbrowser.open(url)
    time.sleep(0.5)

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=settings.server_port,
        log_level="info",
        reload=False,
    )


if __name__ == "__main__":
    run_app()
