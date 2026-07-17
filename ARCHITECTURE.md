# Auro — architecture

This codebase is organized to mirror the "Wellness app architecture" diagram:

```
app.py                     API gateway — creates the app, mounts every service, handles errors
gateway/
  auth.py                  Session auth guard every service route passes through

services/
  user_service/            Registration, login, profile
    routes.py
    repository.py          Owns: users, user_profile tables
  health_data_service/     Mood logs, CBT entries, dashboard, therapist report
    routes.py
    repository.py          Owns: mood_logs, cbt_entries tables
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

data/
  db.py                     Connection + schema — the "data & storage layer"

templates/, static/         Presentation layer (unchanged)
```

Each service only reaches its own tables through its own `repository.py` —
other services call across service boundaries the same way they would over
a network if these were ever split into separately deployed processes.
Nothing about routes, behavior, or the on-disk SQLite schema changed;
this is a structural reshape, not a rewrite.
