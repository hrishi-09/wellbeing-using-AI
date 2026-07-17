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
"""
import os
from flask import Flask, render_template

from data import db
from services.user_service.routes import user_service
from services.health_data_service.routes import health_data_service
from services.ai_engine.routes import ai_engine

app = Flask(__name__)
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


if __name__ == "__main__":
    # use_reloader=False avoids "signal only works in main thread" errors that
    # occur when the dev server is launched from certain IDEs/debuggers where
    # Flask's auto-reloader isn't running in the main interpreter thread.
    app.run(debug=True, port=5050, use_reloader=False)
