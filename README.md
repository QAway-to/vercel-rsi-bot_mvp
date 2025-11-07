# RSI Demo Trading Bot (Vercel Deployment)

This FastAPI application simulates a trading bot for Bybit futures based on RSI (Relative Strength Index) signals. It is designed for **testing and demonstration purposes only** and should **not be used for real trading**.

## 🎯 Features

- **Mock RSI Calculation**: Generates random RSI values (10-90) for demonstration
- **Simulated Trading**: Executes BUY/SELL trades based on RSI thresholds
- **Telegram Notifications**: Sends trade alerts to Telegram (optional)
- **Trade History**: Stores simulated trades in SQLite database
- **RESTful API**: Clean FastAPI endpoints for all operations
- **Vercel Ready**: Configured for serverless deployment on Vercel

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

   Edit `.env` and add your Telegram credentials (optional):
   - `TELEGRAM_TOKEN`: Get from [@BotFather](https://t.me/BotFather) on Telegram
   - `TELEGRAM_CHAT_ID`: Get from [@userinfobot](https://t.me/userinfobot) on Telegram

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
     - `TRADING_PAIR` (optional, defaults to BTCUSDT)
     - `RSI_OVERSOLD` (optional, defaults to 20)
     - `RSI_OVERBOUGHT` (optional, defaults to 80)
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
  "version": "1.0.0",
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
Get current trading status including RSI, price, and trade summary.

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
  }
}
```

### `POST /buy`
Simulate a BUY trade if RSI is below oversold threshold (default: 20).

**Response (executed):**
```json
{
  "pair": "BTCUSDT",
  "action": "BUY",
  "rsi": 18.4,
  "price": 45000.0,
  "quantity": 0.005,
  "status": "executed",
  "trade_id": 1
}
```

**Response (rejected):**
```json
{
  "pair": "BTCUSDT",
  "action": "BUY",
  "rsi": 45.2,
  "status": "rejected",
  "reason": "RSI (45.2) is not below oversold threshold (20)"
}
```

### `POST /sell`
Simulate a SELL trade if RSI is above overbought threshold (default: 80).

**Response (executed):**
```json
{
  "pair": "BTCUSDT",
  "action": "SELL",
  "rsi": 82.1,
  "price": 45100.0,
  "quantity": 0.005,
  "status": "executed",
  "trade_id": 2
}
```

**Response (rejected):**
```json
{
  "pair": "BTCUSDT",
  "action": "SELL",
  "rsi": 45.2,
  "status": "rejected",
  "reason": "RSI (45.2) is not above overbought threshold (80)"
}
```

### `POST /notify`
Send a test notification to Telegram.

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
      "timestamp": "2024-01-01T12:00:00",
      "pair": "BTCUSDT",
      "action": "BUY",
      "rsi": 18.4,
      "price": 45000.0,
      "quantity": 0.005,
      "status": "executed"
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

