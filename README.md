# RSI Demo Trading Bot (Vercel Deployment)

This FastAPI application simulates a trading bot for Bybit futures based on RSI (Relative Strength Index) signals. It is designed for **testing and demonstration purposes only** and should **not be used for real trading**.

## 🎯 Features

- **Mock RSI Calculation**: Generates random RSI values (10-90) for demonstration
- **Simulated Trading**: Executes BUY/SELL trades based on RSI thresholds
- **Security Hardening**: API-key authentication, request deduplication, sequence tracking, and balance checks to prevent double spend
- **Duplicate Protection**: Trade hashing and idempotency keys guard against replayed requests
- **Telegram Notifications**: Sends trade alerts to Telegram (optional)
- **Trade History**: Stores simulated trades in SQLite database (serverless-friendly `/tmp` storage)
- **RESTful API + Web UI**: Secure endpoints with a Tailwind-powered dashboard
- **Vercel Ready**: Configured for serverless deployment on Vercel

## 🔐 Security Hardening

- **API Key Authentication**: Protect sensitive endpoints (`POST /buy`, `POST /sell`, `POST /notify`) with configurable API keys via the `X-API-Key` header. Supports plain keys or SHA-256 hashes prefixed with `hash:` (generate with `python -c "from security import KeyManager; print('hash:' + KeyManager().hash_value('my_api_key'))"`).
- **Request Idempotency**: Every request is hashed (pair + action + quantity + request ID). Duplicates return the original trade, preventing accidental replays.
- **Sequence Enforcement**: Monotonic sequence numbers per pair/action prevent out-of-order or replayed trades.
- **Balance Accounting**: Quote/base balances are tracked atomically to prevent double spending. Trades fail if insufficient funds.
- **Audit Trail**: Each trade stores transaction ID, sequence, request hash, and balance snapshot for forensic analysis.
- **Key Handling Guidance**: Environment template encourages key hashing (pepper) and secure storage via secret managers. Secrets are masked in logs.
- **Serverless Safety**: Uses `/tmp` for writable storage, lazy initialization, and WAL mode for better reliability in Vercel.

## 🚀 Run Locally

### Prerequisites

- Python 3.11 or higher
- pip package manager

### Installation

1. **Create virtual environment:**

   ```bash
   python -m venv .venv
   ```

2. **Activate virtual environment:**

   **Windows:**
   ```bash
   .venv\Scripts\activate
   ```

   **Linux/Mac:**
   ```bash
   source .venv/bin/activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and configure credentials:
   - `TELEGRAM_TOKEN` / `TELEGRAM_CHAT_ID` (optional notifications)
   - `API_KEYS` – comma-separated keys allowed to call protected endpoints (required for UI trades)
   - `KEY_HASH_PEPPER` (optional) – adds an HMAC pepper for hashing secrets
   - Adjust balances (`DEFAULT_BASE_BALANCE`, `DEFAULT_QUOTE_BALANCE`) and default quantity as needed

5. **Run the application:**

   ```bash
   uvicorn main:app --reload
   ```

6. **Access the API:**

   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

## 🌐 Deploy on Vercel

### Step 1: Push to GitHub

1. Initialize git repository (if not already):

   ```bash
   git init
   git add .
   git commit -m "Initial commit: RSI Trading Bot Demo"
   ```

2. Create a new repository on GitHub and push:

   ```bash
   git remote add origin https://github.com/yourusername/vercel-rsi-bot.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy on Vercel

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click **"New Project"**
3. Import your GitHub repository
4. Vercel will auto-detect Python:
   - **Framework Preset**: Other
   - **Root Directory**: `./` (or leave default)
   - **Build Command**: Leave empty (Vercel handles it)
   - **Output Directory**: Leave empty
