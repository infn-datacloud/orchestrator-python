"""Main entry point for the orchestrator application."""

import uvicorn

from orchestrator import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0")
