from sqlalchemy import func, select

from app.db import SessionFactory
from app.domain import capsules_for_day, complete_capsule, phase_for_day
from app.models import Capsule, Completion
from app.presenter import demo_participant


def test_phase_boundaries() -> None:
    assert phase_for_day(1).name == "Listen & orient"
    assert phase_for_day(30).number == 1
    assert phase_for_day(31).name == "Align & deliver"
    assert phase_for_day(61).name == "Scale & sustain"
    assert phase_for_day(90).number == 3


def test_seed_has_complete_role_coverage() -> None:
    with SessionFactory() as session:
        universal = session.scalar(
            select(func.count(Capsule.id)).where(
                Capsule.company_filter == "any",
                Capsule.city_filter == "any",
                Capsule.work_mode_filter == "any",
            )
        )
        total = session.scalar(select(func.count(Capsule.id)))
        assert universal == 270
        assert total == 279


def test_same_company_same_city_manager_gets_enhanced_first_days() -> None:
    with SessionFactory() as session:
        participant = demo_participant(session)
        participant.company_context = "same"
        participant.city_context = "same"
        participant.current_day = 1
        session.commit()
        capsules = capsules_for_day(session, participant, 1)
    assert [capsule.title for capsule in capsules] == [
        "Name the identity shift",
        "Draft a stop-doing list",
        "Catch the expert reflex",
    ]
    assert capsules[0].illustration_path.endswith("day-01-identity-shift.webp")
    assert all(capsule.resource_url for capsule in capsules)


def test_specific_capsule_beats_generic_fallback() -> None:
    with SessionFactory() as session:
        participant = demo_participant(session)
        session.add(
            Capsule(
                role_id=participant.role_id,
                day=18,
                touchpoint="action",
                title="New-company stakeholder map",
                eyebrow="Tailored",
                body="Tailored body",
                prompt="Tailored prompt",
                company_filter="new",
                city_filter="any",
                work_mode_filter="any",
            )
        )
        session.commit()
        capsules = capsules_for_day(session, participant, 18)
        action = next(item for item in capsules if item.touchpoint == "action")
        assert action.title == "New-company stakeholder map"


def test_completion_is_idempotent_and_advances_once() -> None:
    with SessionFactory() as session:
        participant = demo_participant(session)
        action = next(
            item
            for item in capsules_for_day(session, participant, 18)
            if item.touchpoint == "action"
        )
        before = session.scalar(select(func.count(Completion.id))) or 0
        complete_capsule(session, participant, action)
        complete_capsule(session, participant, action)
        after = session.scalar(select(func.count(Completion.id))) or 0
        assert after == before + 1
        assert participant.current_day == 18
        assert participant.current_touchpoint == "reflection"
