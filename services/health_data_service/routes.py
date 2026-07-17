"""
Health data service — routes.

Owns the dashboard, day-to-day mood/CBT logging, and the therapist
report. The report pulls in the content service (PDF rendering) and
the AI engine (narrative insights) the same way a real deployment
would call out to those services over the network.
"""
from datetime import date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, send_file, current_app

from config import OUT_DIR
from gateway.auth import login_required
from services.notification_service.notifier import notify
from services.user_service import repository as user_repository
from services.content_service import pdf_gen
from services.content_service.cbt_library import CBT_LIBRARY
from services.ai_engine import insights
from . import repository
from . import charts

health_data_service = Blueprint("health_data_service", __name__)


def _to_int(value, default=None):
    """Parse a form field to int; accepts comma-as-decimal by truncating, never raises."""
    if value is None or str(value).strip() == "":
        return default
    try:
        return int(float(str(value).replace(",", ".")))
    except (ValueError, TypeError):
        return default


def _to_float(value, default=None):
    """Parse a form field to float; tolerates a comma decimal separator, never raises."""
    if value is None or str(value).strip() == "":
        return default
    try:
        return float(str(value).replace(",", "."))
    except (ValueError, TypeError):
        return default


# ---------- dashboard ----------
@health_data_service.route("/dashboard")
@login_required
def dashboard():
    user = user_repository.get_user_by_id(session["user_id"])
    logs = repository.get_mood_logs(user["id"])
    today = date.today().isoformat()
    today_log = next((r for r in logs if r["log_date"] == today), None)

    # Chart generation touches matplotlib/numpy on every request; if any one
    # of them trips (e.g. a bad data point), show the dashboard without
    # charts rather than 500ing the whole page.
    try:
        trend_chart = charts.mood_trend_chart(logs)
        sleep_chart = charts.sleep_correlation_chart(logs)
        exercise_chart = charts.exercise_correlation_chart(logs)
        stats = charts.correlation_stats(logs)
    except Exception:
        current_app.logger.exception("Chart generation failed for user %s", user["id"])
        trend_chart = sleep_chart = exercise_chart = None
        stats = {"sleep_corr": None, "exercise_corr": None}

    streak = 0
    log_dates = {r["log_date"] for r in logs}
    d = date.today()
    while d.isoformat() in log_dates:
        streak += 1
        d -= timedelta(days=1)

    avg_mood = round(sum(r["mood_score"] for r in logs) / len(logs), 1) if logs else None

    return render_template(
        "dashboard.html",
        user=user,
        logs=list(reversed(logs)),
        today=today,
        today_log=today_log,
        trend_chart=trend_chart,
        sleep_chart=sleep_chart,
        exercise_chart=exercise_chart,
        stats=stats,
        streak=streak,
        avg_mood=avg_mood,
        total_entries=len(logs),
    )


@health_data_service.route("/log_mood", methods=["POST"])
@login_required
def log_mood():
    user_id = session["user_id"]
    log_date = request.form.get("log_date") or date.today().isoformat()
    mood_score = _to_int(request.form.get("mood_score"), default=5)
    anxiety_score = _to_int(request.form.get("anxiety_score"))
    sleep_hours = _to_float(request.form.get("sleep_hours"))
    exercise_minutes = _to_int(request.form.get("exercise_minutes"))
    notes = request.form.get("notes", "").strip()

    try:
        repository.upsert_mood_log(user_id, log_date, mood_score, anxiety_score, sleep_hours, exercise_minutes, notes)
    except Exception:
        current_app.logger.exception("Failed to save mood log for user %s", user_id)
        notify("Something went wrong saving that entry — please try again.")
        return redirect(url_for("health_data_service.dashboard"))

    return redirect(url_for("health_data_service.dashboard"))


# ---------- CBT ----------
@health_data_service.route("/cbt")
@login_required
def cbt():
    user_id = session["user_id"]
    entries = repository.get_cbt_entries(user_id)
    return render_template("cbt.html", library=CBT_LIBRARY, entries=entries)


@health_data_service.route("/cbt/save", methods=["POST"])
@login_required
def cbt_save():
    user_id = session["user_id"]
    entry_date = request.form.get("entry_date") or date.today().isoformat()
    exercise_type = request.form.get("exercise_type", "thought_record")
    situation = request.form.get("situation", "")
    automatic_thought = request.form.get("automatic_thought", "")
    evidence_for = request.form.get("evidence_for", "")
    evidence_against = request.form.get("evidence_against", "")
    balanced_thought = request.form.get("balanced_thought", "")
    mood_before = _to_int(request.form.get("mood_before"))
    mood_after = _to_int(request.form.get("mood_after"))

    try:
        repository.add_cbt_entry(
            user_id, entry_date, exercise_type, situation, automatic_thought,
            evidence_for, evidence_against, balanced_thought,
            mood_before, mood_after,
        )
    except Exception:
        current_app.logger.exception("Failed to save CBT entry for user %s", user_id)
        notify("Something went wrong saving that entry — please try again.")

    return redirect(url_for("health_data_service.cbt"))


# ---------- therapist report ----------
@health_data_service.route("/report/download")
@login_required
def report_download():
    user = user_repository.get_user_by_id(session["user_id"])
    logs = repository.get_mood_logs(user["id"], limit=365)
    cbt_entries = repository.get_cbt_entries(user["id"], limit=20)

    try:
        chart_data = {
            "trend": charts.mood_trend_chart(logs),
            "sleep": charts.sleep_correlation_chart(logs),
            "exercise": charts.exercise_correlation_chart(logs),
        }
    except Exception:
        current_app.logger.exception("Chart generation failed while building report for user %s", user["id"])
        chart_data = {"trend": None, "sleep": None, "exercise": None}

    try:
        stats = charts.correlation_stats(logs)
    except Exception:
        stats = {"sleep_corr": None, "exercise_corr": None}

    try:
        out_path = f"{OUT_DIR}/auro_therapist_report_{user['id']}.pdf"
        analysis = insights.build_graph_analysis(logs, stats)
        plan = insights.build_lifestyle_plan(logs)
        pdf_gen.generate_therapist_report_pdf(user, logs, cbt_entries, chart_data, stats, out_path, analysis=analysis, plan=plan)
    except Exception:
        current_app.logger.exception("Failed to generate therapist report for user %s", user["id"])
        notify("Couldn't generate the report — please try again in a moment.")
        return redirect(url_for("health_data_service.dashboard"))

    return send_file(out_path, as_attachment=True, download_name=f"Auro_Therapist_Report_{user['name'].replace(' ', '_')}.pdf")


# ---------- API (for JS charts / live refresh) ----------
@health_data_service.route("/api/mood_logs")
@login_required
def api_mood_logs():
    logs = repository.get_mood_logs(session["user_id"])
    return jsonify([dict(r) for r in logs])
