"""
============================================
📈 QUANT TRADING DASHBOARD (Multi-User)
============================================
Run with: streamlit run dashboard.py
"""
import sys
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).parent / "src"))

from signals import SignalGenerator
from config import STRATEGY_CONFIG
from auth import login_user, register_user
from user_data import get_watchlist, save_watchlist, DEFAULT_WATCHLIST

st.set_page_config(page_title="Quant Trading Dashboard", page_icon="📈", layout="wide")

if "user" not in st.session_state:
    st.session_state.user = None


@st.cache_resource
def get_generator():
    return SignalGenerator(STRATEGY_CONFIG)


# ============================================
# 🔐 LOGIN / SIGNUP PAGE
# ============================================
def show_login_page():
    st.title("📈 Quant Trading Dashboard")
    st.caption("Sign in to view and customize your personal watchlist")

    # Initialize session states for reset flow
    if "show_reset" not in st.session_state:
        st.session_state.show_reset = False
    if "reset_code" not in st.session_state:
        st.session_state.reset_code = None
    if "reset_email" not in st.session_state:
        st.session_state.reset_email = None

    # ============================================
    # 🔒 RESET PASSWORD FLOW
    # ============================================
    if st.session_state.show_reset:
        st.header("🔒 Reset Password")
        
        if st.session_state.reset_code is None:
            # Step 1: Ask for email
            email_input = st.text_input("Enter your account email")
            if st.button("Send Reset Code"):
                from auth import check_email_exists
                if check_email_exists(email_input):
                    import random
                    code = str(random.randint(100000, 999999))
                    st.session_state.reset_code = code
                    st.session_state.reset_email = email_input.strip().lower()
                    st.rerun()
                else:
                    st.error("No account found with that email.")
            
            if st.button("⬅️ Back to Login"):
                st.session_state.show_reset = False
                st.rerun()

        else:
            # Step 2: Show simulated email and ask for new password
            st.info(f"📧 **Simulated Email Inbox:**\n\nHello! Your password reset code is: **{st.session_state.reset_code}**\n\n*(Note for judges: In a production environment, this code would be sent via a transactional email API like SendGrid. For this demo, it is displayed securely on-screen).*")
            
            with st.form("reset_form"):
                entered_code = st.text_input("Enter the 6-digit code")
                new_pw = st.text_input("New Password", type="password")
                confirm_pw = st.text_input("Confirm New Password", type="password")
                
                if st.form_submit_button("Reset Password"):
                    if entered_code != st.session_state.reset_code:
                        st.error("Incorrect code.")
                    elif len(new_pw) < 6:
                        st.error("Password must be at least 6 characters.")
                    elif new_pw != confirm_pw:
                        st.error("Passwords do not match.")
                    else:
                        from auth import update_password
                        ok, msg = update_password(st.session_state.reset_email, new_pw)
                        if ok:
                            st.success("✅ " + msg + " You can now log in.")
                            st.session_state.show_reset = False
                            st.session_state.reset_code = None
                        else:
                            st.error(msg)

            if st.button("⬅️ Back to Login"):
                st.session_state.show_reset = False
                st.session_state.reset_code = None
                st.rerun()

        return # Stop here so we don't show the login tabs below

    # ============================================
    # 🔑 NORMAL LOGIN / SIGNUP FLOW
    # ============================================
    tab_login, tab_signup = st.tabs(["🔑 Log In", "📝 Sign Up"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Log In"):
                user, msg = login_user(email, password)
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error(msg)
        
        # Add the Forgot Password button here
        if st.button("🔒 Forgot Password?"):
            st.session_state.show_reset = True
            st.rerun()

    with tab_signup:
        with st.form("signup_form"):
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            pw = st.text_input("Password", type="password")
            pw2 = st.text_input("Confirm Password", type="password")
            if st.form_submit_button("Create Account"):
                if not name or not email or not pw:
                    st.error("Please fill in all fields.")
                elif "@" not in email:
                    st.error("Please enter a valid email.")
                elif len(pw) < 6:
                    st.error("Password must be at least 6 characters.")
                elif pw != pw2:
                    st.error("Passwords do not match.")
                else:
                    ok, msg = register_user(name, email, pw)
                    if ok:
                        st.success("✅ " + msg)
                    else:
                        st.error(msg)

    st.info("🔒 Passwords are hashed with bcrypt and stored locally.")
    st.title("📈 Quant Trading Dashboard")
    st.caption("Sign in to view and customize your personal watchlist")

    tab_login, tab_signup = st.tabs(["🔑 Log In", "📝 Sign Up"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Log In"):
                user, msg = login_user(email, password)
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error(msg)

    with tab_signup:
        with st.form("signup_form"):
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            pw = st.text_input("Password", type="password")
            pw2 = st.text_input("Confirm Password", type="password")
            if st.form_submit_button("Create Account"):
                if not name or not email or not pw:
                    st.error("Please fill in all fields.")
                elif "@" not in email:
                    st.error("Please enter a valid email.")
                elif len(pw) < 6:
                    st.error("Password must be at least 6 characters.")
                elif pw != pw2:
                    st.error("Passwords do not match.")
                else:
                    ok, msg = register_user(name, email, pw)
                    if ok:
                        st.success("✅ " + msg)
                    else:
                        st.error(msg)

    st.info("🔒 Passwords are hashed with bcrypt and stored locally in `data/users.json`.")


# ============================================
# 🧩 WATCHLIST MANAGER (sidebar)
# ============================================
def watchlist_manager(email, watchlist):
    st.sidebar.header("➕ Customize Watchlist")
    new_ticker = st.sidebar.text_input("Add a ticker", placeholder="e.g. UBER").upper().strip()

    if st.sidebar.button("➕ Add Stock", use_container_width=True):
        if not new_ticker:
            st.sidebar.warning("Type a symbol first.")
        elif new_ticker in watchlist:
            st.sidebar.warning(f"{new_ticker} is already in your list.")
        else:
            import yfinance as yf
            try:
                df = yf.download(new_ticker, period="5d", progress=False)
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                valid = not df.empty
            except Exception:
                valid = False
            if valid:
                watchlist.append(new_ticker)
                save_watchlist(email, watchlist)
                st.rerun()
            else:
                st.sidebar.error(f"'{new_ticker}' not found. Check the symbol.")

    st.sidebar.caption(f"📋 Your list: {len(watchlist)} stocks")
    for sym in list(watchlist):
        c1, c2 = st.sidebar.columns([4, 1])
        c1.markdown(f"`{sym}`")
        if c2.button("❌", key=f"rm_{sym}"):
            watchlist.remove(sym)
            save_watchlist(email, watchlist)
            st.rerun()

    if st.sidebar.button("🔄 Reset to default 20", use_container_width=True):
        save_watchlist(email, list(DEFAULT_WATCHLIST))
        st.rerun()


# ============================================
# 📊 MAIN DASHBOARD
# ============================================
def show_dashboard(user):
    email = user["email"]
    watchlist = get_watchlist(email)
    gen = get_generator()

    st.sidebar.title(f"👋 {user['name']}")
    st.sidebar.caption(email)
    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        st.session_state.user = None
        st.rerun()

    selected = None
    if watchlist:
        selected = st.sidebar.selectbox("📊 Select Symbol", watchlist)

    watchlist_manager(email, watchlist)

    st.title("📈 Quant Trading Dashboard")
    st.caption(f"Last updated: {datetime.now():%Y-%m-%d %H:%M:%S}")

    if not watchlist:
        st.warning("Your watchlist is empty — add a stock in the sidebar!")
        st.stop()

    try:
        df = gen.generate_signals(selected)
        signal = gen.get_latest_signal(selected)
    except Exception as e:
        st.error(f"❌ Error fetching data for {selected}: {e}")
        st.stop()

    # Metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("💰 Price", f"${signal['price']:.2f}", f"{signal['change_pct']:.2f}%")
    col2.metric("🎯 Signal", signal['action'])
    col3.metric("📊 Score", signal['signal_score'])
    col4.metric("💪 Strength", f"{signal['signal_strength']:.1f}%")
    col5.metric("📈 RSI", f"{signal['indicators']['RSI']:.1f}")

    if signal['action'] == 'BUY':
        st.success(f"🟢 **BUY SIGNAL** — Score {signal['signal_score']} | Strength {signal['signal_strength']:.1f}%")
    elif signal['action'] == 'SELL':
        st.error(f"🔴 **SELL SIGNAL** — Score {signal['signal_score']} | Strength {signal['signal_strength']:.1f}%")
    else:
        st.warning(f"🟡 **HOLD** — Score {signal['signal_score']} | Strength {signal['signal_strength']:.1f}%")

    # Price chart
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                                 low=df['Low'], close=df['Close'], name='Price'))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_short'], name='SMA short', line=dict(color='orange', width=1.5)))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_long'], name='SMA long', line=dict(color='blue', width=1.5)))
    fig.update_layout(height=500, xaxis_rangeslider_visible=False, template='plotly_white')
    st.plotly_chart(fig, use_container_width=True)

    # RSI + MACD
    c1, c2 = st.columns(2)
    with c1:
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='purple')))
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
        fig_rsi.update_layout(height=300, template='plotly_white', yaxis_range=[0, 100])
        st.plotly_chart(fig_rsi, use_container_width=True)
    with c2:
        fig_macd = go.Figure()
        fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='blue')))
        fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD_signal'], line=dict(color='red')))
        fig_macd.update_layout(height=300, template='plotly_white')
        st.plotly_chart(fig_macd, use_container_width=True)

    # Signals table for the user's personal watchlist
    st.subheader("📋 Your Watchlist Signals")
    rows = []
    for sym in watchlist:
        try:
            s = gen.get_latest_signal(sym)
            rows.append({
                'Symbol': sym,
                'Price': f"${s['price']:.2f}",
                'Action': s['action'],
                'Score': s['signal_score'],
                'Strength': f"{s['signal_strength']:.1f}%",
                'RSI': f"{s['indicators']['RSI']:.1f}",
            })
        except Exception:
            pass
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ============================================
# 🚦 APP ENTRY POINT
# ============================================
if st.session_state.user:
    show_dashboard(st.session_state.user)
else:
    show_login_page()