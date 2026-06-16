# vercel-rsi-bot_mvp

> Demo RSI trading bot — simulated BUY/SELL signals on Bybit futures, production-grade API security, Telegram alerts, and one-click Vercel deploy.

A FastAPI application that demonstrates a complete trading-bot backend: RSI signal generation, authenticated REST endpoints, idempotent trade execution, SQLite audit trail, and Telegram notifications. All trades are simulated — no real funds involved.

## Features

- **RSI signals** — generates BUY/SELL decisions based on configurable RSI thresholds
- **API-key auth** — `X-API-Key` header; supports plain keys or `hash:sha256` prefix
- **Idempotency** — each request is hashed (pair + action + qty + request ID); replays return the original trade
- **Sequence enforcement** — monotonic sequence numbers per pair/action prevent out-of-order execution
- **Balance accounting** — quote/base balances tracked atomically; trades fail on insufficient funds
- **Audit trail** — every trade stores tx ID, sequence, request hash, and balance snapshot
- **Telegram notifications** — optional trade alerts via Bot API
- **Serverless-safe** — WAL mode SQLite in `/tmp`, lazy initialization, no persistent process required

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI, Python 3.11+ |
| Database | SQLite (WAL mode) |
| Auth | SHA-256 hashed API keys |
| Notifications | Telegram Bot API |
| Frontend | Tailwind CSS dashboard |
| Deployment | Vercel (serverless) |

## Getting Started

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in API_KEY, TELEGRAM_BOT_TOKEN (optional)
uvicorn main:app --reload
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `API_KEY` | Secret for `X-API-Key` header (`hash:sha256_hex` or plain) |
| `TELEGRAM_BOT_TOKEN` | Bot token for trade alerts (optional) |
| `TELEGRAM_CHAT_ID` | Target chat for notifications (optional) |

## API

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `POST /buy` | POST | ✓ | Execute simulated BUY |
| `POST /sell` | POST | ✓ | Execute simulated SELL |
| `GET /trades` | GET | ✓ | Trade history |
| `GET /balance` | GET | ✓ | Current balances |
| `POST /notify` | POST | ✓ | Send Telegram alert |

## License

MIT
