from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select

from app.config import get_settings
from app.db import Base, SessionFactory, engine
from app.domain import capsules_for_day
from app.models import Notification, Participant
from app.seed import seed_database
from app.telegram import send_telegram_message

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("first90.worker")

DELIVERY_HOURS = {"focus": 9, "action": 13, "reflection": 18}


async def run_delivery_tick() -> int:
    settings = get_settings()
    if not settings.telegram_bot_token:
        return 0
    sent = 0
    with SessionFactory() as session:
        participants = session.scalars(
            select(Participant).where(
                Participant.external_id.like("tg:%"), Participant.paused.is_(False)
            )
        ).all()
        for participant in participants:
            try:
                local_now = datetime.now(ZoneInfo(participant.timezone))
            except ZoneInfoNotFoundError:
                local_now = datetime.now(ZoneInfo("UTC"))
            expected_hour = DELIVERY_HOURS[participant.current_touchpoint]
            if local_now.hour != expected_hour:
                continue
            existing = session.scalar(
                select(Notification).where(
                    Notification.participant_id == participant.id,
                    Notification.day == participant.current_day,
                    Notification.touchpoint == participant.current_touchpoint,
                )
            )
            if existing is not None:
                continue
            capsules = capsules_for_day(session, participant, participant.current_day)
            capsule = next(
                (item for item in capsules if item.touchpoint == participant.current_touchpoint),
                None,
            )
            if capsule is None:
                continue
            chat_id = int(participant.external_id.removeprefix("tg:"))
            message = (
                f"Day {participant.current_day} · {capsule.title}\n\n"
                f"{capsule.body}\n\n{capsule.prompt}"
            )
            delivered = await send_telegram_message(settings.telegram_bot_token, chat_id, message)
            session.add(
                Notification(
                    participant_id=participant.id,
                    day=participant.current_day,
                    touchpoint=participant.current_touchpoint,
                    status="sent" if delivered else "failed",
                )
            )
            session.commit()
            sent += int(delivered)
    return sent


async def run() -> None:
    Base.metadata.create_all(engine)
    with SessionFactory() as session:
        seed_database(session)
    logger.info("First 90 delivery worker started")
    while True:
        try:
            sent = await run_delivery_tick()
            if sent:
                logger.info("Delivered %s Telegram touchpoints", sent)
        except Exception:
            logger.exception("Delivery tick failed")
        await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(run())
