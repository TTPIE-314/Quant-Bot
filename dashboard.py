"""
============================================
📈 QUANT TRADING DASHBOARD
============================================
Streamlit dashboard for monitoring signals and portfolio
Run with: streamlit run dashboard.py
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from signals import SignalGenerator
from config import STRATEGY_CONFIG, WATCHLIST

# Page config
st.set_page_config(
    page_title="Quant Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #4CAF50;
}
.buy-signal { border-left-color: #4CAF50; }
.sell-signal { border-left-color: #f44336; }
.hold-signal { border-left-color: #ff9800; }
</style>
""", unsafe_allow_html=True)

# Title
st.title("📈 Quant Trading Dashboard")
st.caption(f"Last updated: {datetime.now():%Y-%m-%d %H:%M:%S}")

# Sidebar
st.sidebar.header("⚙️ Settings")
selected_symbol = st.sidebar.selectbox("📊 Select Symbol", WATCHLIST, index=0)
auto_refresh = st.sidebar.checkbox("🔄 Auto Refresh", value=False)
show_all_signals = st.sidebar.checkbox("📋 Show All Signals", value=True)

# Initialize signal generator
@st.cache_resource
def get_generator():
    return SignalGenerator(STRATEGY_CONFIG)

generator = get_generator()

# Generate signals
try:
    df = generator.generate_signals(selected_symbol)
    signal = generator.get_latest_signal(selected_symbol)
except Exception as e:
    st.error(f"❌ Error fetching data for {selected_symbol}: {e}")
    st.stop()

# Metrics Row
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    delta = signal['change_pct']
    st.metric(
        label="💰 Price",
        value=f"${signal['price']:.2f}",
        delta=f"{delta:.2f}%",
        delta_color="normal"
    )

with col2:
    action = signal['action']
    st.metric(
        label="🎯 Signal",
        value=action,
        delta=None
    )

with col3:
    st.metric(
        label="📊 Score",
        value=signal['signal_score'],
        delta=None
    )

with col4:
    st.metric(
        label="💪 Strength",
        value=f"{signal['signal_strength']:.1f}%",
        delta=None
    )

with col5:
    rsi = signal['indicators']['RSI']
    st.metric(
        label="📈 RSI",
        value=f"{rsi:.1f}",
        delta=None
    )

# Signal badge
if action == 'BUY':
    st.success(f"🟢 **BUY SIGNAL** - Score: {signal['signal_score']} | Strength: {signal['signal_strength']:.1f}%")
elif action == 'SELL':
    st.error(f"🔴 **SELL SIGNAL** - Score: {signal['signal_score']} | Strength: {signal['signal_strength']:.1f}%")
else:
    st.warning(f"🟡 **HOLD** - Score: {signal['signal_score']} | Strength: {signal['signal_strength']:.1f}%")

# Price Chart
st.subheader(f"📊 {selected_symbol} Price Chart")

fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=df.index,
    open=df['Open'],
    high=df['High'],
    low=df['Low'],
    close=df['Close'],
    name='Price'
))
fig.add_trace(go.Scatter(
    x=df.index,
    y=df['SMA_short'],
    name=f"SMA {STRATEGY_CONFIG['sma_short']}",
    line=dict(color='orange', width=1.5)
))
fig.add_trace(go.Scatter(
    x=df.index,
    y=df['SMA_long'],
    name=f"SMA {STRATEGY_CONFIG['sma_long']}",
    line=dict(color='blue', width=1.5)
))
fig.add_trace(go.Scatter(
    x=df.index,
    y=df['BB_upper'],
    name='BB Upper',
    line=dict(color='gray', width=1, dash='dash'),
    opacity=0.5
))
fig.add_trace(go.Scatter(
    x=df.index,
    y=df['BB_lower'],
    name='BB Lower',
    line=dict(color='gray', width=1, dash='dash'),
    opacity=0.5
))
fig.update_layout(
    height=500,
    xaxis_rangeslider_visible=False,
    template='plotly_white',
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
)
st.plotly_chart(fig, use_container_width=True)

