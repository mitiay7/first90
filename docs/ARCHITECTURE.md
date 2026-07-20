# Architecture

First 90 uses a small modular monolith plus an independent delivery worker. This keeps the demo easy to run while preserving production boundaries.

## Runtime

```text
Browser / Telegram
        |
   Caddy gateway
        |
   FastAPI web/API ---- OpenAI Responses API
        |
     PostgreSQL
        |
  Delivery worker ---- Telegram Bot API
```

## Boundaries

- `domain.py` owns deterministic journey rules. It has no web or OpenAI dependency.
- `coach.py` owns the GPT‑5.6 request contract and fallback behavior.
- `telegram.py` owns six-step participant onboarding, private journey commands, and privacy-safe reviewer group commands.
- `presenter.py` exposes privacy-safe participant and team views.
- `worker.py` delivers the active touchpoint at timezone-aware local hours.

## Privacy model

Participant views may read their journal and coach history. Team Studio receives only progress, activity, and consented mood scores. No team endpoint serializes journal text or coach conversations.

## Personalization

Each capsule may filter on company context, city context, and work mode. Selection chooses the most specific matching capsule for each daily touchpoint, then falls back to `any` content. Role and day are always exact.

The People Manager journey has 270 universal capsules. Days 1–3 add nine reviewed capsules for a same-company, same-city transition, each with an external learning resource and one original illustration per day.
