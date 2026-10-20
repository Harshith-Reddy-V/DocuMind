"""
DocuMind Root Server Launcher.
Runs the FastAPI application using the host's assigned PORT environment variable.
"""
import os
import sys

backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

if __name__ == "__main__":
    import uvicorn
    from app.config import settings

    port = int(os.environ.get("PORT", settings.PORT))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
