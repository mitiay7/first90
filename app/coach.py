from __future__ import annotations

import hashlib

from openai import AsyncOpenAI

from app.config import Settings, get_settings
from app.models import Participant

COACH_INSTRUCTIONS = """You are First 90, a practical transition coach for people entering
a new role.
Give workplace guidance, not therapy or legal advice. Use the supplied role context but never invent
facts about the user's company or colleagues. State the useful conclusion first. Return 3 short
sections titled Read, Move, and Notice. Include one action that can be completed within 24 hours.
Keep the full answer under 170 words. Do not use generic praise or a sign-off."""


def _safety_identifier(participant: Participant) -> str:
    return hashlib.sha256(f"first90:{participant.external_id}".encode()).hexdigest()[:32]


def _fallback_answer(participant: Participant, question: str) -> str:
    concern = question.rstrip("?.!")
    return (
        "Read\n"
        f"At day {participant.current_day}, uncertainty about {concern.lower()} is useful data, "
        "not a "
        "verdict. Separate what you observed from the story you are telling about it.\n\n"
        "Move\n"
        'Ask one trusted stakeholder: "What would good progress look like by the end of this '
        'month?" Write their answer next to your current assumption and choose one reversible '
        "next step.\n\n"
        "Notice\n"
        "Look for repeated evidence across two or more conversations before changing direction."
    )


async def answer_question(
    participant: Participant,
    question: str,
    *,
    settings: Settings | None = None,
) -> tuple[str, str, bool]:
    current_settings = settings or get_settings()
    if not current_settings.openai_api_key:
        return _fallback_answer(participant, question), "demo-coach", False

    client = AsyncOpenAI(api_key=current_settings.openai_api_key)
    context = (
        f"Role: {participant.role.title}\n"
        f"Program day: {participant.current_day}/90\n"
        f"Company context: {participant.company_context}\n"
        f"City context: {participant.city_context}\n"
        f"Work mode: {participant.work_mode}\n\n"
        f"Question: {question}"
    )
    try:
        response = await client.responses.create(
            model=current_settings.openai_model,
            reasoning={"effort": "low"},
            instructions=COACH_INSTRUCTIONS,
            input=context,
            max_output_tokens=500,
            safety_identifier=_safety_identifier(participant),
            store=False,
            text={"verbosity": "low"},
        )
    except Exception:
        return _fallback_answer(participant, question), "demo-coach", False
    text = response.output_text.strip()
    if not text:
        return _fallback_answer(participant, question), "demo-coach", False
    return text, response.model, True
