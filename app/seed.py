from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.domain import TOUCHPOINT_ORDER
from app.models import (
    Capsule,
    CityReference,
    CoachMessage,
    Completion,
    JournalEntry,
    MoodEntry,
    Notification,
    Participant,
    Role,
)

WEEK_THEMES = (
    ("Listen before leading", "notice patterns without rushing to fix them"),
    ("Clarify the mandate", "turn expectations into a shared definition of success"),
    ("Map the system", "understand who shapes decisions, trust, and information"),
    ("Build the team contract", "make collaboration and ownership explicit"),
    ("Choose an early win", "create evidence of progress without overpromising"),
    ("Create feedback loops", "make useful feedback frequent and low-friction"),
    ("Navigate tension", "surface disagreement before it becomes drag"),
    ("Protect priorities", "separate important work from visible noise"),
    ("Lead across boundaries", "influence partners without relying on authority"),
    ("Improve decisions", "make ownership, evidence, and reversibility visible"),
    ("Build a sustainable pace", "replace heroics with dependable operating rhythms"),
    ("Scale through others", "grow capability instead of becoming the bottleneck"),
    ("Write the next chapter", "turn the first 90 days into a durable plan"),
)

EUROPEAN_CITIES = (
    ("riga", "Riga", "LV", "Europe/Riga"),
    ("tallinn", "Tallinn", "EE", "Europe/Tallinn"),
    ("vilnius", "Vilnius", "LT", "Europe/Vilnius"),
    ("helsinki", "Helsinki", "FI", "Europe/Helsinki"),
    ("stockholm", "Stockholm", "SE", "Europe/Stockholm"),
    ("copenhagen", "Copenhagen", "DK", "Europe/Copenhagen"),
    ("berlin", "Berlin", "DE", "Europe/Berlin"),
    ("amsterdam", "Amsterdam", "NL", "Europe/Amsterdam"),
    ("paris", "Paris", "FR", "Europe/Paris"),
    ("madrid", "Madrid", "ES", "Europe/Madrid"),
    ("rome", "Rome", "IT", "Europe/Rome"),
    ("lisbon", "Lisbon", "PT", "Europe/Lisbon"),
    ("warsaw", "Warsaw", "PL", "Europe/Warsaw"),
    ("prague", "Prague", "CZ", "Europe/Prague"),
    ("vienna", "Vienna", "AT", "Europe/Vienna"),
    ("dublin", "Dublin", "IE", "Europe/Dublin"),
)

DAY_LENSES = (
    "Observe",
    "Ask",
    "Connect",
    "Make visible",
    "Experiment",
    "Reflect",
    "Reset",
)

SLOT_COPY = {
    "focus": (
        "See the signal",
        "Before reacting, look for one repeated signal connected to {theme}. Your goal today is "
        "to {promise}. Write down what you know, what you assume, and what you still need to ask.",
        "What signal deserves your attention before you act?",
        4,
    ),
    "action": (
        "Run one small move",
        "Turn insight into a low-risk action. Choose one conversation, decision, or artifact that "
        "helps you {promise}. Keep it small enough to complete today and concrete enough that "
        "another person can notice the difference.",
        "What is the smallest useful move you can finish today?",
        8,
    ),
    "reflection": (
        "Close the loop",
        "Progress compounds when you name what changed. Review today's move through the lens of "
        "{theme}. Capture one fact, one surprise, and one adjustment for tomorrow.",
        "What became clearer after you acted?",
        5,
    ),
}

