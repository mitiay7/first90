from sqlalchemy import select

from app.db import SessionFactory
from app.models import JournalEntry, Participant
from app.schemas import TelegramUpdate
from app.telegram import process_telegram_update


def update(text: str, *, chat_type: str = "private") -> TelegramUpdate:
    return TelegramUpdate(
        update_id=1,
        message={
            "chat": {"id": 998877, "type": chat_type},
            "from": {"id": 998877, "first_name": "Morgan"},
            "text": text,
        },
    )


def send(session, text: str, *, chat_type: str = "private") -> str:
    result = process_telegram_update(
        session,
        update(text, chat_type=chat_type),
        base_url="https://demo",
    )
    assert result is not None
    return result[1]


def complete_onboarding(session) -> str:
    assert "Step 1 of 6" in send(session, "/start")
    assert "Step 2 of 6" in send(session, "Morgan Lee")
    assert "Step 3 of 6" in send(session, "People Manager")
    assert "Step 4 of 6" in send(session, "same")
    assert "Step 5 of 6" in send(session, "same")
    assert "Step 6 of 6" in send(session, "Riga")
    return send(session, "hybrid")


def test_private_telegram_onboarding_creates_tailored_day_one() -> None:
    with SessionFactory() as session:
        finished = complete_onboarding(session)
        participant = session.scalar(
            select(Participant).where(Participant.external_id == "tg:998877")
        )
        today = send(session, "/today")

    assert participant is not None
    assert participant.name == "Morgan Lee"
    assert participant.company_context == "same"
    assert participant.city_context == "same"
    assert participant.city == "Riga"
    assert participant.timezone == "Europe/Riga"
    assert "Day 1 starts now" in finished
    assert "Name the identity shift" in finished
    assert "Day 1" in today
    assert "ccl.org" in today


def test_private_chat_requires_start_and_validates_city() -> None:
    with SessionFactory() as session:
        assert send(session, "Hello") == "Send /start to create your free First 90 journey."
        send(session, "/start")
        send(session, "Morgan Lee")
        send(session, "People Manager")
        send(session, "same")
        send(session, "same")
        invalid = send(session, "New York")
    assert "Choose one supported city" in invalid
    assert "Berlin" in invalid
    assert "Riga" in invalid


def test_telegram_mood_and_private_journal_after_onboarding() -> None:
    with SessionFactory() as session:
        complete_onboarding(session)
        mood = send(session, "/mood 4")
        journal = send(session, "I need to clarify ownership.")
        entry = session.scalar(
            select(JournalEntry).where(JournalEntry.answer == "I need to clarify ownership.")
        )
    assert mood.startswith("Mood saved")
    assert journal == "Saved to your private journal."
    assert entry is not None and entry.answer == "I need to clarify ownership."


def test_group_admin_chat_exposes_preview_but_stores_no_journal() -> None:
    with SessionFactory() as session:
        admin = send(session, "/admin", chat_type="supergroup")
        roles = send(session, "/roles", chat_type="supergroup")
        preview = send(session, "/preview 1", chat_type="supergroup")
        plain = send(session, "group note", chat_type="supergroup")
        journal_count = len(session.scalars(select(JournalEntry)).all())
    assert "reviewer admin chat" in admin
    assert "People Manager" in roles
    assert "Name the identity shift" in preview
    assert "ccl.org" in preview
    assert plain.startswith("Commands:")
    assert journal_count == 2
