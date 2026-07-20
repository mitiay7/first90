# First 90

First 90 is a personalized transition companion for people starting a new role. It turns an ambiguous 90-day change into three small daily touchpoints: focus, action, and reflection.

Built for the **Work & Productivity** track of OpenAI Build Week 2026.

## Live demo

- Participant journey: `https://first90.hub.lea-dev.site/journey`
- Team Studio: `https://first90-studio.hub.lea-dev.site/studio`
- Admin guide: `https://first90-studio.hub.lea-dev.site/studio/guide`
- Participant guide: `https://first90.hub.lea-dev.site/guide`
- Reviewer guide: `https://first90.hub.lea-dev.site/reviewers`
- API documentation: `https://first90-api.hub.lea-dev.site/api/docs`
- Telegram bot: `https://t.me/first90_OpenAI_Week_bot`

The public demo uses fictional European sample data. No login is required. Use **Reset demo** to restore Jordan Lee to day 18.

## What it does

- Builds a 90-day journey with 270 complete touchpoints.
- Adds nine enhanced Days 1–3 capsules for a People Manager staying in the same company and city, with original illustrations and selected learning resources.
- Personalizes guidance by role, company change, city change, and work mode.
- Tracks progress and consented mood signals without exposing private journal text.
- Offers a practical AI Transition Coach powered by GPT‑5.6 through the Responses API.
- Delivers the same journey through the web and an optional Telegram channel.
- Gives people teams an aggregate Studio for progress, engagement, content coverage, and support signals.
- Runs as a reproducible four-container stack: Caddy, FastAPI web, delivery worker, and PostgreSQL.

## Access and payments

Phase 1 is free early access. There is no checkout, card collection, billing profile, or payment-provider integration in this release.

Payment is Phase 2: hosted secure checkout, access entitlements, idempotent webhooks, cancellation, and refunds. This boundary is intentional; the free experience and operational reliability are validated before monetization is enabled.

## Quick start

### Docker

Requirements: Docker Engine with Compose.

```bash
cp .env.example .env
docker compose up --build
```

Open <http://localhost:8090>. The demo works without external credentials. Add `OPENAI_API_KEY` to `.env` for live GPT‑5.6 coaching.

### Local Python

Requirements: Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run uvicorn app.main:app --reload
```

The local Python path defaults to SQLite, so PostgreSQL is not required outside Docker.

## Verify

```bash
make check
docker compose config -q
docker compose up --build -d
curl --fail http://localhost:8090/health/ready
```

## GPT‑5.6 integration

`app/coach.py` uses the OpenAI Responses API with:

- `gpt-5.6-sol` as the explicit frontier model;
- low reasoning effort for a short, interactive coaching loop;
- a lean, code-versioned prompt with a strict 170-word product contract;
- `store=False` and a hashed `safety_identifier`;
- a deterministic fallback so the product remains testable without an API key.

The coach receives role, program day, high-level transition context, work mode, and the user's current question. It does not receive private journal history.

## Telegram

Set `TELEGRAM_BOT_TOKEN`, `TELEGRAM_BOT_USERNAME`, `TELEGRAM_WEBHOOK_SECRET`, and `APP_BASE_URL`, then register:

```text
https://first90-api.hub.lea-dev.site/api/v1/telegram/webhook/<TELEGRAM_WEBHOOK_SECRET>
```

Participant onboarding is real, not pre-seeded. Open [@first90_OpenAI_Week_bot](https://t.me/first90_OpenAI_Week_bot) in a private chat, tap **Start**, and answer six questions:

1. Preferred name.
2. Role. Early access currently supports **People Manager**.
3. Same or new company.
4. Same or new city.
5. One of 16 seeded European cities; this sets the IANA time zone.
6. Office, hybrid, or remote work.

The bot creates Day 1 and returns the first tailored focus immediately. Supported participant commands: `/start`, `/today`, `/mood 1-5`, `/pause`, `/web`, and `/cancel` during setup. Plain text in a private chat becomes a private journal entry.

For reviewer admin-chat mode, add the bot to a Telegram test group and use `/admin`, `/metrics`, `/roles`, `/preview 1`, `/preview 2`, `/preview 3`, and `/privacy`. Group mode exposes fictional aggregate data and capsule previews only; it never stores group messages as journal text.

See [Telegram onboarding](docs/TELEGRAM_ONBOARDING.md) and the in-product [reviewer guide](https://first90.hub.lea-dev.site/reviewers).

## Project map

```text
app/
  coach.py       GPT-5.6 transition coach and offline fallback
  domain.py      personalization, progress, phase, and signal logic
  main.py        web pages and versioned API
  models.py      SQLAlchemy domain model
  seed.py        270 universal touchpoints, tailored Days 1–3, and European demo data
  telegram.py    Telegram companion channel
  worker.py      timezone-aware delivery worker
  templates/     participant, team, landing, and privacy surfaces
deploy/          internal Caddy gateway
                 plus the shared-hub TLS route for port 8091
docs/            architecture, business logic, deployment, and Codex notes
tests/           domain, API, privacy, language, and channel coverage
```

## How Codex accelerated the build

Codex with GPT‑5.6 was used to inspect a mature reference implementation, extract business invariants, design a new public architecture, write the English product from a blank repository, build the responsive UI, add tests, prepare Docker deployment, and verify the live demo.

Key decisions remained explicit and human-reviewable:

- Web-first demo, because judges need a testable experience without Telegram setup.
- Private journal boundaries, because workplace support must not become surveillance.
- Deterministic AI fallback, because a missing key must not break judging.
- One complete 90-day role journey instead of a broad but shallow content catalog.

See [docs/CODEX.md](docs/CODEX.md) for the build log and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for system boundaries.

## License

[MIT](LICENSE)