SAME_COMPANY_MANAGER_CAPSULES = (
    {
        "day": 1,
        "touchpoint": "focus",
        "title": "Name the identity shift",
        "eyebrow": "Day 1 · Same company, new responsibility",
        "body": (
            "You know the company, but your scorecard has changed. Your value now includes the "
            "clarity, judgment, and growth of other people. List three habits that made you a "
            "strong individual contributor. Mark which one may become a trap when you lead."
        ),
        "prompt": "What must success through others replace on your old scorecard?",
        "duration_minutes": 5,
        "illustration_path": "/static/illustrations/day-01-identity-shift.webp",
        "resource_title": "How to be an effective boss: the identity shift",
        "resource_url": (
            "https://www.ccl.org/articles/leading-effectively-articles/"
            "identity-shift-achieving-results-by-managing-others/"
        ),
        "resource_kind": "Read",
    },
    {
        "day": 1,
        "touchpoint": "action",
        "title": "Draft a stop-doing list",
        "eyebrow": "Day 1 · Move from me to we",
        "body": (
            "Choose one task you still own because you are good at it. Write a safe handover: the "
            "outcome, the decision boundary, the support available, and the next review point. Do "
            "not delegate it yet. First make the transfer clear enough to discuss."
        ),
        "prompt": "What can you stop owning without abandoning the team?",
        "duration_minutes": 8,
        "resource_title": "The 12 common challenges of new managers",
        "resource_url": (
            "https://www.ccl.org/articles/leading-effectively-articles/"
            "first-time-managers-must-conquer-these-challenges/"
        ),
        "resource_kind": "Read",
    },
    {
        "day": 1,
        "touchpoint": "reflection",
        "title": "Catch the expert reflex",
        "eyebrow": "Day 1 · Notice before changing",
        "body": (
            "Recall one moment today when you solved, corrected, or answered before someone else "
            "could think. Do not judge it. Record what made the reflex useful and what it may have "
            "prevented the other person from owning."
        ),
        "prompt": "Where could one question replace one answer tomorrow?",
        "duration_minutes": 5,
        "resource_title": "First-time managers: it is not about me anymore",
        "resource_url": (
            "https://www.ccl.org/wp-content/uploads/2015/05/"
            "not-about-me-first-time-managers-research-paper-center-for-creative-leadership.pdf"
        ),
        "resource_kind": "Read",
    },
    {
        "day": 2,
        "touchpoint": "focus",
        "title": "Suspend the insider shortcut",
        "eyebrow": "Day 2 · Familiar place, fresh evidence",
        "body": (
            "Company knowledge is useful, but it can make assumptions feel like facts. Before your "
            "next conversation, split a page into three columns: what I observed, what I was told, "
            "and what I inferred. Keep them separate."
        ),
        "prompt": "Which familiar story about this team needs fresh evidence?",
        "duration_minutes": 5,
        "illustration_path": "/static/illustrations/day-02-listen-first.webp",
        "resource_title": "Listen to understand and ask powerful questions",
        "resource_url": (
            "https://www.ccl.org/articles/leading-effectively-articles/"
            "how-to-use-coaching-and-mentoring-programs-to-develop-new-leaders/"
        ),
        "resource_kind": "Read",
    },
    {
        "day": 2,
        "touchpoint": "action",
        "title": "Run a re-contracting one-to-one",
        "eyebrow": "Day 2 · Listen before leading",
        "body": (
            "Invite one direct report or former peer to a 20-minute conversation. Ask: what should "
            "I protect, what should I reconsider, and what support would be useful now? Listen for "
            "facts, feelings, and values. End by repeating what you heard, not by promising a fix."
        ),
        "prompt": "Who needs to experience you listening in the new role?",
        "duration_minutes": 10,
        "resource_title": "Google re:Work guide to team effectiveness",
        "resource_url": "https://rework.withgoogle.com/en/guides/understanding-team-effectiveness",
        "resource_kind": "Read",
    },
    {
        "day": 2,
        "touchpoint": "reflection",
        "title": "Measure airtime, not agreement",
        "eyebrow": "Day 2 · Make candor possible",
        "body": (
            "Review the conversation without grading its outcome. Estimate how much you spoke, "
            "which question opened new information, and where the other person became cautious. "
            "Choose one behavior that will make tomorrow's conversation safer."
        ),
        "prompt": "What did someone say only after you left enough space?",
        "duration_minutes": 5,
        "resource_title": "Is it safe to speak up at work?",
        "resource_url": (
            "https://www.ted.com/talks/worklife_with_adam_grant_is_it_safe_to_speak_up_at_work"
        ),
        "resource_kind": "Watch",
    },
    {
        "day": 3,
        "touchpoint": "focus",
        "title": "Name the relationship shift",
        "eyebrow": "Day 3 · Familiar people, changed role",
        "body": (
            "A promotion changes expectations even when nobody changes desks. Name three "
            "relationships affected by your new responsibility. For each, write what must stay "
            "human and what now needs a clearer boundary."
        ),
        "prompt": "Which familiar relationship most needs an explicit reset?",
        "duration_minutes": 5,
        "illustration_path": "/static/illustrations/day-03-trust-map.webp",
        "resource_title": "Clarify team roles and responsibilities",
        "resource_url": (
            "https://www.atlassian.com/team-playbook/plays/roles-and-responsibilities"
        ),
        "resource_kind": "Read",
    },
    {
        "day": 3,
        "touchpoint": "action",
        "title": "Draw the trust-and-work map",
        "eyebrow": "Day 3 · See the real system",
        "body": (
            "Place your team goal at the center of a page. Add the people and adjacent teams who "
            "shape information, decisions, delivery, and trust. Use solid lines for dependable "
            "links and dotted lines for fragile ones. Circle one relationship to learn about."
        ),
        "prompt": "Which relationship matters more than the org chart suggests?",
        "duration_minutes": 10,
        "resource_title": "Atlassian Network of Teams play",
        "resource_url": "https://www.atlassian.com/team-playbook/plays/network-of-teams",
        "resource_kind": "Watch + read",
    },
    {
        "day": 3,
        "touchpoint": "reflection",
        "title": "Choose one trust-building promise",
        "eyebrow": "Day 3 · Close the first loop",
        "body": (
            "Pick one small promise you can keep by the end of this week: clarify a decision, "
            "share missing context, protect focus, or schedule a difficult conversation. Make the "
            "owner, outcome, and time visible. Trust starts with a promise that can be observed."
        ),
        "prompt": "What will people be able to see you keep by Friday?",
        "duration_minutes": 5,
        "resource_title": "Create working agreements with your team",
        "resource_url": "https://www.atlassian.com/team-playbook/plays/working-agreements",
        "resource_kind": "Watch + read",
    },
)


