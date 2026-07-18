"""
Auro — Mental Health Mood Tracker
API Gateway.

Creates the Flask application and mounts each core microservice as a
blueprint. In the architecture diagram, this file plays the role of
the "API Gateway (Authentication & rate limit)" box sitting in front
of the "core microservices" layer: it's the single place that wires
sessions and routing to the right service. The services below it
(user_service, health_data_service, ai_engine) are already separated
by module boundary and only talk to each other's public functions —
so any one of them can be pulled out into its own deployed process
later without changing how it's called from here.

This file is not meant to be run directly — use run.py at the project
root (`python run.py`), so both this "backend" package and the
sibling "db" package are importable. Production hosts should point
gunicorn at `run:app` (see Procfile) for the same reason.
"""
import os
from flask import Flask, render_template

from db import connection as db
from backend.services.user_service.routes import user_service
from backend.services.health_data_service.routes import health_data_service
from backend.services.ai_engine.routes import ai_engine

# The frontend (templates + static assets) lives in its own top-level
# folder, sibling to this backend package — not inside it — so Flask
# needs to be told explicitly where to find them.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FRONTEND_DIR = os.path.join(_PROJECT_ROOT, "frontend")

app = Flask(
    __name__,
    template_folder=os.path.join(_FRONTEND_DIR, "templates"),
    static_folder=os.path.join(_FRONTEND_DIR, "static"),
)
app.secret_key = os.environ.get("AURO_SECRET", "rajbari-auro-dev-secret-change-me")

db.init_db()

# ---- mount core microservices ----
app.register_blueprint(user_service)
app.register_blueprint(health_data_service)
app.register_blueprint(ai_engine)


# ---------- error handling ----------
@app.errorhandler(500)
def handle_500(e):
    app.logger.exception("Unhandled server error")
    return render_template("error.html"), 500

