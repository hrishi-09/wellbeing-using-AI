"""
Notification service.

Today this is backed by Flask's flash-based session messaging, which
is enough for a single web app. It's kept as its own module — rather
than every route calling flash() directly — so this is the one seam
to swap in real push notifications, email, or reminders later without
touching any route code.
"""
from flask import flash as _flash


def notify(message, category="message"):
    _flash(message, category)
