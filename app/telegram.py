from __future__ import annotations

import json
from datetime import date

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain import capsules_for_day, studio_metrics
from app.models import (
    Capsule,
    CityReference,
    JournalEntry,
    MoodEntry,
    Participant,
    Role,
    TelegramOnboarding,
)
from app.schemas import TelegramUpdate


async def send_telegram_message(token: str, chat_id: int, text: str) -> bool:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "protect_content": True},
        )
    return response.is_success


def _message_fields(update: TelegramUpdate) -> tuple[int, str, str, str] | None:
    if update.message is None:
        return None
    chat = update.message.get("chat")
    sender = update.message.get("from")
    text = update.message.get("text")
    if not isinstance(chat, dict) or not isinstance(sender, dict) or not isinstance(text, str):
        return None
    chat_id = chat.get("id")
    if not isinstance(chat_id, int):
        return None
    name = sender.get("first_name")
    chat_type = str(chat.get("type") or "private")
    return chat_id, str(name or "there"), text.strip(), chat_type


def _participant(session: Session, chat_id: int) -> Participant | None:
    return session.scalar(select(Participant).where(Participant.external_id == f"tg:{chat_id}"))


def _onboarding(session: Session, chat_id: int) -> TelegramOnboarding | None:
    return session.scalar(
        select(TelegramOnboarding).where(
            TelegramOnboarding.external_id == f"tg-onboarding:{chat_id}"
        )
    )


def _start_onboarding(session: Session, chat_id: int, telegram_name: str) -> str:
    state = _onboarding(session, chat_id)
    if state is None:
        state = TelegramOnboarding(
            external_id=f"tg-onboarding:{chat_id}",
            chat_id=str(chat_id),
            telegram_name=telegram_name,
        )
        session.add(state)
    else:
        state.telegram_name = telegram_name
        state.step = "name"
        state.payload_json = "{}"
    session.commit()
    return (
        "Welcome to First 90. I will set up your free transition journey in six short steps.\n\n"
        "Step 1 of 6 · Name\nWhat name should I use for you?\n\nSend /cancel to stop."
    )


def _payload(state: TelegramOnboarding) -> dict[str, str]:
    try:
        value = json.loads(state.payload_json)
    except json.JSONDecodeError:
        return {}
    return {str(key): str(item) for key, item in value.items()} if isinstance(value, dict) else {}


def _save_step(
    session: Session,
    state: TelegramOnboarding,
    payload: dict[str, str],
    *,
    step: str,
) -> None:
    state.payload_json = json.dumps(payload, sort_keys=True)
    state.step = step
    session.commit()


def _city_prompt(session: Session) -> str:
    cities = session.scalars(
        select(CityReference.name)
        .where(CityReference.active.is_(True))
        .order_by(CityReference.name)
    ).all()
    return ", ".join(cities)


def _finish_onboarding(
    session: Session,
    state: TelegramOnboarding,
    payload: dict[str, str],
    work_mode: str,
) -> Participant:
    role = session.scalar(select(Role).where(Role.slug == payload["role_slug"]))
    city = session.scalar(
        select(CityReference).where(
            func.lower(CityReference.name) == payload["city"].lower(),
            CityReference.active.is_(True),
        )
    )
    if role is None or city is None:
        raise LookupError("Onboarding references are not seeded")
    participant = Participant(
        external_id=f"tg:{state.chat_id}",
        name=payload["name"],
        role_id=role.id,
        company_context=payload["company_context"],
        city_context=payload["city_context"],
        work_mode=work_mode,
        city=city.name,
        timezone=city.timezone,
        start_date=date.today(),
        current_day=1,
    )
    session.add(participant)
    session.delete(state)
    session.commit()
    session.refresh(participant)
    return participant


