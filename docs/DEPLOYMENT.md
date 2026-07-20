# Deployment on hub.lea-dev.site

## DNS

Create three DNS records pointing to the same address as `hub.lea-dev.site`:

- `first90.hub.lea-dev.site` — landing and participant demo.
- `first90-studio.hub.lea-dev.site` — Team Studio.
- `first90-api.hub.lea-dev.site` — API docs, health, and Telegram webhook.

Use `A`/`AAAA` records with the hub address or `CNAME` records to `hub.lea-dev.site`, depending on the DNS provider.

## Host route

The Compose gateway defaults to `127.0.0.1:8090` for local use. On the shared hub, set `APP_PORT=8091` because port 8090 belongs to another service. The host reverse proxy sends all three names to `127.0.0.1:8091` and terminates TLS. The versioned route is `deploy/first90.hub.caddy`.

## Start

```bash
cp .env.example .env
# Set strong POSTGRES_PASSWORD, SECRET_KEY, and TELEGRAM_WEBHOOK_SECRET.
# Set TELEGRAM_BOT_TOKEN and TELEGRAM_BOT_USERNAME to enable live subscription.
# On hub.lea-dev.site, set APP_PORT=8091.
docker compose up --build -d
docker compose ps
curl --fail http://127.0.0.1:${APP_PORT:-8090}/health/ready
```

Do not commit `.env`. Keep the OpenAI and Telegram keys only on the server.
