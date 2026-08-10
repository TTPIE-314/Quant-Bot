"""
Trading Strategies Module
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class Action(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class TradeSignal:
    """Represents a trading signal"""
    symbol: str
    action: Action
    price: float
    timestamp: datetime
    confidence: float  # 0-1
    reason: str
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class PositionSizer:
    """Calculate position sizes based on risk management"""
    
    def __init__(self, max_position_pct: float = 0.10, 
                 stop_loss_pct: float = 0.05,
                 max_risk_per_trade: float = 0.02):
        self.max_position_pct = max_position_pct
        self.stop_loss_pct = stop_loss_pct
        self.max_risk_per_trade = max_risk_per_trade
    
    def calculate_position_size(self, portfolio_value: float, 
                                price: float,
                                confidence: float = 1.0) -> int:
        """
        Calculate number of shares to buy based on Kelly-inspired sizing
        
        Args:
            portfolio_value: Total portfolio value
            price: Current stock price
            confidence: Signal confidence (0-1)
        
        Returns:
            Number of shares to buy
        """
        # Base position size
        max_position_value = portfolio_value * self.max_position_pct
        
        # Adjust by confidence
        position_value = max_position_value * confidence
        
        # Risk-based sizing
        risk_per_share = price * self.stop_loss_pct
        max_risk = portfolio_value * self.max_risk_per_trade
        risk_based_shares = max_risk / risk_per_share if risk_per_share > 0 else 0
        
        # Use smaller of value-based and risk-based
        value_based_shares = position_value / price
        shares = min(value_based_shares, risk_based_shares)
        
        return int(shares)
    
    def calculate_stop_loss(self, entry_price: float) -> float:
        """Calculate stop loss price"""
        return entry_price * (1 - self.stop_loss_pct)
    
    def calculate_take_profit(self, entry_price: float, 
                              risk_reward_ratio: float = 2.0) -> float:
        """Calculate take profit price"""
        risk = entry_price * self.stop_loss_pct
        reward = risk * risk_reward_ratio
        return entry_price + reward


class MultiIndicatorStrategy:
    """
    Multi-indicator trading strategy with risk management
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.position_sizer = PositionSizer(
            max_position_pct=config.get('max_position_pct', 0.10),
            stop_loss_pct=config.get('stop_loss_pct', 0.05)
        )
        self.positions: Dict[str, Dict] = {}
    
    def evaluate_signal(self, signal_data: Dict, 
                       portfolio_value: float,
                       cash: float) -> Optional[TradeSignal]:
        """
        Evaluate a signal and return trade recommendation
        
        Args:
            signal_data: Signal data from SignalGenerator
            portfolio_value: Current portfolio value
            cash: Available cash
        
        Returns:
            TradeSignal if action recommended, None otherwise
        """
        symbol = signal_data['symbol']
        action = signal_data['action']
        price = signal_data['price']
        score = signal_data['signal_score']
        strength = signal_data['signal_strength']
        
        # Calculate confidence
        confidence = min(strength / 100, 1.0)
        
        # Check if we have a position
        has_position = symbol in self.positions
        
        # Generate trade signal
        if action == 'BUY' and not has_position:
            # Check if we have enough cash
            position_size = self.position_sizer.calculate_position_size(
                portfolio_value, price, confidence
            )
            cost = position_size * price
            
            if cost > cash:
                # Reduce position size to fit cash
                position_size = int(cash / price * 0.95)  # Leave 5% buffer
            
            if position_size > 0:
                stop_loss = self.position_sizer.calculate_stop_loss(price)
                take_profit = self.position_sizer.calculate_take_profit(price)
                
                return TradeSignal(
                    symbol=symbol,
                    action=Action.BUY,
                    price=price,
                    timestamp=signal_data['timestamp'],
                    confidence=confidence,
                    reason=f"BUY signal: score={score}, strength={strength:.1f}%",
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )
        
        elif action == 'SELL' and has_position:
            return TradeSignal(
                symbol=symbol,
                action=Action.SELL,
                price=price,
                timestamp=signal_data['timestamp'],
                confidence=confidence,
                reason=f"SELL signal: score={score}, strength={strength:.1f}%"
            )
        
        # Check stop loss / take profit
        if has_position:
            position = self.positions[symbol]
            entry_price = position['entry_price']
            
            if price <= position.get('stop_loss', 0):
                return TradeSignal(
                    symbol=symbol,
                    action=Action.SELL,
                    price=price,
                    timestamp=signal_data['timestamp'],
                    confidence=1.0,
                    reason=f"Stop loss triggered: ${price:.2f} <= ${position['stop_loss']:.2f}"
                )
            
            if price >= position.get('take_profit', float('inf')):
                return TradeSignal(
                    symbol=symbol,
                    action=Action.SELL,
                    price=price,
                    timestamp=signal_data['timestamp'],
                    confidence=1.0,
                    reason=f"Take profit triggered: ${price:.2f} >= ${position['take_profit']:.2f}"
                )
        
        return None
    
    def update_position(self, symbol: str, action: Action, 
                       price: float, quantity: int,
                       stop_loss: float = None,
                       take_profit: float = None):
        """Update internal position tracking"""
        if action == Action.BUY:
            self.positions[symbol] = {
                'quantity': quantity,
                'entry_price': price,
                'entry_date': datetime.now(),
                'stop_loss': stop_loss,
                'take_profit': take_profit
            }
        elif action == Action.SELL and symbol in self.positions:
            del self.positions[symbol]
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get position for a symbol"""
        return self.positions.get(symbol)


# Quick test
if __name__ == "__main__":
    print("🧪 Testing Strategy Module...")
    
    config = {
        'max_position_pct': 0.10,
        'stop_loss_pct': 0.05
    }
    
    strategy = MultiIndicatorStrategy(config)
    sizer = strategy.position_sizer
    
    # Test position sizing
    portfolio = 100000
    price = 150
    size = sizer.calculate_position_size(portfolio, price, confidence=0.8)
    print(f"\n📦 Position Size Test:")
    print(f"   Portfolio: ${portfolio}")
    print(f"   Price: ${price}")
    print(f"   Shares to buy: {size}")
    print(f"   Position value: ${size * price:.2f}")
    
    # Test stop loss / take profit
    sl = sizer.calculate_stop_loss(price)
    tp = sizer.calculate_take_profit(price)
    print(f"\n🎯 Risk Management:")
    print(f"   Stop Loss: ${sl:.2f}")
    print(f"   Take Profit: ${tp:.2f}")
    print(f"   Risk/Reward: {(tp - price) / (price - sl):.2f}")