5. Add environment variables:
   - Go to **Settings** → **Environment Variables**
   - Add all variables from `.env.example`:
     - `BYBIT_API_KEY`
     - `BYBIT_API_SECRET`
     - `TELEGRAM_TOKEN` (optional)
     - `TELEGRAM_CHAT_ID` (optional)
     - `TRADING_PAIR`
     - `RSI_OVERSOLD`
     - `RSI_OVERBOUGHT`
     - `DEFAULT_BASE_BALANCE`
     - `DEFAULT_QUOTE_BALANCE`
     - `DEFAULT_ORDER_QUANTITY`
     - `API_KEYS`
     - `KEY_HASH_PEPPER` (optional)
     - `API_KEY_HEADER_NAME` (optional)
6. Click **"Deploy"**

### Step 3: Access Your API

After deployment, you'll get a URL like:
```
https://rsi-bot-demo.vercel.app
```

## 🧪 API Endpoints

### `GET /`
Root endpoint with API information.

**Response:**
```json
{
  "name": "RSI Trading Bot Demo",
  "version": "1.1.0",
  "description": "Simulated RSI-based trading bot for testing",
  "endpoints": {...}
}
```

### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2024-01-01T12:00:00",
  "service": "rsi-trading-bot"
}
```

### `GET /status`
Get current trading status including RSI, price, balance snapshot, and trade summary.

**Response:**
```json
{
  "pair": "BTCUSDT",
  "rsi": 45.23,
  "price": 45123.45,
  "rsi_oversold": 20,
  "rsi_overbought": 80,
  "trades": {
    "total_trades": 5,
    "buy_trades": 3,
    "sell_trades": 2
  },
  "balances": {
    "BTC": 0.85,
    "USDT": 41234.56
  }
}
```

### `POST /buy`
Simulate a BUY trade if RSI is below oversold threshold (default: 20). Requires `X-API-Key` header.

**Request:**
```http
POST /buy HTTP/1.1
Host: example.vercel.app
Content-Type: application/json
X-API-Key: your_api_key

{
  "quantity": 0.01,
  "request_id": "24f7f3ba-2d9d-4fc0-8c52-5c3c2a6c978a",
  "client_ref": "web-buy-1700000000",
  "sequence_number": 1
}
```

**Response (executed):**
```json
{
  "pair": "BTCUSDT",
  "action": "BUY",
  "rsi": 18.4,
  "price": 45000.0,
  "quantity": 0.01,
  "status": "executed",
  "trade_id": 1,
  "transaction_id": "fS3_h4e2-l8zO0yz3ak7",
  "sequence_number": 1,
  "request_id": "24f7f3ba-2d9d-4fc0-8c52-5c3c2a6c978a",
  "request_hash": "f6bf...",
  "balances": {
    "BTC": 1.01,
    "USDT": 44950.0
  },
  "message": "Trade executed successfully."
}
```

**Response (rejected):**
```json
{
  "pair": "BTCUSDT",
  "action": "BUY",
  "rsi": 45.2,
  "price": 45123.45,
  "quantity": 0.01,
  "status": "rejected",
  "trade_id": null,
  "transaction_id": null,
  "sequence_number": 1,
  "request_id": "24f7f3ba-2d9d-4fc0-8c52-5c3c2a6c978a",
  "request_hash": "f6bf...",
  "balances": {
    "BTC": 1.00,
    "USDT": 45000.0
  },
  "message": "RSI (45.2) is not below oversold threshold (20)."
}
```

### `POST /sell`
Simulate a SELL trade if RSI is above overbought threshold (default: 80). Requires `X-API-Key` header.

**Request:**
```http
POST /sell HTTP/1.1
Host: example.vercel.app
Content-Type: application/json
X-API-Key: your_api_key

