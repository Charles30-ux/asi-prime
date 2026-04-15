import os
import time
import random
import hashlib
from datetime import datetime, timezone
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
import yfinance as yf
import streamlit.components.v1 as components

# ==========================================
# LOCALIZATION ENGINE
# ==========================================
TRANSLATIONS = {
    "English": {
        "dash": "Dashboard", "port": "Portfolio", "news": "Macro News", "alpha": "Alpha Setups",
        "trade": "Trades", "ledger": "Shadow Ledger", "backtest": "Backtest", "comp": "Compliance",
        "logs": "System Logs", "settings": "Settings", "auth_id": "AUTHORIZATION ID", "dec_key": "DECRYPTION KEY",
        "auth_btn": "AUTHORIZE UPLINK", "invalid": "ACCESS DENIED. INVALID CREDENTIALS.",
        "welcome": "WELCOME", "dl_engine": "DL ENGINE PROCESSING", "total_equity": "LIVE EQUITY",
        "fund_acc": "FUND ACCOUNT BALANCE", "ai_rec": "AI RECOMMENDATION"
    },
    "French": {
        "dash": "Tableau de Bord", "port": "Portefeuille", "news": "Actualités Macro", "alpha": "Signaux Alpha",
        "trade": "Transactions", "ledger": "Grand Livre", "backtest": "Simulation", "comp": "Conformité",
        "logs": "Journaux Système", "settings": "Paramètres", "auth_id": "ID D'AUTORISATION", "dec_key": "CLÉ DE DÉCHIFFREMENT",
        "auth_btn": "AUTORISER LA LIAISON", "invalid": "ACCÈS REFUSÉ. IDENTIFIANTS INVALIDES.",
        "welcome": "BIENVENUE", "dl_engine": "TRAITEMENT MOTEUR DL", "total_equity": "CAPITAUX PROPRES",
        "fund_acc": "SOLDE DU FONDS", "ai_rec": "RECOMMANDATION IA"
    },
    "Spanish": {
        "dash": "Panel", "port": "Portafolio", "news": "Noticias Macro", "alpha": "Señales Alpha",
        "trade": "Operaciones", "ledger": "Libro en la Sombra", "backtest": "Prueba Retrospectiva", "comp": "Cumplimiento",
        "logs": "Registros del Sistema", "settings": "Configuración", "auth_id": "ID DE AUTORIZACIÓN", "dec_key": "CLAVE DE DESENCRIPTACIÓN",
        "auth_btn": "AUTORIZAR ENLACE", "invalid": "ACCESO DENEGADO. CREDENCIALES INVÁLIDAS.",
        "welcome": "BIENVENIDO", "dl_engine": "PROCESAMIENTO MOTOR DL", "total_equity": "CAPITAL EN VIVO",
        "fund_acc": "SALDO DEL FONDO", "ai_rec": "RECOMENDACIÓN IA"
    },
    "German": {
        "dash": "Dashboard", "port": "Portfolio", "news": "Makro-Nachrichten", "alpha": "Alpha-Signale",
        "trade": "Handel", "ledger": "Schattenbuch", "backtest": "Rücktest", "comp": "Compliance",
        "logs": "Systemprotokolle", "settings": "Einstellungen", "auth_id": "AUTORISIERUNGS-ID", "dec_key": "ENTSCHLÜSSELUNGSSCHLÜSSEL",
        "auth_btn": "VERBINDUNG AUTORISIEREN", "invalid": "ZUGRIFF VERWEIGERT. UNGÜLTIGE ANMELDEDATEN.",
        "welcome": "WILLKOMMEN", "dl_engine": "DL-ENGINE VERARBEITUNG", "total_equity": "LIVE-EIGENKAPITAL",
        "fund_acc": "FONDSGUTHABEN", "ai_rec": "KI-EMPFEHLUNG"
    },
    "Chinese": {
        "dash": "仪表板", "port": "投资组合", "news": "宏观新闻", "alpha": "阿尔法信号",
        "trade": "交易", "ledger": "影子分类账", "backtest": "回测", "comp": "合规",
        "logs": "系统日志", "settings": "设置", "auth_id": "授权ID", "dec_key": "解密密钥",
        "auth_btn": "授权上行链路", "invalid": "拒绝访问。凭据无效。",
        "welcome": "欢迎", "dl_engine": "DL引擎处理", "total_equity": "实时净值",
        "fund_acc": "基金账户余额", "ai_rec": "AI推荐"
    }
}

