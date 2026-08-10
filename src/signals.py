"""
Trading Signal Generation Module
"""
import pandas as pd
import numpy as np
import yfinance as yf
from typing import Dict, Tuple
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Try to import TA-Lib, fallback to ta if needed
try:
    import talib
    USE_TALIB = True
except ImportError:
    import ta
    USE_TALIB = False
    print("⚠️ Using 'ta' library instead of TA-Lib")


class SignalGenerator:
    """Generate trading signals using technical indicators"""
    
    def __init__(self, config: Dict):
        self.config = config
    
    def fetch_data(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        """Fetch historical data for a symbol"""
        df = yf.download(symbol, period=period, progress=False)
        
        if df.empty:
            raise ValueError(f"No data found for {symbol}")
        
        # Flatten multi-index columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        return df
    
    def calculate_rsi(self, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        if USE_TALIB:
            return talib.RSI(close, timeperiod=period)
        else:
            return ta.momentum.RSIIndicator(close, window=period).rsi()
    
    def calculate_macd(self, close: pd.Series, fast: int = 12, 
                       slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD indicator"""
        if USE_TALIB:
            macd, macd_signal, macd_hist = talib.MACD(
                close, fastperiod=fast, slowperiod=slow, signalperiod=signal
            )
            return macd, macd_signal, macd_hist
        else:
            macd_obj = ta.trend.MACD(close, window_fast=fast, 
                                     window_slow=slow, window_sign=signal)
            return macd_obj.macd(), macd_obj.macd_signal(), macd_obj.macd_diff()
    
    def calculate_bollinger(self, close: pd.Series, period: int = 20, 
                           std: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        if USE_TALIB:
            upper, middle, lower = talib.BBANDS(
                close, timeperiod=period, nbdevup=std, nbdevdn=std
            )
            return upper, middle, lower
        else:
            bb_obj = ta.volatility.BollingerBands(close, window=period, window_dev=std)
            return bb_obj.bollinger_hband(), bb_obj.bollinger_mavg(), bb_obj.bollinger_lband()
    
    def calculate_sma(self, close: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        if USE_TALIB:
            return talib.SMA(close, timeperiod=period)
        else:
            return ta.trend.SMAIndicator(close, window=period).sma_indicator()
    
    def generate_signals(self, symbol: str) -> pd.DataFrame:
        """
        Generate comprehensive trading signals for a symbol
        
        Returns DataFrame with all indicators and final signal
        """
        # Fetch data
        df = self.fetch_data(symbol)
        close = df['Close']
        
        # Calculate indicators
        cfg = self.config
        
        # RSI
        df['RSI'] = self.calculate_rsi(close, cfg['rsi_period'])
        
        # MACD
        df['MACD'], df['MACD_signal'], df['MACD_hist'] = self.calculate_macd(
            close, cfg['macd_fast'], cfg['macd_slow'], cfg['macd_signal']
        )
        
        # Bollinger Bands
        df['BB_upper'], df['BB_middle'], df['BB_lower'] = self.calculate_bollinger(
            close, cfg['bb_period'], cfg['bb_std']
        )
        df['BB_width'] = (df['BB_upper'] - df['BB_lower']) / df['BB_middle']
        df['BB_position'] = (close - df['BB_lower']) / (df['BB_upper'] - df['BB_lower'])
        
        # Moving Averages
        df['SMA_short'] = self.calculate_sma(close, cfg['sma_short'])
        df['SMA_long'] = self.calculate_sma(close, cfg['sma_long'])
        
        # Volume analysis
        if 'Volume' in df.columns:
            df['Volume_MA'] = df['Volume'].rolling(20).mean()
            df['Volume_ratio'] = df['Volume'] / df['Volume_MA']
        
        # Generate individual signals
        df['RSI_signal'] = np.where(df['RSI'] < cfg['rsi_oversold'], 1,
                           np.where(df['RSI'] > cfg['rsi_overbought'], -1, 0))
        
        df['MACD_signal_raw'] = np.where(df['MACD'] > df['MACD_signal'], 1, -1)
        df['MACD_cross'] = np.where(
            (df['MACD'] > df['MACD_signal']) & 
            (df['MACD'].shift(1) <= df['MACD_signal'].shift(1)), 1,
            np.where(
                (df['MACD'] < df['MACD_signal']) & 
                (df['MACD'].shift(1) >= df['MACD_signal'].shift(1)), -1, 0
            )
        )
        
        df['MA_signal'] = np.where(df['SMA_short'] > df['SMA_long'], 1, -1)
        df['MA_cross'] = np.where(
            (df['SMA_short'] > df['SMA_long']) & 
            (df['SMA_short'].shift(1) <= df['SMA_long'].shift(1)), 1,
            np.where(
                (df['SMA_short'] < df['SMA_long']) & 
                (df['SMA_short'].shift(1) >= df['SMA_long'].shift(1)), -1, 0
            )
        )
        
        df['BB_signal'] = np.where(df['BB_position'] < 0.2, 1,
                          np.where(df['BB_position'] > 0.8, -1, 0))
        
        # Combined signal score (weighted voting)
        weights = {
            'RSI': 2,
            'MACD_cross': 2,
            'MA_cross': 2,
            'BB': 1
        }
        
        df['signal_score'] = (
            df['RSI_signal'] * weights['RSI'] +
            df['MACD_cross'] * weights['MACD_cross'] +
            df['MA_cross'] * weights['MA_cross'] +
            df['BB_signal'] * weights['BB']
        )
        
        # Final action
        df['action'] = np.where(df['signal_score'] >= 2, 'BUY',
               np.where(df['signal_score'] <= -2, 'SELL', 'HOLD'))
        # Signal strength (0-100%)
        max_score = sum(weights.values())
        df['signal_strength'] = (df['signal_score'].abs() / max_score * 100).clip(0, 100)
        
        return df
    
    def get_latest_signal(self, symbol: str) -> Dict:
        """Get the latest signal for a symbol"""
        df = self.generate_signals(symbol)
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        return {
            'symbol': symbol,
            'timestamp': latest.name,
            'price': latest['Close'],
            'action': latest['action'],
            'signal_score': latest['signal_score'],
            'signal_strength': latest['signal_strength'],
            'indicators': {
                'RSI': latest['RSI'],
                'MACD': latest['MACD'],
                'MACD_signal': latest['MACD_signal'],
                'BB_position': latest['BB_position'],
                'SMA_short': latest['SMA_short'],
                'SMA_long': latest['SMA_long']
            },
            'new_signal': latest['action'] != prev['action'],
            'change_pct': ((latest['Close'] - prev['Close']) / prev['Close'] * 100)
        }


# Quick test
if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Add project root to path so we can import config
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from config import STRATEGY_CONFIG
    
    print("🧪 Testing Signal Generator...\n")
    gen = SignalGenerator(STRATEGY_CONFIG)
    sig = gen.get_latest_signal("AAPL")
    print(f"📊 {sig['symbol']}: {sig['action']}")
    print(f"   Price: ${sig['price']:.2f}")
    print(f"   Score: {sig['signal_score']}")
    print(f"   Strength: {sig['signal_strength']:.1f}%")
    print(f"   RSI: {sig['indicators']['RSI']:.1f}")