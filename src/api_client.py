"""
============================================
🔌 API CLIENT MODULE
============================================
Mock API client for testing. No external imports needed.
"""
import logging
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockAPIClient:
    """Mock API client for safe testing without real trades."""
    
    def __init__(self, initial_cash: float = 100000):
        self.cash = initial_cash
        self.positions: Dict[str, Dict] = {}
        self.trades: List[Dict] = []
        logger.info(f"🧪 Mock API initialized with ${initial_cash:,.2f}")
    
    def get_portfolio_summary(self) -> Dict:
        pos_value = sum(p['quantity'] * p['price'] for p in self.positions.values())
        return {
            'account_value': self.cash + pos_value,
            'cash': self.cash,
            'buying_power': self.cash,
            'num_positions': len(self.positions),
            'timestamp': datetime.now()
        }
    
    def get_positions(self) -> List[Dict]:
        return list(self.positions.values())
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        return self.positions.get(symbol)
    
    def has_position(self, symbol: str) -> bool:
        return symbol in self.positions
    
    def buy(self, symbol: str, quantity: int, **kwargs) -> bool:
        import yfinance as yf
        data = yf.download(symbol, period='1d', progress=False)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        if data.empty:
            logger.error(f"No data for {symbol}")
            return False
        price = float(data['Close'].iloc[-1])
        cost = quantity * price
        if cost > self.cash:
            logger.warning(f"Insufficient cash for {symbol}")
            return False
        self.cash -= cost
        if symbol in self.positions:
            self.positions[symbol]['quantity'] += quantity
        else:
            self.positions[symbol] = {
                'symbol': symbol, 'quantity': quantity, 'price': price,
                'market_value': cost, 'gain_loss': 0, 'gain_loss_pct': 0
            }
        self.trades.append({'action': 'BUY', 'symbol': symbol, 'quantity': quantity,
                           'price': price, 'timestamp': datetime.now()})
        logger.info(f"📈 MOCK BUY: {quantity} {symbol} @ ${price:.2f}")
        return True
    
    def sell(self, symbol: str, quantity: int = None, **kwargs) -> bool:
        if symbol not in self.positions:
            logger.warning(f"No position in {symbol}")
            return False
        if quantity is None:
            quantity = self.positions[symbol]['quantity']
        if quantity > self.positions[symbol]['quantity']:
            logger.warning(f"Insufficient shares for {symbol}")
            return False
        import yfinance as yf
        data = yf.download(symbol, period='1d', progress=False)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        price = float(data['Close'].iloc[-1])
        self.cash += quantity * price
        self.positions[symbol]['quantity'] -= quantity
        if self.positions[symbol]['quantity'] == 0:
            del self.positions[symbol]
        self.trades.append({'action': 'SELL', 'symbol': symbol, 'quantity': quantity,
                           'price': price, 'timestamp': datetime.now()})
        logger.info(f"📉 MOCK SELL: {quantity} {symbol} @ ${price:.2f}")
        return True

if __name__ == "__main__":
    print("🧪 Testing API Client...\n")
    client = MockAPIClient()
    client.buy("AAPL", 10)
    print(f"\nPortfolio: {client.get_portfolio_summary()}")
