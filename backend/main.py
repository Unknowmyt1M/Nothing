"""Main startup sequence for the FastAPI backend."""
import os
import sys
import logging

import uvicorn

from backend.config import HOST, PORT, DEBUG
from backend.database.json_db import database_init

# Force UTF-8 on Windows to avoid UnicodeEncodeError with emojis
if sys.platform.startswith("win"):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    """Initialize the local JSON database and run the FastAPI (uvicorn) server."""
    # 1. Initialize local JSON database directory
    try:
        database_init()
    except Exception as e:
        logger.critical("Failed to initialize database: %s", e)
        sys.exit(1)

    # 2. Import the app factory and start uvicorn
    from backend.app import create_app

    app = create_app()

    port = int(os.environ.get("PORT", PORT))
    logger.info("Starting UpDownVid Backend API on http://localhost:%d", port)

    # Note: uvicorn + an async server handles concurrent SSE connections well.
    uvicorn.run(
        app,
        host=HOST,
        port=port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()