def _onboarding_reply(
    session: Session,
    state: TelegramOnboarding,
    text: str,
) -> tuple[str, Participant | None]:
    value = text.strip()
    payload = _payload(state)

    if state.step == "name":
        if not 2 <= len(value) <= 80 or value.startswith("/"):
            return "Please send a name between 2 and 80 characters.", None
        payload["name"] = value
        _save_step(session, state, payload, step="role")
        return (
            "Step 2 of 6 · Role\nEarly access currently supports People Manager. "
            "Reply People Manager to continue.",
            None,
        )

    if state.step == "role":
        if value.casefold() not in {"people manager", "manager", "1"}:
            return "Current content supports People Manager. Reply People Manager.", None
        payload["role_slug"] = "people-manager"
        _save_step(session, state, payload, step="company")
        return (
            "Step 3 of 6 · Company context\nAre you moving within the same company or "
            "joining a new company? Reply same or new.",
            None,
        )

    if state.step == "company":
        company = value.casefold()
        if company not in {"same", "new"}:
            return "Reply same or new.", None
        payload["company_context"] = company
        _save_step(session, state, payload, step="city_context")
        return (
            "Step 4 of 6 · City context\nAre you staying in the same city or moving to a "
            "new city? Reply same or new.",
            None,
        )

    if state.step == "city_context":
        city_context = value.casefold()
        if city_context not in {"same", "new"}:
            return "Reply same or new.", None
        payload["city_context"] = city_context
        _save_step(session, state, payload, step="city")
        return (
            f"Step 5 of 6 · City\nReply with one supported European city:\n{_city_prompt(session)}",
            None,
        )

    if state.step == "city":
        city = session.scalar(
            select(CityReference).where(
                func.lower(CityReference.name) == value.lower(),
                CityReference.active.is_(True),
            )
        )
        if city is None:
            return f"Choose one supported city:\n{_city_prompt(session)}", None
        payload["city"] = city.name
        _save_step(session, state, payload, step="work_mode")
        return (
            "Step 6 of 6 · Work mode\nHow will you work most often? Reply office, hybrid, "
            "or remote.",
            None,
        )

    if state.step == "work_mode":
        work_mode = value.casefold()
        if work_mode not in {"office", "hybrid", "remote"}:
            return "Reply office, hybrid, or remote.", None
        participant = _finish_onboarding(session, state, payload, work_mode)
        capsules = capsules_for_day(session, participant, 1)
        first = capsules[0] if capsules else None
        first_move = (
            f"\n\nYour first focus: {first.title}\n{first.body}\n\n{first.prompt}" if first else ""
        )
        return (
            f"You are ready, {participant.name}. Day 1 starts now.{first_move}\n\n"
            "Commands: /today, /mood 1-5, /pause, /web. Plain text is saved to your "
            "private journal.",
            participant,
        )

    state.step = "name"
    state.payload_json = "{}"
    session.commit()
    return "Let us restart. Step 1 of 6 · What name should I use for you?", None


def _admin_reply(session: Session, command: str, argument: str, base_url: str) -> str:
    if command in {"/start", "/admin"}:
        return (
            "First 90 reviewer admin chat · fictional demo data only.\n\n"
            "Commands: /metrics, /roles, /preview 1, /preview 2, /preview 3, /privacy\n\n"
            f"Team Studio: {base_url}/studio\nReviewer guide: {base_url}/reviewers\n\n"
            "To try the participant journey, open the bot privately and send /start."
        )
    if command == "/metrics":
        metrics = studio_metrics(session)
        return (
            "Demo journey health\n"
            f"Participants: {metrics['participants']}\n"
            f"Active: {metrics['active']}\n"
            f"Completed touchpoints: {metrics['completions']}\n"
            f"Average energy: {metrics['average_mood']}\n\n"
            "Use Team Studio for the full aggregate view."
        )
    if command == "/roles":
        return (
            "Content-ready role: People Manager.\n"
            "Journey: 90 days, 270 universal touchpoints.\n"
            "Personalization: same/new company, same/new city, office/hybrid/remote.\n"
            "Days 1-3 include enhanced same-company, same-city manager content."
        )
    if command == "/privacy":
        return (
            "Admin visibility: program day, progress, activity, pause state, role, city, work "
            "mode, and consented energy pattern.\n\nPrivate: journal text, AI coach questions and "
            "answers, personal notes, and raw Telegram messages."
        )
    if command == "/preview":
        try:
            day = int(argument)
        except ValueError:
            day = 0
        if day not in {1, 2, 3}:
            return "Use /preview 1, /preview 2, or /preview 3."
        role = session.scalar(select(Role).where(Role.slug == "people-manager"))
        capsules = (
            session.scalars(
                select(Capsule)
                .where(
                    Capsule.role_id == role.id if role else False,
                    Capsule.day == day,
                    Capsule.company_filter == "same",
                    Capsule.city_filter == "same",
                )
                .order_by(Capsule.id)
            ).all()
            if role
            else []
        )
        if not capsules:
            return "Preview content is unavailable."
        parts = [f"Day {day} preview · People Manager · same company · same city"]
        for capsule in capsules:
            resource = (
                f"\n{capsule.resource_kind}: {capsule.resource_url}" if capsule.resource_url else ""
            )
            parts.append(
                f"{capsule.touchpoint.upper()} · {capsule.title}\n{capsule.prompt}{resource}"
            )
        return "\n\n".join(parts)
    return "Commands: /admin, /metrics, /roles, /preview 1, /preview 2, /preview 3, /privacy"