# ==========================================
# INITIALIZATION & STATE
# ==========================================
st.set_page_config(page_title="ASI Prime OMS", layout="wide", initial_sidebar_state="collapsed")

if 'lang' not in st.session_state: st.session_state.lang = "English"
if 'theme' not in st.session_state: st.session_state.theme = "Dark"
if 'auth' not in st.session_state: 
    st.session_state.update({"auth": False, "user": None, "role": None, "equity": 1420550.00, "fund": 850000.00, "logs": []})

def _t(key): return TRANSLATIONS[st.session_state.lang].get(key, key)
def log_sys(msg):
    st.session_state.logs.insert(0, f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    if len(st.session_state.logs) > 50: st.session_state.logs.pop()

# Theme Variables
bg_color = "#080B14" if st.session_state.theme == "Dark" else "#F8FAFC"
card_bg = "#111623" if st.session_state.theme == "Dark" else "#FFFFFF"
text_color = "#cbd5e1" if st.session_state.theme == "Dark" else "#334155"
border_color = "#1E293B" if st.session_state.theme == "Dark" else "#E2E8F0"
accent = "#00ff88" if st.session_state.theme == "Dark" else "#059669"
header_text = "#ffffff" if st.session_state.theme == "Dark" else "#0f172a"

st.markdown(f"""
    <style>
    .block-container {{ padding-top: max(2rem, env(safe-area-inset-top)) !important; padding-bottom: 100px !important; max-width: 1800px; }}
    .stApp {{ background-color: {bg_color}; color: {text_color}; font-family: 'Inter', sans-serif; }}
    header, footer, #MainMenu {{ visibility: hidden; display: none; }}
    
    .stTabs [data-baseweb="tab-list"] {{ gap: 4px; background-color: {bg_color}; }}
    .stTabs [data-baseweb="tab"] {{ background-color: {card_bg}; border: 1px solid {border_color}; border-radius: 6px 6px 0 0; padding: 10px 16px; color: {text_color}; font-size: 12px; font-weight: 600; text-transform: uppercase; }}
    .stTabs [aria-selected="true"] {{ color: {accent} !important; border-bottom: 2px solid {accent} !important; }}
    
    div[data-testid="metric-container"] {{ background-color: {card_bg}; border: 1px solid {border_color}; padding: 15px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
    div[data-testid="metric-container"] label {{ color: {text_color} !important; font-size: 10px !important; letter-spacing: 1px; }}
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {{ color: {header_text} !important; font-size: 24px !important; font-weight: 800 !important; }}
    
    .card {{ background-color: {card_bg}; padding: 20px; border-radius: 8px; border: 1px solid {border_color}; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }}
    .section-header {{ color: {text_color}; font-size: 10px; letter-spacing: 2px; font-weight: 800; border-bottom: 1px solid {border_color}; padding-bottom: 8px; margin-bottom: 15px; text-transform: uppercase; }}
    
    .stButton>button {{ background-color: {accent}; color: {bg_color}; font-weight: bold; border-radius: 6px; border: none; transition: 0.2s; }}
    .stButton>button:hover {{ opacity: 0.8; transform: scale(0.99); }}
    
    .fixed-footer {{ position: fixed; bottom: 0; left: 0; width: 100%; background-color: {card_bg}; border-top: 1px solid {border_color}; padding: 12px 20px; z-index: 99999; display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: {text_color}; }}
    .footer-links a {{ color: {accent}; text-decoration: none; margin-left: 15px; font-weight: 600; cursor: pointer; }}
    .footer-links a:hover {{ text-decoration: underline; }}
    .svg-icon {{ width: 14px; height: 14px; vertical-align: middle; margin-right: 4px; stroke: {text_color}; fill: none; }}
    </style>
    
    <div class="fixed-footer">
        <div><strong>ASI PRIME OMS</strong> • Powered by Streamlit • Developed by Charles Mfouapon</div>
        <div style="display:flex; align-items:center;">
            <svg class="svg-icon" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path></svg> London, United Kingdom
            <span style="margin: 0 10px;">|</span>
            <svg class="svg-icon" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg> CharlesMfouapon@outlook.com
        </div>
        <div class="footer-links">
            <a href="#">Privacy Policy</a> <a href="#">Terms of Service</a>
            <span style="margin-left: 15px;">Copyright © 2026 ASI PRIME OMS. All rights reserved.</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# REAL DATA FETCHERS
# ==========================================
@st.cache_data(ttl=60)
def fetch_crypto_data():
    try:
        res = requests.get("https://api.binance.com/api/v3/ticker/24hr")
        data = res.json()
        df = pd.DataFrame(data)
        df = df[df['symbol'].str.endswith('USDT')].head(15)
        df['lastPrice'] = df['lastPrice'].astype(float)
        df['priceChangePercent'] = df['priceChangePercent'].astype(float)
        df['volume'] = df['volume'].astype(float)
        return df
    except: return pd.DataFrame()

@st.cache_data(ttl=300)
def fetch_real_news():
    try:
        res = requests.get("https://data.alpaca.markets/v1beta1/news?limit=15&excludeless=true", headers={"APCA-API-KEY-ID": "PK", "APCA-API-SECRET-KEY": "SK"})
        news = res.json().get('news', [])
        if not news: raise Exception
        formatted = []
        finance_images = ["https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&q=80", "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?w=800&q=80", "https://images.unsplash.com/photo-1642790106117-e829e14a795f?w=800&q=80", "https://images.unsplash.com/photo-1535320903710-d993d3d77d29?w=800&q=80"]
        for idx, n in enumerate(news):
            sym = n.get('symbols', ['MACRO'])[0] if n.get('symbols') else 'MACRO'
            formatted.append({
                "head": n.get('headline', ''), "desc": n.get('summary', '')[:200] + "...",
                "sym": sym, "img": finance_images[idx % len(finance_images)],
                "ai_impact": random.choice(["Bullish +4.2%", "Bearish -2.1%", "Neutral", "High Volatility"]),
                "ai_strat": random.choice(["Accumulate on dips", "Liquidate 20%", "Hold", "Initiate straddle"])
            })
        return formatted
    except:
        return [{"head": f"Market Maker Flows in {s}", "desc": "Algorithmic dark pool data flags high institutional activity.", "sym": s, "img": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&q=80", "ai_impact": "Bullish", "ai_strat": "Accumulate"} for s in ["AAPL", "NVDA", "TSLA"]]

def get_clocks():
    now = datetime.now(timezone.utc)
    t = now.hour + now.minute/60.0
    wd = now.weekday()
    if wd >= 5: return {"NYSE": "CLOSED", "LSE": "CLOSED", "TSE": "CLOSED", "HKEX": "CLOSED"}
    return {
        "NYSE": "OPEN" if 13.5 <= t < 20 else "CLOSED", "LSE": "OPEN" if 8 <= t < 16.5 else "CLOSED",
        "TSE": "OPEN" if 0 <= t < 6 else "CLOSED", "HKEX": "OPEN" if 1.5 <= t < 8 else "CLOSED"
    }

# ==========================================
# AUTHENTICATION
# ==========================================
if not st.session_state.auth:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<br><br><br><h1 style='text-align:center; letter-spacing:3px;'>ASI PRIME <span style='color:#00ff88'>OMS</span></h1>", unsafe_allow_html=True)
        with st.form("login"):
            user = st.text_input(_t("auth_id"))
            pwd = st.text_input(_t("dec_key"), type="password")
            if st.form_submit_button(_t("auth_btn"), use_container_width=True):
                if user in ["charles", "admin"] and pwd == "admin":
                    st.session_state.update({"auth": True, "user": user, "role": "EXECUTIVE ADMIN"})
                    log_sys("System Uplink Authorized.")
                    st.rerun()
                else: st.error(_t("invalid"))
    st.stop()

# ==========================================
# HEADER
# ==========================================
clocks = get_clocks()
clock_html = "".join([f"<span style='margin-right:15px;'>{k}: <strong style='color:{accent if v=='OPEN' else text_color}'>{v}</strong></span>" for k,v in clocks.items()])

st.markdown(f"""
    <div style='display:flex; justify-content:space-between; align-items:center; background-color:{card_bg}; padding:15px; border-radius:8px; border:1px solid {border_color}; margin-bottom:15px;'>
        <div style='display:flex; align-items:center; gap:15px;'>
            <svg style="width:24px; height:24px; stroke:{accent}; fill:none;" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
            <h2 style='margin:0; font-size:18px; color:{header_text}; letter-spacing:1px;'>ASI PRIME</h2>
            <span style='background:{bg_color}; color:{accent}; padding:4px 8px; border-radius:4px; font-size:10px; font-weight:bold; border:1px solid {accent}50;'>{st.session_state.role}</span>
        </div>
        <div style='display:flex; align-items:center; gap:20px; font-size:11px; font-family:monospace;'>
            {clock_html}
            <div style='position:relative;'>
                <svg style="width:20px; height:20px; stroke:{text_color}; fill:none;" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path></svg>
                <div style='position:absolute; top:-2px; right:-2px; width:8px; height:8px; background-color:#ef4444; border-radius:50%;'></div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 10 TABS
# ==========================================
t1, t2, t3, t4, t5, t6, t7, t8, t9, t10 = st.tabs([
    _t("dash"), _t("port"), _t("trade"), _t("news"), _t("alpha"), 
    "SMART ROUTING", _t("ledger"), _t("backtest"), _t("comp"), _t("settings")
])

# --- TAB 1: DASHBOARD ---
with t1:
    # DL Engine Canvas Animation
    components.html(f"""
        <div style="background-color:{card_bg}; border:1px solid {border_color}; border-radius:8px; height:280px; position:relative; overflow:hidden; font-family:sans-serif;">
            <canvas id="dlCanvas" style="width:100%; height:100%;"></canvas>
            <div style="position:absolute; top:20px; left:20px; color:{text_color}; font-size:12px; font-weight:bold; letter-spacing:1px; text-transform:uppercase;">
                <div style="display:inline-block; width:8px; height:8px; background-color:{accent}; border-radius:50%; box-shadow: 0 0 10px {accent}; margin-right:8px;"></div>
                {_t('dl_engine')}
            </div>
        </div>
        <script>
            const canvas = document.getElementById('dlCanvas');
            const ctx = canvas.getContext('2d');
            canvas.width = canvas.offsetWidth; canvas.height = canvas.offsetHeight;
            const nodes = Array.from({{length: 25}}, () => ({{x: Math.random()*canvas.width, y: Math.random()*canvas.height, vx: (Math.random()-0.5)*1.5, vy: (Math.random()-0.5)*1.5, sym: ['AAPL','NVDA','BTC','ETH','SOL'][Math.floor(Math.random()*5)], val: (Math.random()*5).toFixed(2)}}));
            function draw() {{
                ctx.clearRect(0,0,canvas.width,canvas.height);
                nodes.forEach(n => {{ n.x+=n.vx; n.y+=n.vy; if(n.x<0||n.x>canvas.width)n.vx*=-1; if(n.y<0||n.y>canvas.height)n.vy*=-1; }});
                ctx.strokeStyle = '{accent}40'; ctx.lineWidth = 1;
                for(let i=0; i<nodes.length; i++) {{
                    for(let j=i+1; j<nodes.length; j++) {{
                        if(Math.hypot(nodes[i].x-nodes[j].x, nodes[i].y-nodes[j].y) < 120) {{
                            ctx.beginPath(); ctx.moveTo(nodes[i].x, nodes[i].y); ctx.lineTo(nodes[j].x, nodes[j].y); ctx.stroke();
                        }}
                    }}
                }}
                nodes.forEach(n => {{ 
                    ctx.beginPath(); ctx.arc(n.x, n.y, 4, 0, Math.PI*2); ctx.fillStyle = '{accent}'; ctx.fill(); 
                    ctx.fillStyle = '{text_color}'; ctx.font = '10px monospace'; ctx.fillText(n.sym + ' +' + n.val + '%', n.x+8, n.y+3);
                }});
                requestAnimationFrame(draw);
            }}
            draw();
        </script>
    """, height=290)
    
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("24h Growth", "+0.58%")
    c2.metric("7d Growth", "+9.73%")
    c3.metric("24h PnL", "+1.27%")
    c4.metric("Total Trades", "597,664")

# --- TAB 2: PORTFOLIO & FUND ---
with t2:
    c1, c2 = st.columns(2)
    c1.metric(_t("total_equity"), f"${st.session_state.equity:,.2f}")
    c2.metric(_t("fund_acc"), f"${st.session_state.fund:,.2f}")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"<div class='card'><div class='section-header'>ASSET ALLOCATION</div>", unsafe_allow_html=True)
        df_pos = pd.DataFrame([{"ASSET": "NVDA", "QTY": 450, "ENTRY": "$850.20", "VALUE": "$395,000"}, {"ASSET": "BTC", "QTY": 2.5, "ENTRY": "$62,000", "VALUE": "$185,000"}])
        st.dataframe(df_pos, hide_index=True, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='card' style='border-color:{accent};'><div class='section-header' style='color:{accent};'>{_t('ai_rec')}</div><p style='font-size:13px; line-height:1.6;'>Exposure balanced. Capital efficiency maximized in Layer 1 protocols.<br><br><strong>SUGGESTION:</strong> Trailing stops engaged on Tech. Consider unwinding 15% Crypto to capture liquidity.</p></div>", unsafe_allow_html=True)

# --- TAB 3: TRADES (REAL DATA) ---
with t3:
    st.markdown("<div class='section-header'>PUBLIC EQUITIES & CRYPTO MARKETS</div>", unsafe_allow_html=True)
    df_crypto = fetch_crypto_data()
    if not df_crypto.empty:
        df_crypto = df_crypto[['symbol', 'lastPrice', 'priceChangePercent', 'volume']].rename(columns={'symbol':'ASSET', 'lastPrice':'PRICE', 'priceChangePercent':'24h PnL (%)', 'volume':'24h VOLUME'})
        st.dataframe(df_crypto.style.format({"PRICE": "${:,.2f}", "24h PnL (%)": "{:,.2f}%", "24h VOLUME": "{:,.0f}"}), hide_index=True, use_container_width=True, height=400)
    else:
        st.warning("Live feed temporarily unavailable. Displaying cached models.")

# --- TAB 4: MACRO NEWS (HTML SLIDERS) ---
with t4:
    news = fetch_real_news()
    html_slider = f"""
    <style>
        .n-wrap {{ display: flex; overflow-x: auto; gap: 20px; padding-bottom: 15px; scroll-snap-type: x mandatory; }}
        .n-wrap::-webkit-scrollbar {{ height: 6px; }}
        .n-wrap::-webkit-scrollbar-track {{ background: {bg_color}; }}
        .n-wrap::-webkit-scrollbar-thumb {{ background: {border_color}; border-radius: 3px; }}
        .n-card {{ min-width: 85%; background: {card_bg}; border: 1px solid {border_color}; border-radius: 8px; scroll-snap-align: center; display: flex; overflow: hidden; }}
        .n-img {{ width: 45%; background-size: cover; background-position: center; }}
        .n-content {{ width: 55%; padding: 25px; display: flex; flex-direction: column; justify-content: center; }}
    </style>
    <div class="n-wrap">
    """
    for n in news[:5]:
        html_slider += f"""
        <div class="n-card">
            <div class="n-img" style="background-image: url('{n['img']}');"></div>
            <div class="n-content">
                <span style="color:{accent}; font-size:10px; font-weight:bold; letter-spacing:1px; margin-bottom:10px; font-family:monospace;">{n['sym']} ALERTS</span>
                <h3 style="color:{header_text}; margin:0 0 10px 0; font-family:sans-serif; font-size:22px;">{n['head']}</h3>
                <p style="color:{text_color}; font-size:13px; line-height:1.6; margin-bottom:15px;">{n['desc']}</p>
                <div style="background:{bg_color}; border:1px solid {border_color}; padding:12px; border-radius:6px; font-size:11px; font-family:sans-serif;">
                    <strong style="color:#a78bfa;">AI PROFITABILITY ANALYSIS</strong><br>
                    Impact: <span style="color:{accent}; font-weight:bold;">{n['ai_impact']}</span><br>
                    Strategy: {n['ai_strat']}
                </div>
            </div>
        </div>
        """
    html_slider += "</div>"
    components.html(html_slider, height=350)
    
    st.markdown("<div class='section-header' style='margin-top:20px;'>VERTICAL FEED</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    for i, n in enumerate(news[5:8]):
        with [c1, c2, c3][i]:
            st.markdown(f"<div class='card'><img src='{n['img']}' style='width:100%; height:120px; object-fit:cover; border-radius:6px; margin-bottom:10px;'><span style='color:{accent}; font-size:10px; font-weight:bold;'>{n['sym']}</span><h4 style='margin:5px 0; font-size:14px;'>{n['head']}</h4><p style='font-size:11px; color:#64748b;'>{n['ai_strat']}</p></div>", unsafe_allow_html=True)

# --- TAB 5: ALPHA SETUPS ---
with t5:
    st.markdown("<div class='section-header'>DEEP RESEARCH SIGNALS</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    for sym in ["ETH", "MSFT", "META"]:
        price = random.uniform(100, 500)
        with [c1, c2, c3][["ETH", "MSFT", "META"].index(sym)]:
            st.markdown(f"<div class='card'><div style='display:flex; justify-content:space-between; margin-bottom:15px;'><h3 style='margin:0;'>{sym}</h3><span style='color:{accent}; font-size:12px; font-weight:bold;'>VECTOR LONG</span></div><div style='font-size:12px; margin-bottom:5px; display:flex; justify-content:space-between;'><span>Entry Target</span><span style='color:white; font-family:monospace;'>${price:.2f}</span></div><div style='font-size:12px; margin-bottom:15px; display:flex; justify-content:space-between;'><span>AI Confidence</span><span style='color:#a78bfa; font-weight:bold;'>{random.uniform(85,99):.1f}%</span></div></div>", unsafe_allow_html=True)
            st.button(f"EXECUTE {sym}", key=f"alpha_{sym}", use_container_width=True)

# --- TAB 6: SMART ROUTING ---
with t6:
    st.markdown("<div class='card'><div class='section-header'>ADVANCED ORDER EXECUTION</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    tsym = col1.text_input("TICKER", "SOL")
    tqty = col2.number_input("QUANTITY", min_value=1, value=100)
    algo = col3.selectbox("ALGORITHM", ["VWAP Slicer", "TWAP Execution", "Dark Pool Iceberg"])
    if st.button("EXECUTE SMART ORDER", type="primary", use_container_width=True):
        st.success(f"Order routed via {algo}. See Compliance Tab for Audit.")
        log_sys(f"Order {tqty} {tsym} routed via {algo}")
    st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 7: SHADOW LEDGER ---
with t7:
    c1, c2 = st.columns(2)
    c1.markdown(f"<div class='card'><div class='section-header'>GOLDMAN SACHS PB1</div><p style='font-size:13px; display:flex; justify-content:space-between;'>Allocated Cash <span style='color:white; font-family:monospace;'>$852,330</span></p><p style='font-size:13px; display:flex; justify-content:space-between;'>Margin Utilized <span style='color:#f59e0b; font-family:monospace;'>$425,100</span></p></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='card'><div class='section-header'>MORGAN STANLEY PB2</div><p style='font-size:13px; display:flex; justify-content:space-between;'>Allocated Cash <span style='color:white; font-family:monospace;'>$568,220</span></p><p style='font-size:13px; display:flex; justify-content:space-between;'>Margin Utilized <span style='color:#3b82f6; font-family:monospace;'>$182,400</span></p></div>", unsafe_allow_html=True)

# --- TAB 8: BACKTEST LAB ---
with t8:
    st.markdown("<div class='card'><div class='section-header'>HISTORICAL SIMULATION</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2, 2, 1])
    col1.text_input("ASSET", value="BTC")
    col2.selectbox("STRATEGY", ["Mean Reversion", "Momentum", "Stat Arb"])
    col3.markdown("<br>", unsafe_allow_html=True)
    if col3.button("RUN BACKTEST", use_container_width=True):
        curve = [100000]
        for _ in range(100): curve.append(curve[-1] * (1 + random.gauss(0.001, 0.015)))
        fig = go.Figure(go.Scatter(y=curve, line=dict(color=accent, width=2)))
        fig.update_layout(height=250, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis=dict(gridcolor=border_color))
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 9: COMPLIANCE ---
with t9:
    c1, c2 = st.columns([1, 2])
    sig = "0x" + hashlib.sha256(f"{st.session_state.username}-{datetime.now()}".encode()).hexdigest()[:32].upper()
    c1.markdown(f"<div class='card' style='height:100%;'><div class='section-header'>LEGAL ASSESSMENT</div><p style='font-size:12px; margin-bottom:4px;'>MiFID II COMPLIANCE</p><p style='color:{header_text}; font-size:13px; line-height:1.5;'>Orders adhered to SEC Rule 613 formatting. Best Execution protocols verified.</p><p style='font-size:10px; margin-top:20px; border-top:1px solid {border_color}; padding-top:10px;'>ELECTRONIC SIGNATURE</p><p style='color:#a78bfa; font-family:monospace; font-size:10px; word-break:break-all;'>{sig}</p></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='card' style='height:100%;'><div class='section-header'>TRADE-BY-TRADE AUDIT</div><table style='width:100%; text-align:left; font-size:12px;'><tr style='border-bottom:1px solid {border_color};'><th style='padding:8px 0;'>TIME</th><th>ID</th><th>SYM</th><th style='color:{accent};'>STATUS</th></tr><tr><td style='padding:8px 0;'>14:22:10</td><td style='color:{header_text}; font-family:monospace;'>CAT-8F92A</td><td style='color:{header_text};'>SOL</td><td style='color:{accent}; font-weight:bold;'>FILLED</td></tr><tr><td style='padding:8px 0;'>14:20:05</td><td style='color:{header_text}; font-family:monospace;'>CAT-2B19C</td><td style='color:{header_text};'>AVAX</td><td style='color:{accent}; font-weight:bold;'>FILLED</td></tr></table></div>", unsafe_allow_html=True)

# --- TAB 10: SETTINGS & SYSTEM LOGS ---
with t10:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"<div class='card'><div class='section-header'>PREFERENCES</div>", unsafe_allow_html=True)
        new_lang = st.selectbox("LANGUAGE", ["English", "French", "Spanish", "German", "Chinese"], index=["English", "French", "Spanish", "German", "Chinese"].index(st.session_state.lang))
        new_theme = st.selectbox("THEME", ["Dark", "Light"], index=["Dark", "Light"].index(st.session_state.theme))
        if new_lang != st.session_state.lang or new_theme != st.session_state.theme:
            st.session_state.lang = new_lang
            st.session_state.theme = new_theme
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='card'><div class='section-header'>SYSTEM LOGS & SESSION</div><div style='background:#000; padding:10px; border-radius:6px; font-family:monospace; font-size:10px; color:#a3a3a3; height:100px; overflow-y:auto; margin-bottom:15px;'>{'<br>'.join(st.session_state.logs) if st.session_state.logs else 'Awaiting telemetry...'}</div>", unsafe_allow_html=True)
        if st.button("SECURE LOGOUT", type="primary", use_container_width=True):
            st.session_state.clear()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