{
  "quantity": 0.01,
  "request_id": "60d269e0-5cb1-4df4-a4c9-b6437bc44d8f",
  "client_ref": "web-sell-1700000500",
  "sequence_number": 2
}
```

**Response (executed):**
```json
{
  "pair": "BTCUSDT",
  "action": "SELL",
  "rsi": 82.1,
  "price": 45100.0,
  "quantity": 0.01,
  "status": "executed",
  "trade_id": 2,
  "transaction_id": "dA2P73or7iXbvtcL1n",
  "sequence_number": 2,
  "request_id": "60d269e0-5cb1-4df4-a4c9-b6437bc44d8f",
  "request_hash": "9d21...",
  "balances": {
    "BTC": 0.99,
    "USDT": 45451.0
  },
  "message": "Trade executed successfully."
}
```

**Response (rejected - insufficient balance):**
```json
{
  "pair": "BTCUSDT",
  "action": "SELL",
  "rsi": 48.2,
  "price": 45200.0,
  "quantity": 2.0,
  "status": "rejected",
  "trade_id": null,
  "transaction_id": null,
  "sequence_number": 2,
  "request_id": "60d269e0-5cb1-4df4-a4c9-b6437bc44d8f",
  "request_hash": "9d21...",
  "balances": {
    "BTC": 1.00,
    "USDT": 45000.0
  },
  "message": "Insufficient BTC balance. Needed 2.000000, available 1.000000."
}
```

### `POST /notify`
Send a test notification to Telegram (requires `X-API-Key`).

**Response:**
```json
{
  "status": "sent",
  "message": "🧪 Test notification from RSI Trading Bot Demo..."
}
```

### `GET /trades?limit=10`
Get recent trade history.

**Response:**
```json
{
  "trades": [
    {
      "id": 1,
      "transaction_id": "fS3_h4e2-l8zO0yz3ak7",
      "sequence_number": 1,
      "timestamp": "2024-01-01T12:00:00",
      "pair": "BTCUSDT",
      "action": "BUY",
      "rsi": 18.4,
      "price": 45000.0,
      "quantity": 0.01,
      "status": "executed",
      "metadata": {
        "balances": {
          "BTC": 1.01,
          "USDT": 44950.0
        }
      }
    }
  ],
  "count": 1
}
```

## 📁 Project Structure

```
vercel_rsi_bot/
├── main.py           # FastAPI app with endpoints
├── trader.py         # Simulated RSI and order logic
├── notifier.py       # Telegram notification sender
├── config.py         # Environment variables loader
├── db.py             # SQLite trade history
├── requirements.txt  # Python dependencies
├── vercel.json       # Vercel deployment config
├── .env.example      # Example environment variables
└── README.md         # This file
```

## 🔧 Configuration

All configuration is done through environment variables (see `.env.example`):

- **BYBIT_API_KEY**: Demo API key (not used for real trading)
- **BYBIT_API_SECRET**: Demo API secret (not used for real trading)
- **TELEGRAM_TOKEN**: Telegram bot token (optional)
- **TELEGRAM_CHAT_ID**: Telegram chat ID (optional)
- **TRADING_PAIR**: Trading pair (default: BTCUSDT)
- **RSI_OVERSOLD**: RSI threshold for BUY signals (default: 20)
- **RSI_OVERBOUGHT**: RSI threshold for SELL signals (default: 80)

## ⚠️ Important Notes

1. **This is a simulation**: All trades are fake and for testing purposes only
2. **No real trading**: This bot does not connect to real Bybit API for trading
3. **Vercel limitations**: Vercel serverless functions cannot run background tasks or infinite loops
4. **Database**: SQLite database (`trades.db`) is created locally but may not persist on Vercel (use external database for production)

## 🛠️ Development

### Adding Real Bybit Integration

To replace mock data with real Bybit API calls:

1. Update `trader.py`:
   - Replace `calculate_mock_rsi()` with real RSI calculation using `pandas_ta`
   - Replace `get_mock_price()` with real price fetch from Bybit API

2. Update `main.py`:
   - Add real order execution logic (if needed)
   - Implement proper error handling for API failures

### Testing

Test endpoints using curl or any HTTP client:

```bash
# Health check
curl https://your-app.vercel.app/health

# Get status
curl https://your-app.vercel.app/status

# Execute BUY
curl -X POST https://your-app.vercel.app/buy

# Execute SELL
curl -X POST https://your-app.vercel.app/sell

# Send notification
curl -X POST https://your-app.vercel.app/notify
```

## 📝 License

This project is for educational and testing purposes only.

## 🤝 Contributing

This is a demo project. Feel free to fork and modify for your own testing needs.

---

**⚠️ DISCLAIMER**: This software is for demonstration purposes only. Do not use it for real trading. Always test thoroughly and understand the risks before trading with real money.

