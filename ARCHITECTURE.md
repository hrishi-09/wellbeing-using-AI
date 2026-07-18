# Auro — architecture

This codebase is split into three top-level layers:

```
frontend/                   Presentation layer — templates + static assets
  templates/                 Jinja2 HTML pages
  static/
    css/style.css
    js/dashboard.js, cbt.js

backend/                    All Flask application logic
  app.py                     API gateway — creates the app, points it at
                             frontend/ for templates+static, mounts every
                             service, handles errors
  gateway/
    auth.py                  Session auth guard every service route passes through

  services/
    user_service/            Registration, login, profile
      routes.py
      repository.py          Reads/writes via db.connection
    health_data_service/     Mood logs, CBT entries, dashboard, therapist report
      routes.py
      repository.py
      charts.py               Matplotlib chart rendering
    ai_engine/                The "brain" — narrative insights + lifestyle recommendations
      routes.py
      insights.py
      age_guidance.py
    content_service/          Curated/generated content
      cbt_library.py           CBT exercise catalog
      pdf_gen.py                Welcome letter + therapist report PDFs
    notification_service/
      notifier.py              Single seam for user-facing messages (flash today, push/email later)

db/                          Database layer
  connection.py               Connection handling + full schema (SQLite today)

run.py                       Project entry point — `python run.py` locally,
                             `gunicorn run:app` in production (see Procfile)
```

## Why this shape

- **frontend/** holds everything a browser receives directly — HTML, CSS, JS —
  with no Python in it. `backend/app.py` points Flask's `template_folder` and
  `static_folder` here explicitly, since it's a sibling folder rather than the
  Flask default location.
- **backend/** is one Python package. Within it, each service only reaches its
  own tables through its own `repository.py` — other services call across
  service boundaries the same way they would over a network if these were
  ever split into separately deployed processes.
- **db/** is deliberately its own top-level package, not nested inside
  `backend/`, so the database layer reads as a peer of the backend rather than
  a detail buried inside it — the schema and connection handling in
  `db/connection.py` is the single source of truth every service's repository
  goes through.
- **run.py** is the one entry point that can see both `backend/` and `db/` as
  importable top-level packages, in development and in production alike.

Nothing about routes, behavior, or the on-disk SQLite schema changed — this
is a structural reshape, not a rewrite.
