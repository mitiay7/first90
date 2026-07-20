from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain import capsules_for_day, phase_for_day, progress_percent, risk_label, studio_metrics
from app.models import CoachMessage, Completion, JournalEntry, MoodEntry, Participant


def demo_participant(session: Session) -> Participant:
    participant = session.scalar(
        select(Participant).where(Participant.external_id == "demo-jordan")
    )
    if participant is None:
        raise LookupError("Demo participant is not seeded")
    return participant


def participant_state(session: Session, participant: Participant) -> dict[str, object]:
    capsules = capsules_for_day(session, participant, participant.current_day)
    completed_ids = set(
        session.scalars(
            select(Completion.capsule_id).where(Completion.participant_id == participant.id)
        ).all()
    )
    moods = session.scalars(
        select(MoodEntry)
        .where(MoodEntry.participant_id == participant.id)
        .order_by(MoodEntry.day.desc())
        .limit(14)
    ).all()
    journals = session.scalars(
        select(JournalEntry)
        .where(JournalEntry.participant_id == participant.id)
        .order_by(JournalEntry.created_at.desc())
        .limit(5)
    ).all()
    messages = session.scalars(
        select(CoachMessage)
        .where(CoachMessage.participant_id == participant.id)
        .order_by(CoachMessage.created_at.desc())
        .limit(3)
    ).all()
    phase = phase_for_day(participant.current_day)
    return {
        "participant": {
            "id": participant.id,
            "name": participant.name,
            "first_name": participant.name.split()[0],
            "role": participant.role.title,
            "day": participant.current_day,
            "touchpoint": participant.current_touchpoint,
            "paused": participant.paused,
            "company_context": participant.company_context,
            "city_context": participant.city_context,
            "work_mode": participant.work_mode,
            "city": participant.city,
        },
        "phase": {
            "number": phase.number,
            "name": phase.name,
            "promise": phase.promise,
        },
        "progress": progress_percent(participant.current_day, participant.current_touchpoint),
        "capsules": [
            {
                "id": capsule.id,
                "touchpoint": capsule.touchpoint,
                "title": capsule.title,
                "eyebrow": capsule.eyebrow,
                "body": capsule.body,
                "prompt": capsule.prompt,
                "duration_minutes": capsule.duration_minutes,
                "illustration_path": capsule.illustration_path,
                "resource_title": capsule.resource_title,
                "resource_url": capsule.resource_url,
                "resource_kind": capsule.resource_kind,
                "completed": capsule.id in completed_ids,
                "current": capsule.touchpoint == participant.current_touchpoint,
            }
            for capsule in capsules
        ],
        "moods": [
            {"day": mood.day, "score": mood.score}
            for mood in sorted(moods, key=lambda item: item.day)
        ],
        "journals": [
            {"day": entry.day, "prompt": entry.prompt, "answer": entry.answer} for entry in journals
        ],
        "coach_messages": [
            {
                "question": message.question,
                "answer": message.answer,
                "model": message.model,
                "live_model": message.live_model,
            }
            for message in messages
        ],
    }


def studio_state(session: Session) -> dict[str, object]:
    participants = session.scalars(
        select(Participant).order_by(Participant.current_day.desc())
    ).all()
    return {
        "metrics": studio_metrics(session),
        "participants": [
            {
                "id": participant.id,
                "name": participant.name,
                "role": participant.role.title,
                "day": participant.current_day,
                "progress": progress_percent(
                    participant.current_day, participant.current_touchpoint
                ),
                "risk": risk_label(session, participant),
                "paused": participant.paused,
                "work_mode": participant.work_mode,
                "city": participant.city,
            }
            for participant in participants
        ],
    }
