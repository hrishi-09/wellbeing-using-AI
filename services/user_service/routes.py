"""
User service — routes.

Owns registration, authentication, and profile management. This is
the "User service: profile, auth/roles, preferences" box in the
architecture diagram.
"""
import json
from flask import Blueprint, render_template, request, redirect, url_for, session, send_file, current_app
from werkzeug.security import generate_password_hash, check_password_hash

from config import OUT_DIR
from gateway.auth import login_required
from services.notification_service.notifier import notify
from services.content_service import pdf_gen
from services.ai_engine import age_guidance
from . import repository

user_service = Blueprint("user_service", __name__)

PROFILE_FIELDS = [
    "date_of_birth", "occupation", "marital_status", "blood_group",
    "medical_conditions", "medications", "allergies", "therapist_name",
    "smoking", "alcohol", "diet_type", "activity_level", "work_schedule",
    "emergency_contact_name", "emergency_contact_relation", "emergency_contact_phone",
]

DEFAULT_PREFERENCES = {
    "units": "metric",
    "theme": "dark",
    "notifications_enabled": True,
    "age_guidance_enabled": True,
}


# ---------- auth ----------
@user_service.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("health_data_service.dashboard"))
    return redirect(url_for("user_service.login"))


@user_service.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        age = request.form.get("age", "").strip()
        sex = request.form.get("sex", "").strip()
        email = request.form.get("email", "").strip()
        location = request.form.get("location", "").strip()
        password = request.form.get("password", "")

        if not name or not phone or not password:
            notify("Name, phone number, and password are required.")
            return redirect(url_for("user_service.register"))

        if repository.get_user_by_phone(phone):
            notify("An account with this phone number already exists. Please log in.")
            return redirect(url_for("user_service.login"))

        user_id = repository.create_user(
            name, phone,
            int(age) if age.isdigit() else None,
            sex, email, location,
            generate_password_hash(password)
        )

        # Generate the welcome PDF
        pdf_path = f"{OUT_DIR}/auro_welcome_{user_id}.pdf"
        pdf_gen.generate_welcome_pdf(name, phone, age, sex, email, location, pdf_path)

        session["user_id"] = user_id
        session["welcome_pdf"] = pdf_path
        return redirect(url_for("user_service.welcome"))

    return render_template("register.html")


@user_service.route("/welcome")
@login_required
def welcome():
    user = repository.get_user_by_id(session["user_id"])
    return render_template("welcome.html", user=user)


@user_service.route("/welcome/download")
@login_required
def welcome_download():
    user = repository.get_user_by_id(session["user_id"])
    pdf_path = f"{OUT_DIR}/auro_welcome_{session['user_id']}.pdf"
    # Always regenerate rather than reusing a cached file — otherwise an
    # account created before a pdf_gen.py style update would keep serving
    # the old-looking PDF forever.
    pdf_gen.generate_welcome_pdf(user["name"], user["phone"], user["age"], user["sex"],
                                  user["email"], user["location"], pdf_path)
    return send_file(pdf_path, as_attachment=True, download_name="Welcome_to_Auro.pdf")


@user_service.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        user = repository.get_user_by_phone(phone)
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            return redirect(url_for("health_data_service.dashboard"))
        notify("Phone number or password is incorrect.")
        return redirect(url_for("user_service.login"))
    return render_template("login.html")


@user_service.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("user_service.login"))


# ---------- profile ----------
@user_service.route("/profile")
@login_required
def profile():
    user = repository.get_user_by_id(session["user_id"])
    prof = repository.get_profile(session["user_id"])

    goals = []
    preferences = dict(DEFAULT_PREFERENCES)
    if prof:
        if prof["goals"]:
            try:
                goals = json.loads(prof["goals"])
            except (ValueError, TypeError):
                goals = []
        if prof["preferences"]:
            try:
                preferences.update(json.loads(prof["preferences"]))
            except (ValueError, TypeError):
                pass

    guidance = None
    if preferences.get("age_guidance_enabled", True):
        guidance = age_guidance.get_age_guidance(user["age"])

    return render_template(
        "profile.html",
        user=user,
        prof=prof,
        goals=goals,
        preferences=preferences,
        guidance=guidance,
    )


@user_service.route("/profile/save", methods=["POST"])
@login_required
def profile_save():
    user_id = session["user_id"]
    form = request.form

    # -- Personal Information (lives on the users table) --
    name = form.get("name", "").strip()
    age_raw = form.get("age", "").strip()
    age = int(age_raw) if age_raw.isdigit() else None
    sex = form.get("sex", "").strip()
    email = form.get("email", "").strip()
    location = form.get("location", "").strip()
    if name:
        repository.update_user_basic(user_id, name, age, sex, email, location)

    # -- Everything else (user_profile table) --
    fields = {col: (form.get(col, "").strip() or None) for col in PROFILE_FIELDS}

    goals_raw = form.get("goals", "")
    goals = [g.strip() for g in goals_raw.splitlines() if g.strip()]
    fields["goals"] = json.dumps(goals)

    preferences = {
        "units": form.get("units", "metric"),
        "theme": form.get("theme", "dark"),
        "notifications_enabled": form.get("notifications_enabled") == "on",
        "age_guidance_enabled": form.get("age_guidance_enabled") == "on",
    }
    fields["preferences"] = json.dumps(preferences)

    repository.upsert_profile(user_id, fields)
    notify("Profile updated.")
    return redirect(url_for("user_service.profile"))
