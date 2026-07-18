"""
Development entry point.

Run locally with:
    python run.py

This exists at the project root (rather than running backend/app.py
directly) so that both top-level packages it depends on — "backend"
and "db" — are importable regardless of how or where it's launched.

Production hosts (Render, etc.) should point gunicorn at `run:app`
instead of running this file — see Procfile.
"""
from backend.app import app

if __name__ == "__main__":
    # use_reloader=False avoids "signal only works in main thread" errors that
    # occur when the dev server is launched from certain IDEs/debuggers where
    # Flask's auto-reloader isn't running in the main interpreter thread.
    app.run(debug=True, port=5050, use_reloader=False)
