import os
import uvicorn
import asyncio
from dotenv import load_dotenv
from api.api_controller import app

# Load environment variables from .env file
load_dotenv()

# Environment configuration with defaults
DEBUG = os.getenv("LOGLEVEL", "info").lower()
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

def main():
    """Run the FastAPI application with Uvicorn"""
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=False,
        log_level=DEBUG if DEBUG else "warning",
        access_log=True,
        use_colors=True
        # Don't activate watching, because then you'd get
        # multiple schedulers and other funny things
        #reload_dirs="/app/config",
        #reload_includes="*.json"
    )

if __name__ == "__main__":
    main()
