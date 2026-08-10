
import pytest
import sys
from pathlib import Path
import unittest
import pandas as pd
import numpy as np

# Add src to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from signals import SignalGenerator
from config import STRATEGY_CONFIG


# ============================================
# 📦 FIXTURES
# ============================================

@pytest.fixture
def generator():
    """Create a SignalGenerator instance for tests"""
    return SignalGenerator(STRATEGY_CONFIG)


@pytest.fixture
def sample_data():
    """Create sample price data for indicator tests"""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
    df = pd.DataFrame({
        'Open': prices,
        'High': prices + np.abs(np.random.randn(100) * 0.3),
        'Low': prices - np.abs(np.random.randn(100) * 0.3),
        'Close': prices,
        'Volume': np.random.randint(1000000, 5000000, 100)
    }, index=dates)
    return df


# ============================================
# ✅ INITIALIZATION TESTS
# ============================================

def test_generator_init(generator):
    """Test SignalGenerator initializes correctly"""
    assert generator is not None
    assert generator.config == STRATEGY_CONFIG
    assert 'rsi_period' in generator.config


# ============================================
# 📊 DATA FETCHING TESTS
# ============================================

def test_fetch_data_success(generator):
    """Test fetching data for a valid symbol"""
    df = generator.fetch_data("AAPL", period="1mo")
    assert not df.empty
    assert len(df) > 0
    assert 'Close' in df.columns
    assert 'Open' in df.columns
    assert 'High' in df.columns
    assert 'Low' in df.columns
    assert isinstance(df.index, pd.DatetimeIndex)


def test_fetch_data_invalid_symbol(generator):
    """Test fetching data for an invalid symbol raises error"""
    with pytest.raises(ValueError, match="No data found"):
        generator.fetch_data("INVALIDSYMBOL123", period="1mo")


# ============================================
# 📈 SIGNAL GENERATION TESTS
# ============================================

def test_generate_signals_structure(generator):
    """Test generate_signals returns DataFrame with expected columns"""
    df = generator.generate_signals("AAPL")
    
    assert not df.empty
    assert isinstance(df, pd.DataFrame)
    
    # Check indicator columns
    assert 'RSI' in df.columns
    assert 'MACD' in df.columns
    assert 'MACD_signal' in df.columns
    assert 'MACD_hist' in df.columns
    assert 'BB_upper' in df.columns
    assert 'BB_middle' in df.columns
    assert 'BB_lower' in df.columns
    assert 'BB_position' in df.columns
    assert 'SMA_short' in df.columns
    assert 'SMA_long' in df.columns
    
    # Check signal columns
    assert 'signal_score' in df.columns
    assert 'action' in df.columns
    assert 'signal_strength' in df.columns


def test_generate_signals_action_values(generator):
    """Test action column contains valid values"""
    df = generator.generate_signals("AAPL")
    valid_actions = {'BUY', 'SELL', 'HOLD'}
    assert set(df['action'].unique()).issubset(valid_actions)


def test_generate_signals_score_range(generator):
    """Test signal_score is within expected range"""
    df = generator.generate_signals("AAPL")
    # Score is weighted sum: RSI(2) + MACD(2) + MA(2) + BB(1) = max 7, min -7
    assert df['signal_score'].min() >= -7
    assert df['signal_score'].max() <= 7


def test_generate_signals_strength_range(generator):
    """Test signal_strength is between 0 and 100"""
    df = generator.generate_signals("AAPL")
    assert df['signal_strength'].min() >= 0
    assert df['signal_strength'].max() <= 100


# ============================================
# 🎯 LATEST SIGNAL TESTS
# ============================================

def test_get_latest_signal_structure(generator):
    """Test get_latest_signal returns dict with expected keys"""
    sig = generator.get_latest_signal("AAPL")
    
    assert isinstance(sig, dict)
    assert 'symbol' in sig
    assert 'timestamp' in sig
    assert 'price' in sig
    assert 'action' in sig
    assert 'signal_score' in sig
    assert 'signal_strength' in sig
    assert 'indicators' in sig
    assert 'change_pct' in sig


def test_get_latest_signal_values(generator):
    """Test get_latest_signal returns valid values"""
    sig = generator.get_latest_signal("AAPL")
    
    assert sig['symbol'] == 'AAPL'
    assert sig['action'] in ['BUY', 'SELL', 'HOLD']
    assert isinstance(sig['price'], float)
    assert sig['price'] > 0
    assert isinstance(sig['signal_score'], int)
    assert isinstance(sig['signal_strength'], float)
    assert 0 <= sig['signal_strength'] <= 100
    assert isinstance(sig['indicators'], dict)
    assert 'RSI' in sig['indicators']
    assert 'MACD' in sig['indicators']
    assert 'BB_position' in sig['indicators']


def test_get_latest_signal_rsi_range(generator):
    """Test RSI indicator is within valid range"""
    sig = generator.get_latest_signal("AAPL")
    rsi = sig['indicators']['RSI']
    assert 0 <= rsi <= 100


def test_get_latest_signal_bb_position_range(generator):
    """Test BB_position is within valid range"""
    sig = generator.get_latest_signal("AAPL")
    bb_pos = sig['indicators']['BB_position']
    assert 0 <= bb_pos <= 1


# ============================================
# 🧠 INDICATOR CALCULATION TESTS
# ============================================

def test_rsi_calculation(generator, sample_data):
    """Test RSI calculation returns valid values"""
    rsi = generator._rsi(sample_data['Close'], period=14)
    assert rsi is not None
    assert len(rsi) == len(sample_data)
    # RSI should be between 0 and 100 (excluding NaNs)
    valid_rsi = rsi.dropna()
    assert valid_rsi.min() >= 0
    assert valid_rsi.max() <= 100


def test_sma_calculation(generator, sample_data):
    """Test SMA calculation returns valid values"""
    sma = generator._sma(sample_data['Close'], period=20)
    assert sma is not None
    assert len(sma) == len(sample_data)
    # SMA should be positive for positive prices
    valid_sma = sma.dropna()
    assert valid_sma.min() > 0


# ============================================
# 📋 MULTI-SYMBOL TESTS
# ============================================

@pytest.mark.parametrize("symbol", ["AAPL", "MSFT", "GOOGL"])
def test_multiple_symbols(generator, symbol):
    """Test signal generation for multiple symbols"""
    sig = generator.get_latest_signal(symbol)
    assert sig['symbol'] == symbol
    assert sig['action'] in ['BUY', 'SELL', 'HOLD']
    assert sig['price'] > 0


# ============================================
# 🏁 END OF TESTS
# ============================================

if __name__ == "__main__":
    # Allow running tests directly with: python tests/test_signals.py
    pytest.main([__file__, "-v"])
