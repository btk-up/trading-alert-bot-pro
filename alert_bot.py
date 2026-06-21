# -*- coding: utf-8 -*-
"""
TRADING ALERT BOT PRO
Surveille 50 actions S&P 500 et envoie des alertes
quand une action devient STRONG BUY
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import yfinance as yf
import pandas as pd
import numpy as np
import smtplib
import json
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("   TRADING ALERT BOT PRO")
print("=" * 60)

# ============================================================
# CONFIGURATION — MODIFIE ICI
# ============================================================
CONFIG = {
    # Seuils d'alerte
    "STRONG_BUY_THRESHOLD" : 70,   # Score > 70 = STRONG BUY
    "BUY_THRESHOLD"        : 55,   # Score > 55 = BUY

    # Alertes techniques
    "RSI_OVERSOLD"         : 30,   # RSI < 30 = survente
    "RSI_OVERBOUGHT"       : 70,   # RSI > 70 = surachat
    "MOM_ALERT_PCT"        : 10,   # Hausse > 10% en 1 mois = alerte

    # Email (optionnel — laisse vide si pas d'email)
    "EMAIL_FROM"    : "",
    "EMAIL_TO"      : "zakaria0123121@gmail.com",
    "EMAIL_PASSWORD": "",
    "SMTP_SERVER"   : "smtp.gmail.com",
    "SMTP_PORT"     : 587,
}

# ============================================================
# UNIVERS D'ACTIONS
# ============================================================
WATCHLIST = {
    "TECH"       : ['AAPL','MSFT','GOOGL','NVDA','META','AMD','INTC','CSCO','ADBE','CRM'],
    "FINANCE"    : ['JPM','BAC','GS','MS','V','MA','AXP','WFC','C','BLK'],
    "HEALTHCARE" : ['JNJ','UNH','PFE','ABBV','MRK','TMO','ABT','BMY','AMGN','LLY'],
    "CONSUMER"   : ['AMZN','TSLA','HD','NKE','MCD','SBUX','TGT','WMT','COST','DIS'],
    "ENERGY"     : ['XOM','CVX','COP','SLB','EOG','PSX','VLO','MPC','OXY','HAL'],
}

ALL_TICKERS = [t for group in WATCHLIST.values() for t in group]
print(f"[*] Surveillance de {len(ALL_TICKERS)} actions")

# ============================================================
# DOWNLOAD PRIX
# ============================================================
print("[*] Telechargement des donnees...")
prices = yf.download(ALL_TICKERS, period="6mo", auto_adjust=True, progress=False)['Close']
prices = prices.dropna(thresh=int(len(prices)*0.7), axis=1)
valid  = prices.columns.tolist()
print(f"[OK] {len(valid)} actions disponibles")

# ============================================================
# CALCUL RSI
# ============================================================
def calc_rsi(series, period=14):
    delta = series.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

# ============================================================
# CALCUL SCORES + ALERTES
# ============================================================
print("[*] Analyse des signaux...")

last   = prices.iloc[-1]
alerts = []

for ticker in valid:
    try:
        serie = prices[ticker].dropna()
        if len(serie) < 63:
            continue

        # Momentum
        mom_1m  = (serie.iloc[-1] / serie.iloc[-21]  - 1) * 100 if len(serie) > 21  else 0
        mom_3m  = (serie.iloc[-1] / serie.iloc[-63]  - 1) * 100 if len(serie) > 63  else 0
        mom_6m  = (serie.iloc[-1] / serie.iloc[-126] - 1) * 100 if len(serie) > 126 else 0

        # RSI
        rsi = calc_rsi(serie).iloc[-1]

        # Volatilite
        vol = serie.pct_change().std() * np.sqrt(252) * 100

        # Distance depuis 52w high
        high_52w    = serie.rolling(252).max().iloc[-1] if len(serie) >= 252 else serie.max()
        pct_from_52 = (serie.iloc[-1] / high_52w - 1) * 100

        # Score simple base momentum + RSI
        mom_score = (mom_1m * 0.2 + mom_3m * 0.5 + mom_6m * 0.3)

        # Normalisation brute
        score = 50
        score += min(mom_score * 0.5, 20)
        score += max((50 - rsi) * 0.3, -15)
        score += min((pct_from_52 + 5) * 0.5, 10)
        score  = max(0, min(100, score))

        # Type d'alerte
        if score >= CONFIG["STRONG_BUY_THRESHOLD"]:
            signal = "STRONG BUY"
        elif score >= CONFIG["BUY_THRESHOLD"]:
            signal = "BUY"
        elif rsi < CONFIG["RSI_OVERSOLD"]:
            signal = "OVERSOLD"
        elif rsi > CONFIG["RSI_OVERBOUGHT"]:
            signal = "OVERBOUGHT"
        elif mom_1m > CONFIG["MOM_ALERT_PCT"]:
            signal = "MOMENTUM"
        else:
            signal = "WATCH"

        alerts.append({
            'ticker'      : ticker,
            'price'       : round(float(last.get(ticker, 0)), 2),
            'score'       : round(score, 1),
            'signal'      : signal,
            'rsi'         : round(rsi, 1),
            'mom_1m'      : round(mom_1m, 1),
            'mom_3m'      : round(mom_3m, 1),
            'mom_6m'      : round(mom_6m, 1),
            'volatility'  : round(vol, 1),
            'pct_52w_high': round(pct_from_52, 1),
        })

    except Exception as e:
        continue

df = pd.DataFrame(alerts).sort_values('score', ascending=False)

# ============================================================
# AFFICHAGE RESULTATS
# ============================================================
print("\n" + "=" * 70)
print("   ALERTES TRADING — RESULTATS")
print("=" * 70)

priority_signals = ["STRONG BUY", "BUY", "OVERSOLD", "MOMENTUM"]

for sig in priority_signals:
    subset = df[df['signal'] == sig]
    if len(subset) == 0:
        continue
    print(f"\n--- {sig} ({len(subset)} actions) ---")
    print(f"{'Ticker':<8} {'Score':>6} {'Prix':>8} {'RSI':>6} {'Mom1M':>8} {'Mom3M':>8}  Volatilite")
    print("-" * 65)
    for _, row in subset.head(10).iterrows():
        print(f"{row['ticker']:<8} {row['score']:>6.1f} ${row['price']:>7.2f} "
              f"{row['rsi']:>6.1f} {row['mom_1m']:>+7.1f}% {row['mom_3m']:>+7.1f}% "
              f"  {row['volatility']:.1f}%")

# ============================================================
# RESUME EXECUTIF
# ============================================================
strong_buys = df[df['signal'] == 'STRONG BUY']
buys        = df[df['signal'] == 'BUY']
oversolds   = df[df['signal'] == 'OVERSOLD']

print("\n" + "=" * 70)
print("   RESUME EXECUTIF")
print("=" * 70)
print(f"Date analyse  : {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print(f"Actions scannees : {len(df)}")
print(f"STRONG BUY    : {len(strong_buys)} actions")
print(f"BUY           : {len(buys)} actions")
print(f"OVERSOLD      : {len(oversolds)} actions (potentiel rebond)")
print(f"\nTOP 3 PRIORITAIRES :")
for i, (_, row) in enumerate(df.head(3).iterrows(), 1):
    print(f"  {i}. {row['ticker']} | Score {row['score']} | {row['signal']} | RSI {row['rsi']}")

# ============================================================
# GRAPHIQUES
# ============================================================
print("\n[*] Generation dashboard...")

color_map = {
    'STRONG BUY' : '#00ff88',
    'BUY'        : '#00aaff',
    'OVERSOLD'   : '#ffaa00',
    'MOMENTUM'   : '#aa00ff',
    'OVERBOUGHT' : '#ff4444',
    'WATCH'      : '#888888',
}

df['color'] = df['signal'].map(color_map).fillna('#888888')

top30 = df.head(30)

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        'Top 30 Actions par Score',
        'RSI vs Momentum 3M',
        'Distribution des Signaux',
        'Score vs Volatilite'
    ),
    specs=[
        [{"type": "bar"},     {"type": "scatter"}],
        [{"type": "pie"},     {"type": "scatter"}]
    ],
    vertical_spacing=0.15,
    horizontal_spacing=0.1
)

# Bar chart
fig.add_trace(go.Bar(
    x=top30['score'],
    y=[f"{r['ticker']} [{r['signal']}]" for _, r in top30.iterrows()],
    orientation='h',
    marker_color=top30['color'].tolist(),
    text=[f"{s:.0f}" for s in top30['score']],
    textposition='outside',
    hovertemplate='<b>%{y}</b><br>Score: %{x:.1f}<extra></extra>'
), row=1, col=1)

# Scatter RSI vs Momentum
fig.add_trace(go.Scatter(
    x=df['rsi'],
    y=df['mom_3m'],
    mode='markers+text',
    text=df['ticker'],
    textposition='top center',
    textfont=dict(size=7, color='white'),
    marker=dict(
        size=df['score']/5,
        color=df['score'],
        colorscale='RdYlGn',
        showscale=True,
        line=dict(width=1, color='white')
    ),
    hovertemplate='<b>%{text}</b><br>RSI: %{x:.1f}<br>Mom3M: %{y:.1f}%<extra></extra>'
), row=1, col=2)

# RSI zones
fig.add_vline(x=30, line_dash="dash", line_color="#ffaa00", row=1, col=2)
fig.add_vline(x=70, line_dash="dash", line_color="#ff4444", row=1, col=2)

# Pie signaux
sig_counts = df[df['signal'].isin(priority_signals + ['OVERBOUGHT','WATCH'])]['signal'].value_counts()
fig.add_trace(go.Pie(
    labels=sig_counts.index,
    values=sig_counts.values,
    hole=0.4,
    marker_colors=[color_map.get(s, '#888') for s in sig_counts.index],
    textinfo='label+percent',
    textfont=dict(size=10)
), row=2, col=1)

# Scatter Score vs Vol
fig.add_trace(go.Scatter(
    x=df['volatility'],
    y=df['score'],
    mode='markers+text',
    text=df['ticker'],
    textposition='top center',
    textfont=dict(size=7, color='white'),
    marker=dict(
        size=10,
        color=df['score'],
        colorscale='RdYlGn',
        showscale=True,
        line=dict(width=1, color='white')
    ),
    hovertemplate='<b>%{text}</b><br>Vol: %{x:.1f}%<br>Score: %{y:.1f}<extra></extra>'
), row=2, col=2)

fig.update_layout(
    title=dict(
        text=f'TRADING ALERT BOT PRO — {datetime.now().strftime("%Y-%m-%d %H:%M")}',
        font=dict(size=18, color='white'),
        x=0.5
    ),
    height=900,
    showlegend=False,
    paper_bgcolor='#0d1117',
    plot_bgcolor='#161b22',
    font=dict(color='white')
)
fig.update_xaxes(gridcolor='#30363d', zerolinecolor='#555')
fig.update_yaxes(gridcolor='#30363d', zerolinecolor='#555')

# ============================================================
# SAUVEGARDE
# ============================================================
output_dir = r"C:\Users\zakar\AlertBot"
os.makedirs(output_dir, exist_ok=True)

html_path  = os.path.join(output_dir, "alert_dashboard.html")
excel_path = os.path.join(output_dir, "Trading_Alerts.xlsx")

fig.write_html(html_path, auto_open=True)
print(f"[OK] Dashboard ouvert dans le navigateur !")

df.round(1).to_excel(excel_path, index=False)
print(f"[OK] Excel sauvegarde : {excel_path}")

print("\n" + "=" * 60)
print("[OK] ALERT BOT TERMINE !")
print(f"[*] {len(strong_buys)} STRONG BUY detectes")
print(f"[*] {len(buys)} BUY detectes")
print(f"[*] {len(oversolds)} OVERSOLD detectes")
print("=" * 60)
