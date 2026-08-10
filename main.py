"""
============================================
🤖 QUANT TRADING BOT - MAIN ENTRY POINT
============================================
"""
import sys
import logging
from pathlib import Path
from typing import Dict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import (
    WATCHLIST, STRATEGY_CONFIG, ENABLE_AUTO_TRADE, 
    DEFAULT_CASH, LOGS_DIR, LOG_LEVEL
)
from signals import SignalGenerator
from strategies import MultiIndicatorStrategy
from api_client import MockAPIClient
from utils import setup_logging

# Setup logging
setup_logging(LOGS_DIR, LOG_LEVEL)
logger = logging.getLogger(__name__)

class QuantTradingBot:
    """Main trading bot orchestrator"""
    
    def __init__(self, use_mock: bool = True):
        logger.info("🤖 Initializing Quant Trading Bot...")
        self.signal_gen = SignalGenerator(STRATEGY_CONFIG)
        self.strategy = MultiIndicatorStrategy(STRATEGY_CONFIG)
        self.api = MockAPIClient(initial_cash=DEFAULT_CASH)
        logger.info("✅ Bot initialized (MOCK mode)")
    
    def analyze_and_trade(self):
        logger.info("\n" + "="*50)
        logger.info("🔄 Trading Cycle")
        logger.info("="*50)
        
        summary = self.api.get_portfolio_summary()
        logger.info(f"💰 Portfolio: ${summary['account_value']:,.2f} | Cash: ${summary['cash']:,.2f}")
        
        for symbol in WATCHLIST:
            try:
                sig = self.signal_gen.get_latest_signal(symbol)
                has_pos = self.api.has_position(symbol)
                
                if sig['action'] == 'BUY' and not has_pos:
                    logger.info(f"📈 {symbol}: BUY | Score: {sig['signal_score']} | ${sig['price']:.2f}")
                    if ENABLE_AUTO_TRADE:
                        self.api.buy(symbol, 10)
                elif sig['action'] == 'SELL' and has_pos:
                    logger.info(f"📉 {symbol}: SELL | Score: {sig['signal_score']} | ${sig['price']:.2f}")
                    if ENABLE_AUTO_TRADE:
                        self.api.sell(symbol)
                else:
                    logger.info(f"⏸️  {symbol}: {sig['action']} | Score: {sig['signal_score']}")
            except Exception as e:
                logger.error(f"❌ Error with {symbol}: {e}")
        
        logger.info(f"\n📋 Positions: {len(self.api.get_positions())}")

def main():
    print("\n" + "📈"*30)
    print("   QUANT TRADING BOT")
    print("📈"*30 + "\n")
    
    if ENABLE_AUTO_TRADE:
        print("⚠️  WARNING: AUTO-TRADE IS ENABLED\n")
    
    bot = QuantTradingBot(use_mock=True)
    bot.analyze_and_trade()
    
    print("\n✅ Done! Run with --continuous for ongoing mode.")

if __name__ == "__main__":
    main()
