# 📘 Investopedia Simulator API — Setup & Usage Guide

> Source: https://github.com/dchrostowski/investopedia_simulator_api
> Keep this doc for when you are ready to enable REAL trading.

---

## 🎯 What This API Can Do

- Read all positions in your stock & short portfolios + get quotes
- Fetch and cancel pending/open trades
- Buy/Sell long positions
- Short sell / cover short positions
- Buy/sell options
- Perform option chain lookups

---

## 📋 Prerequisites

| Tool | Purpose | Notes |
|------|---------|-------|
| Python 3.12.2+ | Run the API | Recommended version to avoid issues |
| Git | Clone the repository | Or download the ZIP instead |
| Node.js | Virtual browser login + auth tokens | Install latest version |

---

## 🚀 SETUP STEPS

### Step 1 — Download the API code

    git clone https://github.com/dchrostowski/investopedia_simulator_api.git

Alternative: GitHub page → green "Code" button → "Download ZIP" → unzip it.

In our project:

    cd ~\quant-trading-bot
    .\venv\Scripts\Activate
    git clone https://github.com/dchrostowski/investopedia_simulator_api.git

### Step 2 — Install Node.js

Download and install the latest Node.js. It is used to log in to the
simulator with a virtual web browser and fetch authentication tokens.

### Step 3 — Install Python packages

    cd investopedia_simulator_api
    pip install -r ./requirements.txt

### Step 4 — Create credentials.json

Rename credentials_example.json to credentials.json:

    Copy-Item credentials_example.json credentials.json

Then open it and replace the values with your REAL login.
KEEP THE DOUBLE QUOTES INTACT:

    {
        "username": "you@example.org",
        "password": "yourpassword"
    }

⚠️ KNOWN ISSUE: Investopedia now often uses EMAIL CODES instead of
passwords. The API requires a password. Workarounds:
1. Try "Forgot password?" on investopedia.com to SET a password.
2. If impossible, stay in MOCK mode and trade manually from bot signals.

### Step 5 — Run the example

    python example.py

This prints your portfolio details and executes sample trades.

---

## 💻 USAGE REFERENCE (from example.py)

### Imports & Connect

    from investopedia_api import InvestopediaApi
    from api_models import OptionScope
    from trade_common import (OrderLimit, TransactionType, Expiration,
                              StockTrade, OptionTrade)
    import json

    with open('credentials.json') as ifh:
        credentials = json.load(ifh)

    client = InvestopediaApi(credentials)
    p = client.portfolio

### Portfolio Details

    print(p.account_value)
    print(p.cash)
    print(p.buying_power)
    print(p.annual_return_pct)

### Open Orders (+ Cancel)

    for open_order in p.open_orders:
        print(open_order.trade_type, open_order.symbol,
              open_order.quantity, open_order.order_price)
        # open_order.cancel()   # cancel a pending trade

### Buy With Limit Order

    trade = StockTrade(
        portfolio_id=p.portfolio_id,
        symbol="GOOG",
        quantity=2,
        transaction_type=TransactionType.BUY,
        order_limit=OrderLimit.LIMIT(100),
        expiration=Expiration.GOOD_UNTIL_CANCELLED()
    )
    trade.validate()
    trade.execute()

### Buy At Market Price (defaults)

    trade = StockTrade(portfolio_id=p.portfolio_id, symbol='AAPL',
                       quantity=3, transaction_type=TransactionType.BUY)
    trade.validate()
    trade.execute()

### Short Sell

    trade = StockTrade(portfolio_id=p.portfolio_id, symbol='AMZN',
                       quantity=1, transaction_type=TransactionType.SELL_SHORT)
    trade.validate()
    trade.execute()

### Refresh & Manage Positions

    client.refresh_portfolio()
    p = client.portfolio

    p.stock_portfolio[0].sell()     # sell first long position
    p.short_portfolio[0].cover()    # cover first short position
    p.option_portfolio[0].close()   # close first option contract

### Option Chain Lookup

    from datetime import datetime, timedelta

    oc = client.get_option_chain('AAPL')
    all_options = oc.all()

    two_weeks = datetime.now() + timedelta(days=14)
    puts = oc.search(before=two_weeks, puts=True, calls=False,
                     scope=OptionScope.IN_THE_MONEY)

---

## 🔗 Integration With Our Bot

- The bot currently runs on MockAPIClient (src/api_client.py).
- When login works: wrap this API in an InvestopediaAPIClient class,
  then switch main.py to use_mock=False.

---

## ✅ Quick Checklist

- [ ] Python 3.12.2+ installed
- [ ] Git installed
- [ ] Node.js installed
- [ ] Repo cloned
- [ ] pip install -r requirements.txt done
- [ ] credentials.json created with real login
- [ ] python example.py runs successfully
