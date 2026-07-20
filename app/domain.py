from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Capsule,
    Completion,
    MoodEntry,
    Participant,
    Touchpoint,
)

TOUCHPOINT_ORDER = [Touchpoint.FOCUS.value, Touchpoint.ACTION.value, Touchpoint.REFLECTION.value]


@dataclass(frozen=True)
class Phase:
    number: int
    name: str
    promise: str


PHASES = (
    Phase(1, "Listen & orient", "Build context before making big moves."),
    Phase(2, "Align & deliver", "Turn insight into visible, trusted progress."),
    Phase(3, "Scale & sustain", "Build systems that keep working without heroics."),
)


def phase_for_day(day: int) -> Phase:
    if not 1 <= day <= 90:
        raise ValueError("day must be between 1 and 90")
    return PHASES[min((day - 1) // 30, 2)]


def progress_percent(day: int, touchpoint: str) -> int:
    completed_days = max(day - 1, 0)
    completed_today = TOUCHPOINT_ORDER.index(touchpoint)
    return round(((completed_days * 3 + completed_today) / 270) * 100)


def _matches(value: str, filter_value: str) -> bool:
    return filter_value == "any" or value == filter_value


def _specificity(capsule: Capsule) -> int:
    return sum(
        value != "any"
        for value in (
            capsule.company_filter,
            capsule.city_filter,
            capsule.work_mode_filter,
        )
    )


def capsules_for_day(session: Session, participant: Participant, day: int) -> list[Capsule]:
    candidates = session.scalars(
        select(Capsule).where(
            Capsule.role_id == participant.role_id,
            Capsule.day == day,
            Capsule.published.is_(True),
        )
    ).all()
    selected: dict[str, Capsule] = {}
    for capsule in sorted(candidates, key=_specificity, reverse=True):
        if capsule.touchpoint in selected:
            continue
        if not _matches(participant.company_context, capsule.company_filter):
            continue
        if not _matches(participant.city_context, capsule.city_filter):
            continue
        if not _matches(participant.work_mode, capsule.work_mode_filter):
            continue
        selected[capsule.touchpoint] = capsule
    return [selected[key] for key in TOUCHPOINT_ORDER if key in selected]


def complete_capsule(
    session: Session, participant: Participant, capsule: Capsule
) -> tuple[int, str]:
    existing = session.scalar(
        select(Completion).where(
            Completion.participant_id == participant.id,
            Completion.capsule_id == capsule.id,
        )
    )
    if existing is None:
        session.add(Completion(participant_id=participant.id, capsule_id=capsule.id))

    current_index = TOUCHPOINT_ORDER.index(participant.current_touchpoint)
    capsule_index = TOUCHPOINT_ORDER.index(capsule.touchpoint)
    if capsule.day == participant.current_day and capsule_index >= current_index:
        if capsule_index == len(TOUCHPOINT_ORDER) - 1:
            participant.current_day = min(participant.current_day + 1, 90)
            participant.current_touchpoint = Touchpoint.FOCUS.value
        else:
            participant.current_touchpoint = TOUCHPOINT_ORDER[capsule_index + 1]
    participant.last_active_at = datetime.now(UTC)
    session.commit()
    return participant.current_day, participant.current_touchpoint


def mood_average(session: Session, participant_id: int, limit: int = 7) -> float | None:
    scores = session.scalars(
        select(MoodEntry.score)
        .where(MoodEntry.participant_id == participant_id)
        .order_by(MoodEntry.day.desc())
        .limit(limit)
    ).all()
    return round(sum(scores) / len(scores), 1) if scores else None


def risk_label(session: Session, participant: Participant) -> str:
    average = mood_average(session, participant.id)
    last_active_at = participant.last_active_at
    if last_active_at.tzinfo is None:
        last_active_at = last_active_at.replace(tzinfo=UTC)
    days_inactive = (datetime.now(UTC) - last_active_at).days
    if (average is not None and average < 2.8) or days_inactive >= 5:
        return "Needs attention"
    if (average is not None and average < 3.5) or days_inactive >= 3:
        return "Watch"
    return "On track"


def studio_metrics(session: Session) -> dict[str, int | float]:
    participants = session.scalar(select(func.count(Participant.id))) or 0
    active = (
        session.scalar(select(func.count(Participant.id)).where(Participant.paused.is_(False))) or 0
    )
    completions = session.scalar(select(func.count(Completion.id))) or 0
    moods = session.scalars(select(MoodEntry.score)).all()
    average_mood = round(sum(moods) / len(moods), 1) if moods else 0.0
    return {
        "participants": participants,
        "active": active,
        "completions": completions,
        "average_mood": average_mood,
    }
