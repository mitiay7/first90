# Telegram onboarding

## Participant path

1. Open [@first90_OpenAI_Week_bot](https://t.me/first90_OpenAI_Week_bot).
2. Tap **Start** or send `/start`.
3. Enter the preferred name.
4. Select **People Manager**, the role supported in early access.
5. Choose `same` or `new` company.
6. Choose `same` or `new` city.
7. Enter one supported European city. The city sets the IANA time zone used by delivery.
8. Choose `office`, `hybrid`, or `remote` work.
9. Read the first tailored Day 1 focus returned by the bot.

After setup:

- `/today` returns the current touchpoint and its learning resource, when present.
- `/mood 1-5` saves an optional energy signal.
- `/pause` pauses or resumes delivery.
- `/web` opens the optional fictional web demo.
- Plain text in the private bot chat becomes a private journal entry.

Send `/cancel` to discard an unfinished onboarding flow. Sending `/start` after enrollment does not reset progress.

## Admin setup

1. Create a bot with BotFather and keep its token outside source control.
2. Set `TELEGRAM_BOT_TOKEN`, `TELEGRAM_BOT_USERNAME`, `TELEGRAM_WEBHOOK_SECRET`, and `APP_BASE_URL` in the server environment.
3. Register the HTTPS webhook at:

   ```text
   https://first90-api.hub.lea-dev.site/api/v1/telegram/webhook/<TELEGRAM_WEBHOOK_SECRET>
   ```

4. Use the same webhook secret as Telegram's secret-token header.
5. Share `https://t.me/first90_OpenAI_Week_bot` with participants.
6. Complete one test onboarding and verify `/today` before inviting a cohort.

## Reviewer admin chat

Add the bot to a Telegram test group. The group commands are:

- `/admin` — capabilities and live links.
- `/metrics` — fictional aggregate journey health.
- `/roles` — content-ready role and personalization contexts.
- `/preview 1`, `/preview 2`, `/preview 3` — enhanced same-company, same-city manager capsules.
- `/privacy` — the admin visibility boundary.

Group mode never creates participants and never stores group messages as journal entries.
