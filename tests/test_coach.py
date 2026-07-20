import asyncio

from app.coach import answer_question
from app.config import Settings
from app.db import SessionFactory
from app.presenter import demo_participant


def test_coach_has_deterministic_offline_fallback() -> None:
    with SessionFactory() as session:
        participant = demo_participant(session)
        answer, model, live = asyncio.run(
            answer_question(
                participant,
                "I keep getting conflicting priorities.",
                settings=Settings(openai_api_key=None),
            )
        )
    assert model == "demo-coach"
    assert live is False
    assert "Read\n" in answer
    assert "Move\n" in answer
    assert "Notice\n" in answer
    assert "within 24" not in answer


def test_coach_api_works_without_external_key(client) -> None:
    response = client.post(
        "/api/v1/demo/coach",
        json={"question": "How do I challenge a decision without damaging trust?"},
    )
    assert response.status_code == 200
    assert response.json()["live_model"] is False
    assert response.json()["answer"].startswith("Read")