def process_telegram_update(
    session: Session, update: TelegramUpdate, *, base_url: str
) -> tuple[int, str] | None:
    fields = _message_fields(update)
    if fields is None:
        return None
    chat_id, telegram_name, text, chat_type = fields
    command, _, argument = text.partition(" ")
    command = command.lower().split("@", 1)[0]

    if chat_type in {"group", "supergroup"}:
        return chat_id, _admin_reply(session, command, argument.strip(), base_url)

    participant = _participant(session, chat_id)
    state = _onboarding(session, chat_id)

    if command == "/cancel" and state is not None:
        session.delete(state)
        session.commit()
        return chat_id, "Onboarding cancelled. Send /start whenever you are ready."
    if command == "/start" and participant is None:
        return chat_id, _start_onboarding(session, chat_id, telegram_name)
    if state is not None and participant is None:
        reply, participant = _onboarding_reply(session, state, text)
        return chat_id, reply
    if participant is None:
        return chat_id, "Send /start to create your free First 90 journey."

    if command == "/start":
        reply = (
            f"Welcome back, {participant.name}. Your journey is ready.\n\n"
            "Commands: /today, /mood 1-5, /pause, /web"
        )
    elif command == "/web":
        reply = (
            f"Open the optional web companion: {base_url}/journey\n\n"
            "The public Build Week web demo uses fictional sample data; your personal journey "
            "continues here in Telegram."
        )
    elif command == "/today":
        capsules = capsules_for_day(session, participant, participant.current_day)
        current = next(
            (item for item in capsules if item.touchpoint == participant.current_touchpoint),
            capsules[0] if capsules else None,
        )
        resource = (
            f"\n\n{current.resource_kind}: {current.resource_title}\n{current.resource_url}"
            if current and current.resource_url
            else ""
        )
        reply = (
            f"Day {participant.current_day} · {current.title}\n\n{current.body}\n\n"
            f"{current.prompt}{resource}"
            if current
            else "Today's guidance is being prepared."
        )
    elif command == "/mood":
        try:
            score = int(argument)
        except ValueError:
            score = 0
        if not 1 <= score <= 5:
            reply = "Use /mood followed by a number from 1 to 5."
        else:
            existing = session.scalar(
                select(MoodEntry).where(
                    MoodEntry.participant_id == participant.id,
                    MoodEntry.day == participant.current_day,
                )
            )
            if existing:
                existing.score = score
            else:
                session.add(
                    MoodEntry(
                        participant_id=participant.id,
                        day=participant.current_day,
                        score=score,
                    )
                )
            session.commit()
            reply = "Mood saved. Small signals become useful patterns over time."
    elif command == "/pause":
        participant.paused = not participant.paused
        session.commit()
        reply = "Journey paused." if participant.paused else "Journey resumed."
    elif text.startswith("/"):
        reply = "Commands: /today, /mood 1-5, /pause, /web"
    else:
        session.add(
            JournalEntry(
                participant_id=participant.id,
                day=participant.current_day,
                prompt="Telegram reflection",
                answer=text,
            )
        )
        session.commit()
        reply = "Saved to your private journal."
    return chat_id, reply