# Indicators
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 RSI (Relative Strength Index)")
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='purple')))
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, annotation_text="Overbought")
    fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, annotation_text="Oversold")
    fig_rsi.add_hline(y=50, line_dash="dot", line_color="gray", opacity=0.3)
    fig_rsi.update_layout(height=300, template='plotly_white', yaxis_range=[0, 100])
    st.plotly_chart(fig_rsi, use_container_width=True)

with col2:
    st.subheader("📊 MACD (Moving Average Convergence Divergence)")
    fig_macd = go.Figure()
    fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='blue')))
    fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD_signal'], name='Signal', line=dict(color='red')))
    fig_macd.add_trace(go.Bar(x=df.index, y=df['MACD_hist'], name='Histogram', marker_color='gray', opacity=0.5))
    fig_macd.update_layout(height=300, template='plotly_white')
    st.plotly_chart(fig_macd, use_container_width=True)

# Bollinger Bands Position
st.subheader("📊 Bollinger Bands Position")
fig_bb = go.Figure()
fig_bb.add_trace(go.Scatter(x=df.index, y=df['BB_position'], name='BB Position', line=dict(color='teal')))
fig_bb.add_hline(y=0.8, line_dash="dash", line_color="red", opacity=0.5, annotation_text="Overbought")
fig_bb.add_hline(y=0.2, line_dash="dash", line_color="green", opacity=0.5, annotation_text="Oversold")
fig_bb.update_layout(height=250, template='plotly_white', yaxis_range=[0, 1])
st.plotly_chart(fig_bb, use_container_width=True)

# All Signals Table
if show_all_signals:
    st.subheader("📋 All Watchlist Signals")
    
    signals_data = []
    for sym in WATCHLIST:
        try:
            sig = generator.get_latest_signal(sym)
            signals_data.append({
                'Symbol': sig['symbol'],
                'Price': sig['price'],
                'Action': sig['action'],
                'Score': sig['signal_score'],
                'Strength': sig['signal_strength'],
                'RSI': sig['indicators']['RSI'],
                'Change %': sig['change_pct']
            })
        except Exception:
            pass
    
    if signals_data:
        signals_df = pd.DataFrame(signals_data)
        
        # Format columns
        signals_df['Price'] = signals_df['Price'].apply(lambda x: f"${x:.2f}")
        signals_df['Strength'] = signals_df['Strength'].apply(lambda x: f"{x:.1f}%")
        signals_df['RSI'] = signals_df['RSI'].apply(lambda x: f"{x:.1f}")
        signals_df['Change %'] = signals_df['Change %'].apply(lambda x: f"{x:.2f}%")
        
        # Highlight buy/sell signals
        def highlight_action(row):
            if row['Action'] == 'BUY':
                return ['background-color: #d4edda; color: #155724'] * len(row)
            elif row['Action'] == 'SELL':
                return ['background-color: #f8d7da; color: #721c24'] * len(row)
            return [''] * len(row)
        
        st.dataframe(
            signals_df.style.apply(highlight_action, axis=1),
            use_container_width=True,
            hide_index=True
        )
        
        # Summary stats
        col1, col2, col3 = st.columns(3)
        buy_count = len(signals_df[signals_df['Action'] == 'BUY'])
        sell_count = len(signals_df[signals_df['Action'] == 'SELL'])
        hold_count = len(signals_df[signals_df['Action'] == 'HOLD'])
        
        col1.metric("🟢 Buy Signals", buy_count)
        col2.metric("🔴 Sell Signals", sell_count)
        col3.metric("🟡 Hold Signals", hold_count)

# Footer
st.markdown("---")
st.caption("🤖 Quant Trading Bot Dashboard | For educational purposes only")

# Auto-refresh
if auto_refresh:
    import time
    time.sleep(30)
    st.rerun()
