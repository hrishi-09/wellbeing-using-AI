"""
AI engine — age-wise guidance.

General, non-clinical wellness reference points by age bracket (sleep
targets, activity guidance, and things worth paying attention to at that
life stage). This is a reference scaffold, not a diagnostic or medical
tool — it never labels the user with a condition, only offers generic,
publicly-known wellness ranges (e.g. CDC/AAP-style sleep guidance).

Feeds into the AI engine's recommendations alongside insights.py,
personalizing them by life stage rather than mood data alone.
"""

BRACKETS = [
    ("child", 0, 12, "Child (under 13)"),
    ("teen", 13, 17, "Teen (13–17)"),
    ("young_adult", 18, 25, "Young Adult (18–25)"),
    ("adult", 26, 39, "Adult (26–39)"),
    ("midlife", 40, 59, "Midlife (40–59)"),
    ("senior", 60, 200, "Senior (60+)"),
]


def get_age_bracket(age):
    if age is None:
        return None
    for key, lo, hi, _label in BRACKETS:
        if lo <= age <= hi:
            return key
    return None


def get_age_guidance(age):
    """Returns a dict with label, sleep_hours, exercise, and a short list
    of notes tailored to the age bracket. Returns None if age is unknown."""
    bracket = get_age_bracket(age)
    if bracket is None:
        return None

    label = next(l for k, _, _, l in BRACKETS if k == bracket)

    guidance = {
        "child": {
            "sleep_hours": "9–12 hours/night",
            "exercise": "At least 60 minutes of active play most days",
            "notes": [
                "This app is designed for self-tracking by teens and adults — a "
                "parent or guardian should be involved in any use by a child.",
                "Mood and stress at this age are best supported with a trusted "
                "adult, not a self-tracking app alone.",
            ],
        },
        "teen": {
            "sleep_hours": "8–10 hours/night",
            "exercise": "At least 60 minutes of moderate–vigorous activity most days",
            "notes": [
                "It's worth involving a parent, guardian, or school counselor if "
                "mood or anxiety logs are consistently low — you don't have to "
                "sort it out alone.",
                "Screen time close to bedtime is one of the more common, and "
                "fixable, contributors to short sleep at this age.",
                "Academic and social pressure are common stress sources — the "
                "goals section is a good place to keep expectations realistic.",
            ],
        },
        "young_adult": {
            "sleep_hours": "7–9 hours/night",
            "exercise": "150+ minutes/week of moderate activity, plus 2 days of strength work",
            "notes": [
                "This stage often brings a lot of change at once (study, first "
                "jobs, moving, relationships) — routine and sleep consistency "
                "tend to matter more here than people expect.",
                "If anxiety or low mood logs persist for more than 2 weeks, a "
                "student counseling service or GP is a reasonable first stop.",
            ],
        },
        "adult": {
            "sleep_hours": "7–9 hours/night",
            "exercise": "150+ minutes/week of moderate activity, plus 2 days of strength work",
            "notes": [
                "Work/life balance and career stress are the most common drivers "
                "logged at this age — the habit tracker and pomodoro-style focus "
                "blocks tend to help more than willpower alone.",
                "Routine health checks (blood pressure, blood sugar) become more "
                "worth tracking here even without symptoms.",
            ],
        },
        "midlife": {
            "sleep_hours": "7–9 hours/night",
            "exercise": "150+ minutes/week moderate activity; add mobility/strength work",
            "notes": [
                "Caregiving responsibilities (kids, aging parents, or both) are a "
                "common source of chronic low-grade stress at this stage — it's "
                "worth logging honestly rather than normalizing it.",
                "This is a good decade to get baseline health numbers on record "
                "(blood pressure, cholesterol, blood sugar) if you haven't recently.",
            ],
        },
        "senior": {
            "sleep_hours": "7–8 hours/night (lighter, more fragmented sleep is normal)",
            "exercise": "150+ minutes/week moderate activity, with a strong emphasis on "
                        "balance and strength work to reduce fall risk",
            "notes": [
                "Social connection has an outsized effect on mood and cognitive "
                "health at this stage — worth treating as seriously as diet or exercise.",
                "Medication interactions and multiple prescriptions become more "
                "relevant — the medical information section is worth keeping current.",
                "Regular checkups matter more here even without new symptoms.",
            ],
        },
    }

    return {"bracket": bracket, "label": label, **guidance[bracket]}
