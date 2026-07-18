"""
AI engine — routes.

The AI engine reads from the health data service (mood logs) and the
user service (profile preferences), then hands back a personalized
lifestyle recommendation. This is the orchestration role the AI engine
plays in the architecture diagram, expressed as a single endpoint
today.
"""
import json
from flask import Blueprint, render_template, session

from backend.gateway.auth import login_required
from backend.services.user_service import repository as user_repository
from backend.services.health_data_service import repository as health_repository
from . import insights
from . import age_guidance

ai_engine = Blueprint("ai_engine", __name__)


@ai_engine.route("/lifestyle")
@login_required
def lifestyle():
    user_id = session["user_id"]
    user = user_repository.get_user_by_id(user_id)
    logs = health_repository.get_mood_logs(user_id, limit=365)
    plan = insights.build_lifestyle_plan(logs)

    prof = user_repository.get_profile(user_id)
    show_age_guidance = True
    if prof and prof["preferences"]:
        try:
            show_age_guidance = json.loads(prof["preferences"]).get("age_guidance_enabled", True)
        except (ValueError, TypeError):
            pass
    guidance = age_guidance.get_age_guidance(user["age"]) if show_age_guidance else None

    return render_template("lifestyle.html", plan=plan, total_entries=len(logs), guidance=guidance)
