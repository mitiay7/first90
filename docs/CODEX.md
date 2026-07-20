# Built with Codex and GPT‑5.6

This repository was created from a blank Git history during OpenAI Build Week 2026.

## Where Codex accelerated the work

1. Inspected a mature private reference product and separated durable business rules from legacy implementation details.
2. Reframed a Telegram-first experience as a judge-friendly web product while keeping Telegram as a supported channel.
3. Rebuilt the domain model, 90-day content generator, personalization engine, privacy boundary, API, delivery worker, and responsive interface in English.
4. Used official OpenAI documentation to implement the GPT‑5.6 Responses API contract.
5. Added automated checks for behavior, English-only public code and content, European city seeds, privacy-safe team output, and container readiness.
6. Prepared the public repository, four-container deployment, Telegram onboarding, reviewer path, and operational guides.

## Key decisions

- `gpt-5.6-sol` is explicit rather than an implicit alias.
- Low reasoning effort matches the short interactive coaching task.
- Prompts live in code, stay lean, and define output length and boundaries once.
- Live AI failure falls back to a deterministic coach response.
- The public repository contains fictional data only.

## Verification

The final delivery records unit and integration test counts, Docker health, live URL checks, and English-only scans in the release notes.
