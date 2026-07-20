from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.coach import answer_question
from app.config import get_settings
from app.db import Base, SessionFactory, engine, get_session
from app.domain import complete_capsule
from app.models import Capsule, CityReference, CoachMessage, JournalEntry, MoodEntry
from app.presenter import demo_participant, participant_state, studio_state
from app.schemas import CoachInput, JournalInput, MoodInput, TelegramUpdate
from app.seed import seed_database
from app.telegram import process_telegram_update, send_telegram_message

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    with SessionFactory() as session:
        seed_database(session)
    yield


app = FastAPI(
    title="First 90 API",
    summary="Personalized role-transition journeys for people and teams.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url=None,
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


def _page_context(request: Request, active: str, **extra: object) -> dict[str, object]:
    return {
        "request": request,
        "active": active,
        "demo_mode": settings.demo_mode,
        **extra,
    }


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def landing(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="landing.html",
        context=_page_context(request, "home"),
    )


@app.get("/journey", response_class=HTMLResponse, include_in_schema=False)
def journey(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    state = participant_state(session, demo_participant(session))
    return templates.TemplateResponse(
        request=request,
        name="journey.html",
        context=_page_context(request, "journey", state=state),
    )


@app.get("/studio", response_class=HTMLResponse, include_in_schema=False)
def studio(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    state = studio_state(session)
    return templates.TemplateResponse(
        request=request,
        name="studio.html",
        context=_page_context(request, "studio", state=state),
    )


@app.get("/studio/guide", response_class=HTMLResponse, include_in_schema=False)
def studio_guide(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="studio_guide.html",
        context=_page_context(request, "studio-guide"),
    )


@app.get("/privacy", response_class=HTMLResponse, include_in_schema=False)
def privacy(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="privacy.html",
        context=_page_context(request, "privacy"),
    )


@app.get("/guide", response_class=HTMLResponse, include_in_schema=False)
def participant_guide(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    capsules = session.scalars(
        select(Capsule)
        .where(
            Capsule.day <= 3,
            Capsule.company_filter == "same",
            Capsule.city_filter == "same",
        )
        .order_by(Capsule.day, Capsule.id)
    ).all()
    first_days = []
    for day in range(1, 4):
        day_capsules = [capsule for capsule in capsules if capsule.day == day]
        if day_capsules:
            first_days.append(
                {
                    "day": day,
                    "illustration_path": next(
                        (
                            capsule.illustration_path
                            for capsule in day_capsules
                            if capsule.illustration_path
                        ),
                        None,
                    ),
                    "capsules": day_capsules,
                }
            )
    return templates.TemplateResponse(
        request=request,
        name="participant_guide.html",
        context=_page_context(request, "guide", first_days=first_days),
    )


@app.get("/reviewers", response_class=HTMLResponse, include_in_schema=False)
def reviewer_guide(request: Request) -> HTMLResponse:
    bot_url = (
        f"https://t.me/{settings.telegram_bot_username.lstrip('@')}"
        if settings.telegram_bot_username
        else None
    )
    return templates.TemplateResponse(
        request=request,
        name="reviewer_guide.html",
        context=_page_context(request, "reviewers", bot_url=bot_url),
    )


@app.get("/presentation", response_class=HTMLResponse, include_in_schema=False)
def presentation(request: Request) -> HTMLResponse:
    scene = request.query_params.get("scene", "01")
    phase = request.query_params.get("phase", "evidence")
    if scene not in {"01", "02", "08"}:
        raise HTTPException(status_code=404, detail="Presentation scene not found")
    if phase not in {"evidence", "ending"}:
        raise HTTPException(status_code=404, detail="Presentation phase not found")
    return templates.TemplateResponse(
        request=request,
        name="presentation.html",
        context=_page_context(request, "presentation", scene=scene, phase=phase),
    )


@app.get("/health/live", tags=["operations"])
def live() -> dict[str, str]:
    return {"status": "ok", "service": "first90"}


@app.get("/health/ready", tags=["operations"])
def ready(session: Session = Depends(get_session)) -> JSONResponse:
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse({"status": "not_ready"}, status_code=503)
    return JSONResponse({"status": "ready"})


@app.get("/api/v1/demo/state", tags=["demo"])
def demo_state(session: Session = Depends(get_session)) -> dict[str, object]:
    return participant_state(session, demo_participant(session))


@app.post("/api/v1/demo/reset", tags=["demo"])
def reset_demo(session: Session = Depends(get_session)) -> dict[str, object]:
    if not settings.demo_mode:
        raise HTTPException(status_code=404, detail="Demo mode is disabled")
    participant = seed_database(session, reset_demo=True)
    return participant_state(session, participant)


@app.post("/api/v1/demo/capsules/{capsule_id}/complete", tags=["demo"])
def complete_demo_capsule(
    capsule_id: int, session: Session = Depends(get_session)
) -> dict[str, object]:
    participant = demo_participant(session)
    capsule = session.get(Capsule, capsule_id)
    if capsule is None or capsule.role_id != participant.role_id:
        raise HTTPException(status_code=404, detail="Capsule not found")
    if capsule.day != participant.current_day:
        raise HTTPException(status_code=409, detail="Complete today's journey in order")
    complete_capsule(session, participant, capsule)
    return participant_state(session, participant)


@app.post("/api/v1/demo/mood", tags=["demo"])
def save_mood(payload: MoodInput, session: Session = Depends(get_session)) -> dict[str, object]:
    participant = demo_participant(session)
    entry = session.scalar(
        select(MoodEntry).where(
            MoodEntry.participant_id == participant.id,
            MoodEntry.day == participant.current_day,
        )
    )
    if entry is None:
        session.add(
            MoodEntry(
                participant_id=participant.id,
                day=participant.current_day,
                score=payload.score,
            )
        )
    else:
        entry.score = payload.score
    session.commit()
    return participant_state(session, participant)


@app.post("/api/v1/demo/journal", tags=["demo"])
def save_journal(
    payload: JournalInput, session: Session = Depends(get_session)
) -> dict[str, object]:
    participant = demo_participant(session)
    session.add(
        JournalEntry(
            participant_id=participant.id,
            day=participant.current_day,
            prompt=payload.prompt,
            answer=payload.answer,
        )
    )
    session.commit()
    return participant_state(session, participant)


@app.post("/api/v1/demo/coach", tags=["demo"])
async def ask_coach(
    payload: CoachInput, session: Session = Depends(get_session)
) -> dict[str, object]:
    participant = demo_participant(session)
    answer, model, live_model = await answer_question(participant, payload.question)
    session.add(
        CoachMessage(
            participant_id=participant.id,
            question=payload.question,
            answer=answer,
            model=model,
            live_model=live_model,
        )
    )
    session.commit()
    return {"answer": answer, "model": model, "live_model": live_model}


@app.get("/api/v1/studio/overview", tags=["studio"])
def studio_overview(session: Session = Depends(get_session)) -> dict[str, object]:
    return studio_state(session)


@app.get("/api/v1/reference/cities", tags=["reference"])
def city_references(session: Session = Depends(get_session)) -> list[dict[str, str]]:
    cities = session.scalars(
        select(CityReference).where(CityReference.active.is_(True)).order_by(CityReference.name)
    ).all()
    return [
        {
            "slug": city.slug,
            "name": city.name,
            "country_code": city.country_code,
            "timezone": city.timezone,
        }
        for city in cities
    ]


@app.post("/api/v1/telegram/webhook/{path_secret}", tags=["telegram"])
async def telegram_webhook(
    path_secret: str,
    update: TelegramUpdate,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
    session: Session = Depends(get_session),
) -> dict[str, bool]:
    expected = settings.telegram_webhook_secret
    if path_secret != expected or (
        x_telegram_bot_api_secret_token is not None and x_telegram_bot_api_secret_token != expected
    ):
        raise HTTPException(status_code=404, detail="Not found")
    result = process_telegram_update(session, update, base_url=settings.app_base_url)
    if result and settings.telegram_bot_token:
        chat_id, reply = result
        await send_telegram_message(settings.telegram_bot_token, chat_id, reply)
    return {"ok": True}
