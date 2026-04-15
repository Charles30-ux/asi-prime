import os
import time
import random
import hashlib
from datetime import datetime, timezone
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import psycopg2
import requests
import streamlit.components.v1 as components

# ==========================================
# PAGE CONFIGURATION & BULKTRADE CSS
# ==========================================
st.set_page_config(page_title="ASI Prime OMS", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Mobile Safe Area & Bulktrade Theme */
    .block-container { 
        padding-top: max(2rem, env(safe-area-inset-top)) !important; 
        padding-bottom: 4rem !important; 
        max-width: 1600px;
    }
    .stApp { background-color: #0B0E14; color: #8B9BB4; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
    header, #MainMenu, footer { visibility: hidden; }
    
    /* Clean Text-Only Tabs (Bulktrade Style) */
    .stTabs [data-baseweb="tab-list"] { gap: 0px; background-color: transparent; border-bottom: 1px solid #1A2235; padding: 0; }
    .stTabs [data-baseweb="tab"] { background-color: transparent; border: none; padding: 15px 20px; color: #8B9BB4; font-size: 14px; font-weight: 500; text-transform: capitalize; }
    .stTabs [aria-selected="true"] { color: #00FF88 !important; border-bottom: 2px solid #00FF88 !important; background-color: transparent !important; }
    
    /* Metric Cards matching screenshot */
    div[data-testid="metric-container"] { background-color: #121826; border: 1px solid #1A2235; padding: 16px; border-radius: 8px; box-shadow: none; }
    div[data-testid="metric-container"] label { color: #8B9BB4 !important; font-size: 12px !important; font-weight: 500 !important; }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 20px !important; font-weight: 600 !important; margin-top: 4px; }
    
    .card { background-color: #121826; padding: 20px; border-radius: 12px; border: 1px solid #1A2235; margin-bottom: 16px; }
    .section-header { color: #FFFFFF; font-size: 16px; font-weight: 600; margin-bottom: 16px; }
    
    /* Fixed Footer */
    .fixed-footer { position: fixed; bottom: 0; left: 0; width: 100%; background-color: #0B0E14; border-top: 1px solid #1A2235; color: #8B9BB4; text-align: center; padding: 12px; font-size: 10px; font-family: monospace; letter-spacing: 1px; z-index: 9999; }
    
    /* Inputs & Buttons */
    .stTextInput>div>div>input { background-color: #121826; color: #fff; border: 1px solid #1A2235; border-radius: 6px; }
    .stSelectbox>div>div>div { background-color: #121826; color: #fff; border: 1px solid #1A2235; border-radius: 6px; }
    .stButton>button { background-color: #00FF88; color: #0B0E14; font-weight: 600; border-radius: 6px; border: none; transition: opacity 0.2s; }
    .stButton>button:hover { opacity: 0.8; }
    </style>
    <div class="fixed-footer">ASI PRIME OMS © 2026 • REGULATORY COMPLIANT NODE</div>
""", unsafe_allow_html=True)

# ==========================================
# SECURE VAULT
# ==========================================
USERS = {
    os.getenv("ADMIN_USER", "admin"): {"pass": os.getenv("ADMIN_PASS", "adminpass"), "role": "ADMIN"},
    os.getenv("PM_USER", "pm"): {"pass": os.getenv("PM_PASS", "pmpass"), "role": "PM"},
    os.getenv("TRADER_USER", "trader"): {"pass": os.getenv("TRADER_PASS", "traderpass"), "role": "TRADER"},
    os.getenv("RISK_USER", "risk"): {"pass": os.getenv("RISK_PASS", "riskpass"), "role": "RISK"}
}

MARKET_UNIVERSE = ["AAPL", "NVDA", "TSLA", "MSFT", "AMD", "META", "AMZN", "SOL", "AVAX", "ETH", "BTC"]

# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================
if 'authenticated' not in st.session_state:
    st.session_state.update({
        "authenticated": False, "role": None, "username": None, 
        "hist_var": [np.random.normal(1.27, 0.5) for _ in range(30)], 
        "blotter": [], "logs": [], "portfolio_equity": 1420550.00
    })

def log_event(msg, level="INFO"):
    t = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.insert(0, f"[{t}] [{level}] {msg}")
    if len(st.session_state.logs) > 50: st.session_state.logs.pop()

# ==========================================
# LOGIN SCREEN
# ==========================================
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br><br><div style='text-align:center;'><svg width='40' height='40' viewBox='0 0 24 24' fill='none' stroke='#00FF88' stroke-width='2'><path d='M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5'/></svg><h1 style='color:#FFFFFF; font-size:32px; margin-top:10px;'>BULKTRADE <span style='color:#00FF88; font-size:14px; vertical-align:middle;'>OMS</span></h1></div>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("AUTHORIZATION ID")
            password = st.text_input("DECRYPTION KEY", type="password")
            submit = st.form_submit_button("AUTHENTICATE", use_container_width=True)
            
            if submit:
                user_data = USERS.get(username)
                if user_data and user_data["pass"] == password:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.role = user_data["role"]
                    log_event(f"User {username} authenticated with clearance {user_data['role']}", "SUCCESS")
                    st.rerun()
                else:
                    st.error("Invalid Credentials.")
    st.stop()

# ==========================================
# HEADER
# ==========================================
st.markdown(f"""
    <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;'>
        <div style='display:flex; align-items:center; gap:10px;'>
            <svg width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='#00FF88' stroke-width='2'><path d='M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5'/></svg>
            <h2 style='color:white; margin:0; font-size:20px; font-weight:600;'>BULKTRADE</h2>
        </div>
        <div style='display:flex; gap:15px; font-size:12px; color:#8B9BB4; font-weight:500;'>
            <span>BTC <strong style='color:white;'>$74.77K</strong></span>
            <span>ETH <strong style='color:white;'>$2.38K</strong></span>
            <span>BNB <strong style='color:white;'>$615.2</strong></span>
        </div>
    </div>
    <h2 style='color:white; font-size:24px; font-weight:600; margin-bottom:20px;'><span style='color:#00FF88;'>{st.session_state.username.capitalize()}'s</span> Dashboard</h2>
""", unsafe_allow_html=True)

# ==========================================
# TABS (Text Only, like screenshot)
# ==========================================
tabs = st.tabs([
    "Dashboard", "Portfolio", "Macro News", "Alpha Setups", 
    "Smart Trading", "Shadow Ledger", "Backtest", 
    "Compliance", "System Logs", "Settings"
])

# --- TAB 1: DASHBOARD ---
@st.fragment(run_every=5)
def render_dashboard():
    # DL Engine Canvas Injection
    components.html("""
        <div style="background-color:#121826; border:1px solid #1A2235; border-radius:12px; height:280px; position:relative; overflow:hidden;">
            <canvas id="dlCanvas" style="width:100%; height:100%;"></canvas>
            <div style="position:absolute; top:20px; left:20px; color:#8B9BB4; font-family:monospace; font-size:12px; display:flex; align-items:center; gap:8px;">
                <div style="width:8px; height:8px; background-color:#00FF88; border-radius:50%; box-shadow: 0 0 10px #00FF88;"></div>
                Processing SOL...
            </div>
            <div style="position:absolute; top:20px; right:20px; color:#00FF88; font-weight:bold; font-size:14px;">+0.95% <span style="color:#8B9BB4; font-weight:normal; font-size:12px;">today</span></div>
        </div>
        <script>
            const canvas = document.getElementById('dlCanvas');
            const ctx = canvas.getContext('2d');
            canvas.width = canvas.offsetWidth; canvas.height = canvas.offsetHeight;
            
            // Simple static network rendering matching screenshot vibe
            function drawNetwork() {
                ctx.clearRect(0,0,canvas.width,canvas.height);
                const cx = canvas.width/2 + 50, cy = canvas.height/2;
                
                // Draw lines
                ctx.beginPath(); ctx.strokeStyle = 'rgba(0, 255, 136, 0.2)'; ctx.lineWidth = 1.5;
                ctx.moveTo(cx, cy); ctx.lineTo(cx-100, cy-50);
                ctx.moveTo(cx, cy); ctx.lineTo(cx-120, cy+60);
                ctx.moveTo(cx, cy); ctx.lineTo(cx+150, cy);
                ctx.moveTo(cx+150, cy); ctx.lineTo(cx+200, cy-40);
                ctx.moveTo(cx+150, cy); ctx.lineTo(cx+180, cy+50);
                ctx.stroke();
                
                // Draw nodes
                const drawNode = (x, y, r, color, glow) => {
                    ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI*2);
                    ctx.fillStyle = color; ctx.shadowColor = glow; ctx.shadowBlur = 15; ctx.fill();
                    ctx.shadowBlur = 0;
                };
                
                drawNode(cx, cy, 20, 'rgba(0,255,136,0.1)', '#00FF88');
                drawNode(cx, cy, 6, '#00FF88', 'transparent');
                
                drawNode(cx-100, cy-50, 8, '#f59e0b', 'transparent');
                drawNode(cx-120, cy+60, 6, '#3b82f6', 'transparent');
                drawNode(cx+150, cy, 12, 'rgba(0,255,136,0.3)', 'transparent');
                drawNode(cx+150, cy, 4, '#00FF88', 'transparent');
                drawNode(cx+200, cy-40, 6, '#8b5cf6', 'transparent');
                drawNode(cx+180, cy+50, 8, '#3b82f6', 'transparent');
                
                // Labels
                ctx.fillStyle = '#00FF88'; ctx.font = 'bold 12px sans-serif'; ctx.textAlign = 'center';
                ctx.fillText('+0.95%', cx, cy-35);
                ctx.fillStyle = '#8B9BB4'; ctx.font = '10px sans-serif';
                ctx.fillText('SOL LONG', cx, cy-20);
                ctx.fillText('DL Engine', cx, cy+40);
            }
            drawNetwork();
        </script>
    """, height=290)

    # Replicating 24h Growth metrics from image
    col1, col2 = st.columns(2)
    with col1: st.metric("24h Growth", "0.58%")
    with col2: st.metric("7d Growth", "9.73%")
    
    col3, col4 = st.columns(2)
    with col3: 
        st.markdown("""
        <div style='background-color:#121826; border:1px solid #00FF8830; padding:16px; border-radius:8px;'>
            <p style='color:#8B9BB4; font-size:12px; margin:0 0 4px 0; font-weight:500;'>24h PnL</p>
            <p style='color:#00FF88; font-size:20px; font-weight:600; margin:0;'>+1.27%</p>
        </div>
        """, unsafe_allow_html=True)
    with col4: st.metric("Total Trades", "597664")

    # Live Stream (Replicating bottom of screenshot)
    st.markdown("<div class='card' style='padding:0;'><table style='width:100%; border-collapse:collapse; text-align:left; font-size:14px;'><tr style='border-bottom:1px solid #1A2235;'><th style='padding:16px; color:white;'>SOL <span style='color:#00FF88; font-size:12px; font-weight:normal; margin-left:8px;'>LONG</span></th><th style='padding:16px; color:#8B9BB4;'>$2,265</th><th style='padding:16px; color:#00FF88; text-align:right;'>0.95%</th></tr><tr><th style='padding:16px; color:white;'>AVAX <span style='color:#00FF88; font-size:12px; font-weight:normal; margin-left:8px;'>LONG</span></th><th style='padding:16px; color:#8B9BB4;'>$1,982</th><th style='padding:16px; color:#00FF88; text-align:right;'>5.46%</th></tr></table></div>", unsafe_allow_html=True)

with tabs[0]: render_dashboard()

# --- TAB 2: PORTFOLIO AI ---
with tabs[1]:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("<div class='section-header'>ACTIVE POSITIONS</div>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame([{"ASSET": "SOL", "SIDE": "LONG", "ENTRY": "$145.20", "P/L": "+0.95%"}, {"ASSET": "AVAX", "SIDE": "LONG", "ENTRY": "$35.40", "P/L": "+5.46%"}]), hide_index=True, use_container_width=True)
    with col2:
        st.markdown("""
        <div class='card' style='border-color: #00FF8830;'>
            <div style='color:#00FF88; font-weight:600; font-size:14px; margin-bottom:10px;'>AI PORTFOLIO OPTIMIZER</div>
            <p style='color:#8B9BB4; font-size:13px; line-height:1.6;'>Exposure balanced. Capital efficiency maximized in Layer 1 protocols.<br><br><strong style='color:white;'>SUGGESTION:</strong><br>Trailing stops engaged on SOL. Consider unwinding 15% AVAX to capture liquidity.</p>
        </div>
        """, unsafe_allow_html=True)

# --- TAB 3: MACRO NEWS ---
with tabs[2]:
    st.markdown("<div class='section-header'>FINANCIAL TIMES ANALYTICS</div>", unsafe_allow_html=True)
    
    # Custom HTML for interactive news cards
    news_html = """
    <style>
        .n-card { background: #121826; border: 1px solid #1A2235; border-radius: 8px; overflow: hidden; margin-bottom: 20px; display: flex; flex-direction: column; }
        @media(min-width: 768px) { .n-card { flex-direction: row; height: 200px; } }
        .n-img { width: 100%; height: 150px; background-size: cover; background-position: center; }
        @media(min-width: 768px) { .n-img { width: 300px; height: 100%; } }
        .n-content { padding: 20px; display: flex; flex-direction: column; justify-content: center; flex: 1; }
    </style>
    """
    for i, sym in enumerate(["NVDA", "BTC", "AAPL"]):
        news_html += f"""
        <div class="n-card">
            <div class="n-img" style="background-image: url('https://picsum.photos/seed/{sym}news{i}/600/400');"></div>
            <div class="n-content">
                <div style="color:#00FF88; font-size:10px; font-weight:bold; letter-spacing:1px; margin-bottom:8px;">MACRO IMPACT • {sym}</div>
                <h3 style="color:white; margin:0 0 10px 0; font-size:18px;">Structural Market Shifts Detected in Sector</h3>
                <p style="color:#8B9BB4; font-size:13px; margin:0 0 15px 0; line-height:1.5; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;">Quantitative analysis shows large block accumulation. AI profitability modeling indicates a high probability of mean reversion within 72 hours.</p>
                <div style="background:#0B0E14; border:1px solid #1A2235; border-left:2px solid #3b82f6; padding:10px; border-radius:4px; font-size:11px;">
                    <span style="color:white; font-weight:bold;">AI Strategy:</span> <span style="color:#8B9BB4;">Accumulate via TWAP execution below VWAP.</span>
                </div>
            </div>
        </div>
        """
    components.html(news_html, height=700, scrolling=True)

# --- TAB 4: ALPHA SETUPS ---
with tabs[3]:
    st.markdown("<div class='section-header'>DEEP RESEARCH SIGNALS</div>", unsafe_allow_html=True)
    cols = st.columns(3)
    for i, sym in enumerate(["ETH", "MSFT", "META"]):
        with cols[i]:
            st.markdown(f"""
            <div class='card'>
                <div style='display:flex; justify-content:space-between; margin-bottom:15px;'><h3 style='color:white; margin:0;'>{sym}</h3><span style='color:#00FF88; font-size:12px; font-weight:bold;'>LONG</span></div>
                <div style='color:#8B9BB4; font-size:12px; margin-bottom:5px; display:flex; justify-content:space-between;'><span>Entry Target</span><span style='color:white;'>$120.45</span></div>
                <div style='color:#8B9BB4; font-size:12px; margin-bottom:15px; display:flex; justify-content:space-between;'><span>Confidence</span><span style='color:#a78bfa;'>89.4%</span></div>
            </div>
            """, unsafe_allow_html=True)
            st.button(f"PRE-CLEAR {sym}", key=f"alpha_{sym}", use_container_width=True)

# --- TAB 5: SMART TRADING ---
with tabs[4]:
    st.markdown("<div class='card'><div class='section-header'>ADVANCED ROUTING ALGORITHMS</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    tsym = c1.text_input("TICKER", "SOL")
    tqty = c2.number_input("QUANTITY", min_value=1, value=100)
    algo = c3.selectbox("ALGORITHM", ["VWAP Slicer", "TWAP Execution", "Dark Pool Iceberg"])
    if st.button("EXECUTE SMART ORDER", type="primary", use_container_width=True):
        st.success(f"Order routed via {algo}.")
    st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 6: SHADOW LEDGER ---
with tabs[5]:
    c1, c2 = st.columns(2)
    c1.markdown("<div class='card'><div class='section-header'>GOLDMAN SACHS PB1</div><p style='color:#8B9BB4; font-size:13px; display:flex; justify-content:space-between;'>Allocated Cash <span style='color:white;'>$852,330</span></p><p style='color:#8B9BB4; font-size:13px; display:flex; justify-content:space-between;'>Margin Utilized <span style='color:#f59e0b;'>$425,100</span></p></div>", unsafe_allow_html=True)
    c2.markdown("<div class='card'><div class='section-header'>MORGAN STANLEY PB2</div><p style='color:#8B9BB4; font-size:13px; display:flex; justify-content:space-between;'>Allocated Cash <span style='color:white;'>$568,220</span></p><p style='color:#8B9BB4; font-size:13px; display:flex; justify-content:space-between;'>Margin Utilized <span style='color:#3b82f6;'>$182,400</span></p></div>", unsafe_allow_html=True)

# --- TAB 7: BACKTEST LAB ---
with tabs[6]:
    st.markdown("<div class='card'><div class='section-header'>HISTORICAL SIMULATION</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([2, 2, 1])
    c1.text_input("ASSET", value="BTC")
    c2.selectbox("STRATEGY", ["Mean Reversion", "Momentum"])
    c3.markdown("<br>", unsafe_allow_html=True)
    if c3.button("RUN BACKTEST", use_container_width=True):
        curve = [100000]
        for _ in range(100): curve.append(curve[-1] * (1 + random.gauss(0.001, 0.015)))
        fig = go.Figure(go.Scatter(y=curve, line=dict(color='#00ff88', width=2)))
        fig.update_layout(height=250, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis=dict(gridcolor='#1A2235'))
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 8: COMPLIANCE ---
with tabs[7]:
    col1, col2 = st.columns([1, 2])
    sig = "0x" + hashlib.sha256(f"{st.session_state.username}-{datetime.now()}".encode()).hexdigest()[:32].upper()
    col1.markdown(f"<div class='card' style='height:100%;'><div class='section-header'>LEGAL ASSESSMENT</div><p style='color:#8B9BB4; font-size:12px; margin-bottom:4px;'>MiFID II COMPLIANCE</p><p style='color:white; font-size:13px; line-height:1.5;'>Orders adhered to SEC Rule 613 formatting. Best Execution protocols verified. No mandate breaches.</p><p style='color:#8B9BB4; font-size:10px; margin-top:20px; border-top:1px solid #1A2235; padding-top:10px;'>DIGITAL SIGNATURE</p><p style='color:#a78bfa; font-family:monospace; font-size:10px; word-break:break-all;'>{sig}</p></div>", unsafe_allow_html=True)
    col2.markdown("<div class='card' style='height:100%;'><div class='section-header'>OATS AUDIT LOG</div><table style='width:100%; text-align:left; font-size:12px;'><tr style='color:#8B9BB4; border-bottom:1px solid #1A2235;'><th style='padding:8px 0;'>TIME</th><th>ID</th><th>SYM</th><th style='color:#00FF88;'>STATUS</th></tr><tr><td style='padding:8px 0; color:#8B9BB4;'>14:22:10</td><td style='color:white; font-family:monospace;'>CAT-8F92A</td><td style='color:white;'>SOL</td><td style='color:#00FF88;'>FILLED</td></tr><tr><td style='padding:8px 0; color:#8B9BB4;'>14:20:05</td><td style='color:white; font-family:monospace;'>CAT-2B19C</td><td style='color:white;'>AVAX</td><td style='color:#00FF88;'>FILLED</td></tr></table></div>", unsafe_allow_html=True)

# --- TAB 9: SYSTEM LOGS ---
with tabs[8]:
    st.markdown("<div class='card' style='background:#000;'><div class='section-header'>TCP TERMINAL</div><div style='font-family:monospace; font-size:12px; color:#a3a3a3;'>[SYSTEM] Boot sequence initiated...<br>[SUCCESS] Fix Gateway attached.<br>[INFO] Streaming market data...</div></div>", unsafe_allow_html=True)

# --- TAB 10: SETTINGS ---
with tabs[9]:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div class='card'><div class='section-header'>PREFERENCES</div>", unsafe_allow_html=True)
        st.selectbox("THEME", ["Bulktrade Dark"])
        st.selectbox("LANGUAGE", ["English (US)", "Français"])
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='card'><div class='section-header'>SESSION</div>", unsafe_allow_html=True)
        if st.button("SECURE LOGOUT", type="primary", use_container_width=True):
            st.session_state.clear()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