def _capsule_copy(day: int, touchpoint: str) -> tuple[str, str, str, str, int]:
    week_index = min((day - 1) // 7, len(WEEK_THEMES) - 1)
    theme, promise = WEEK_THEMES[week_index]
    lens = DAY_LENSES[(day - 1) % len(DAY_LENSES)]
    title, body, prompt, duration = SLOT_COPY[touchpoint]
    eyebrow = f"Day {day} · {lens} · {theme}"
    return (
        f"{title}: {theme.lower()}",
        eyebrow,
        body.format(theme=theme.lower(), promise=promise),
        prompt,
        duration,
    )


def _seed_same_company_manager_capsules(session: Session, role: Role) -> None:
    for values in SAME_COMPANY_MANAGER_CAPSULES:
        capsule = session.scalar(
            select(Capsule).where(
                Capsule.role_id == role.id,
                Capsule.day == values["day"],
                Capsule.touchpoint == values["touchpoint"],
                Capsule.company_filter == "same",
                Capsule.city_filter == "same",
                Capsule.work_mode_filter == "any",
            )
        )
        if capsule is None:
            capsule = Capsule(
                role_id=role.id,
                company_filter="same",
                city_filter="same",
                work_mode_filter="any",
                **values,
            )
            session.add(capsule)
            continue
        for key, value in values.items():
            setattr(capsule, key, value)


def seed_database(session: Session, *, reset_demo: bool = False) -> Participant:
    for slug, name, country_code, timezone_name in EUROPEAN_CITIES:
        if session.scalar(select(CityReference.id).where(CityReference.slug == slug)) is None:
            session.add(
                CityReference(
                    slug=slug,
                    name=name,
                    country_code=country_code,
                    timezone=timezone_name,
                )
            )
    session.flush()

    if reset_demo:
        participant_ids = session.scalars(
            select(Participant.id).where(Participant.is_demo.is_(True))
        ).all()
        if participant_ids:
            session.execute(
                delete(Notification).where(Notification.participant_id.in_(participant_ids))
            )
            session.execute(
                delete(CoachMessage).where(CoachMessage.participant_id.in_(participant_ids))
            )
            session.execute(
                delete(JournalEntry).where(JournalEntry.participant_id.in_(participant_ids))
            )
            session.execute(delete(MoodEntry).where(MoodEntry.participant_id.in_(participant_ids)))
            session.execute(
                delete(Completion).where(Completion.participant_id.in_(participant_ids))
            )
            session.execute(delete(Participant).where(Participant.id.in_(participant_ids)))
            session.commit()

    role = session.scalar(select(Role).where(Role.slug == "people-manager"))
    if role is None:
        role = Role(
            slug="people-manager",
            title="People Manager",
            description="A manager taking responsibility for a new team or a broader mandate.",
        )
        session.add(role)
        session.flush()

    existing_capsules = session.scalar(
        select(Capsule.id).where(Capsule.role_id == role.id).limit(1)
    )
    if existing_capsules is None:
        for day in range(1, 91):
            for touchpoint in TOUCHPOINT_ORDER:
                title, eyebrow, body, prompt, duration = _capsule_copy(day, touchpoint)
                session.add(
                    Capsule(
                        role_id=role.id,
                        day=day,
                        touchpoint=touchpoint,
                        title=title,
                        eyebrow=eyebrow,
                        body=body,
                        prompt=prompt,
                        duration_minutes=duration,
                    )
                )
        session.flush()

        day_18_action = session.scalar(
            select(Capsule).where(
                Capsule.role_id == role.id,
                Capsule.day == 18,
                Capsule.touchpoint == "action",
            )
        )
        if day_18_action is not None:
            day_18_action.title = "Make one low-cost ask"
            day_18_action.eyebrow = "Day 18 · Map the invisible network"
            day_18_action.body = (
                "Choose one stakeholder outside your reporting line. Ask for 20 minutes to learn "
                "what makes collaboration easy, where work gets stuck, and what they wish your "
                "team "
                "understood. Do not pitch a solution. Your win is a better map."
            )
            day_18_action.prompt = "Who can show you a part of the system your org chart cannot?"

    _seed_same_company_manager_capsules(session, role)
    session.flush()

    participant = session.scalar(
        select(Participant).where(Participant.external_id == "demo-jordan")
    )
    if participant is None:
        participant = Participant(
            external_id="demo-jordan",
            name="Jordan Lee",
            email="jordan@example.com",
            role_id=role.id,
            company_context="new",
            city_context="same",
            work_mode="hybrid",
            city="Riga",
            timezone="Europe/Riga",
            start_date=date.today() - timedelta(days=17),
            current_day=18,
            current_touchpoint="action",
            is_demo=True,
            last_active_at=datetime.now(UTC) - timedelta(hours=2),
        )
        session.add(participant)
        session.flush()

        completed_capsules = session.scalars(
            select(Capsule).where(
                Capsule.role_id == role.id,
                Capsule.day <= 18,
            )
        ).all()
        for capsule in completed_capsules:
            if capsule.day < 18 or capsule.touchpoint == "focus":
                session.add(Completion(participant_id=participant.id, capsule_id=capsule.id))

        for day, score in zip(range(11, 18), (3, 4, 4, 3, 4, 5, 4), strict=True):
            session.add(MoodEntry(participant_id=participant.id, day=day, score=score))

        session.add_all(
            [
                JournalEntry(
                    participant_id=participant.id,
                    day=14,
                    prompt="What expectation needs a clearer conversation?",
                    answer=(
                        "My sponsor values speed, but the team needs clearer decision rights first."
                    ),
                ),
                JournalEntry(
                    participant_id=participant.id,
                    day=17,
                    prompt="What pattern did you notice this week?",
                    answer="The most useful context travels through informal peer conversations.",
                ),
            ]
        )

    additional_profiles = (
        (
            "demo-amina",
            "Amina Hassan",
            7,
            "focus",
            "remote",
            "Berlin",
            "Europe/Berlin",
            (4, 4, 3, 4, 4, 4, 5),
        ),
        (
            "demo-taylor",
            "Taylor Morgan",
            28,
            "reflection",
            "office",
            "Amsterdam",
            "Europe/Amsterdam",
            (3, 3, 3, 2, 3, 3, 3),
        ),
        (
            "demo-sam",
            "Sam Rivera",
            42,
            "action",
            "hybrid",
            "Madrid",
            "Europe/Madrid",
            (4, 5, 4, 4, 5, 4, 5),
        ),
        (
            "demo-chris",
            "Chris Wong",
            63,
            "focus",
            "remote",
            "Stockholm",
            "Europe/Stockholm",
            (2, 2, 3, 2, 2, 2, 2),
        ),
        (
            "demo-priya",
            "Priya Shah",
            76,
            "reflection",
            "hybrid",
            "Paris",
            "Europe/Paris",
            (4, 4, 4, 5, 4, 5, 5),
        ),
    )
    for (
        external_id,
        name,
        current_day,
        touchpoint,
        work_mode,
        city,
        timezone_name,
        scores,
    ) in additional_profiles:
        profile = session.scalar(select(Participant).where(Participant.external_id == external_id))
        if profile is not None:
            continue
        profile = Participant(
            external_id=external_id,
            name=name,
            email=f"{name.lower().replace(' ', '.')}@example.com",
            role_id=role.id,
            company_context="new" if current_day % 2 else "same",
            city_context="same",
            work_mode=work_mode,
            city=city,
            timezone=timezone_name,
            start_date=date.today() - timedelta(days=current_day - 1),
            current_day=current_day,
            current_touchpoint=touchpoint,
            is_demo=True,
            last_active_at=datetime.now(UTC)
            - timedelta(days=6 if external_id == "demo-chris" else 1),
        )
        session.add(profile)
        session.flush()
        completed = session.scalars(
            select(Capsule).where(
                Capsule.role_id == role.id,
                Capsule.day < current_day,
            )
        ).all()
        for capsule in completed:
            session.add(Completion(participant_id=profile.id, capsule_id=capsule.id))
        start_day = max(current_day - 7, 1)
        for mood_day, score in zip(range(start_day, start_day + 7), scores, strict=True):
            session.add(MoodEntry(participant_id=profile.id, day=mood_day, score=score))

    session.commit()
    session.refresh(participant)
    return participant
