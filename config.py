"""
Configuration settings for Quant Trading Bot
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Project paths
BASE_DIR = Path(__file__).parent
SRC_DIR = BASE_DIR / "src"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Investopedia credentials
INVESTOPEDIA_USERNAME = os.getenv("INVESTOPEDIA_USERNAME", "")
INVESTOPEDIA_PASSWORD = os.getenv("INVESTOPEDIA_PASSWORD", "")

# Validate credentials
if not INVESTOPEDIA_USERNAME or not INVESTOPEDIA_PASSWORD:
    raise ValueError("Missing INVESTOPEDIA_USERNAME or INVESTOPEDIA_PASSWORD in .env file")

# Trading configuration
DEFAULT_CASH = float(os.getenv("DEFAULT_CASH", "100000"))
MAX_POSITION_SIZE = float(os.getenv("MAX_POSITION_SIZE", "0.1"))  # 10% of portfolio
STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", "0.05"))  # 5% stop loss
TAKE_PROFIT_PCT = float(os.getenv("TAKE_PROFIT_PCT", "0.10"))  # 10% take profit

# API settings
CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "30"))
ENABLE_AUTO_TRADE = os.getenv("ENABLE_AUTO_TRADE", "false").lower() == "true"

# Watchlist (stocks to track)
WATCHLIST = [
    "AAPL", "MSFT", "GOOG", "NVDA", "TSLA",
    "AMZN", "META", "AMD", "INTC", "JPM", "NFLX", "DIS", "V", "MA", 
]

# Strategy parameters
STRATEGY_CONFIG = {
    "rsi_period": 14,
    "rsi_oversold": 30,
    "rsi_overbought": 70,
    "sma_short": 50,
    "sma_long": 200,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "bb_period": 20,
    "bb_std": 2,
}

print("✅ Configuration loaded successfully")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
