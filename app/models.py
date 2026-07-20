from __future__ import annotations

from datetime import UTC, date, datetime
from enum import StrEnum

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class CompanyContext(StrEnum):
    SAME = "same"
    NEW = "new"


class CityContext(StrEnum):
    SAME = "same"
    NEW = "new"


class WorkMode(StrEnum):
    OFFICE = "office"
    HYBRID = "hybrid"
    REMOTE = "remote"


class Touchpoint(StrEnum):
    FOCUS = "focus"
    ACTION = "action"
    REFLECTION = "reflection"


class CityReference(Base):
    __tablename__ = "city_references"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    country_code: Mapped[str] = mapped_column(String(2))
    timezone: Mapped[str] = mapped_column(String(80))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    participants: Mapped[list[Participant]] = relationship(back_populates="role")
    capsules: Mapped[list[Capsule]] = relationship(back_populates="role")


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str] = mapped_column(String(120), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    company_context: Mapped[str] = mapped_column(String(20))
    city_context: Mapped[str] = mapped_column(String(20))
    work_mode: Mapped[str] = mapped_column(String(20))
    city: Mapped[str] = mapped_column(String(120), default="Riga")
    timezone: Mapped[str] = mapped_column(String(80), default="Europe/Riga")
    start_date: Mapped[date] = mapped_column(Date)
    current_day: Mapped[int] = mapped_column(Integer, default=1)
    current_touchpoint: Mapped[str] = mapped_column(String(20), default=Touchpoint.FOCUS.value)
    paused: Mapped[bool] = mapped_column(Boolean, default=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    last_active_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    role: Mapped[Role] = relationship(back_populates="participants")
    completions: Mapped[list[Completion]] = relationship(
        back_populates="participant", cascade="all, delete-orphan"
    )
    moods: Mapped[list[MoodEntry]] = relationship(
        back_populates="participant", cascade="all, delete-orphan"
    )
    journal_entries: Mapped[list[JournalEntry]] = relationship(
        back_populates="participant", cascade="all, delete-orphan"
    )
    coach_messages: Mapped[list[CoachMessage]] = relationship(
        back_populates="participant", cascade="all, delete-orphan"
    )


class Capsule(Base):
    __tablename__ = "capsules"
    __table_args__ = (
        UniqueConstraint(
            "role_id",
            "day",
            "touchpoint",
            "company_filter",
            "city_filter",
            "work_mode_filter",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    day: Mapped[int] = mapped_column(Integer)
    touchpoint: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(160))
    eyebrow: Mapped[str] = mapped_column(String(120))
    body: Mapped[str] = mapped_column(Text)
    prompt: Mapped[str] = mapped_column(Text)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=5)
    illustration_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resource_title: Mapped[str | None] = mapped_column(String(180), nullable=True)
    resource_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    resource_kind: Mapped[str | None] = mapped_column(String(20), nullable=True)
    company_filter: Mapped[str] = mapped_column(String(20), default="any")
    city_filter: Mapped[str] = mapped_column(String(20), default="any")
    work_mode_filter: Mapped[str] = mapped_column(String(20), default="any")
    published: Mapped[bool] = mapped_column(Boolean, default=True)

    role: Mapped[Role] = relationship(back_populates="capsules")
    completions: Mapped[list[Completion]] = relationship(back_populates="capsule")


class Completion(Base):
    __tablename__ = "completions"
    __table_args__ = (UniqueConstraint("participant_id", "capsule_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey("participants.id"))
    capsule_id: Mapped[int] = mapped_column(ForeignKey("capsules.id"))
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    participant: Mapped[Participant] = relationship(back_populates="completions")
    capsule: Mapped[Capsule] = relationship(back_populates="completions")


class MoodEntry(Base):
    __tablename__ = "mood_entries"
    __table_args__ = (UniqueConstraint("participant_id", "day"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey("participants.id"))
    day: Mapped[int] = mapped_column(Integer)
    score: Mapped[int] = mapped_column(Integer)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    participant: Mapped[Participant] = relationship(back_populates="moods")


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey("participants.id"))
    day: Mapped[int] = mapped_column(Integer)
    prompt: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    participant: Mapped[Participant] = relationship(back_populates="journal_entries")


class CoachMessage(Base):
    __tablename__ = "coach_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey("participants.id"))
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(80))
    live_model: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    participant: Mapped[Participant] = relationship(back_populates="coach_messages")


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (UniqueConstraint("participant_id", "day", "touchpoint"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey("participants.id"))
    day: Mapped[int] = mapped_column(Integer)
    touchpoint: Mapped[str] = mapped_column(String(20))
    channel: Mapped[str] = mapped_column(String(20), default="telegram")
    status: Mapped[str] = mapped_column(String(20), default="sent")
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class TelegramOnboarding(Base):
    __tablename__ = "telegram_onboarding"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str] = mapped_column(String(120), unique=True)
    chat_id: Mapped[str] = mapped_column(String(40))
    telegram_name: Mapped[str] = mapped_column(String(120))
    step: Mapped[str] = mapped_column(String(40), default="name")
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
