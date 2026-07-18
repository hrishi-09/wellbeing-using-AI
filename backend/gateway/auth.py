"""
API Gateway — authentication.

Every request into a core service passes through this session-based
guard first. In the architecture diagram this is the "Authentication &
rate limiting" role the API Gateway plays in front of the core
microservices — here the services all run in one process, but the
gate they pass through is still a single, explicit place.
"""
from functools import wraps
from flask import session, redirect, url_for

from backend.services.user_service import repository as user_repository
from backend.services.notification_service.notifier import notify


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return redirect(url_for("user_service.login"))
        # Guard against a stale session pointing at a user that no longer
        # exists (e.g. the SQLite file was reset by a redeploy/restart on
        # a host without a persistent disk). Without this check, accessing
        # any page here would 500 instead of asking the person to log in again.
        if user_repository.get_user_by_id(user_id) is None:
            session.clear()
            notify("Your session expired — please log in again.")
            return redirect(url_for("user_service.login"))
        return view(*args, **kwargs)
    return wrapped
