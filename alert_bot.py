# -*- coding: utf-8 -*-
"""
TRADING ALERT BOT PRO — S&P 500 EDITION
Surveille jusqu'a 500 actions et genere des signaux avec strategie
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import yfinance as yf
import pandas as pd
import numpy as np
import os
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("   TRADING ALERT BOT PRO — S&P 500 EDITION")
print("=" * 60)

CONFIG = {
    "STRONG_BUY_THRESHOLD" : 70,
    "BUY_THRESHOLD"        : 55,
    "RSI_OVERSOLD"         : 30,
    "RSI_OVERBOUGHT"       : 70,
    "MOM_ALERT_PCT"        : 10,
}

# ============================================================
# LISTE S&P 500 — Wikipedia avec fallback
# ============================================================
print("[*] Chargement de la liste S&P 500...")
try:
    import requests
    r = requests.get(
        'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies',
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
        timeout=15
    )
    sp500 = pd.read_html(io.StringIO(r.text))[0]
    sp500['Symbol'] = sp500['Symbol'].str.replace('.', '-', regex=False)
    WATCHLIST = {}
    for sector, group in sp500.groupby('GICS Sector'):
        WATCHLIST[sector] = group['Symbol'].tolist()
    ALL_TICKERS = [t for tickers in WATCHLIST.values() for t in tickers]
    print(f"[OK] {len(ALL_TICKERS)} actions chargees ({len(WATCHLIST)} secteurs GICS)")
    for s, tickers in WATCHLIST.items():
        print(f"     {s[:35]:<35} {len(tickers)} actions")
except Exception as e:
    print(f"[WARN] Wikipedia indisponible, liste de secours... ({e})")
    WATCHLIST = {
        "Information Technology" : ['AAPL','MSFT','NVDA','AMD','INTC','CSCO','ADBE','CRM','ORCL','IBM',
                                     'QCOM','TXN','AVGO','MU','HPQ','AMAT','LRCX','KLAC','MCHP','ADI'],
        "Financials"             : ['JPM','BAC','GS','MS','V','MA','AXP','WFC','C','BLK',
                                     'SCHW','USB','PNC','COF','TFC','SPGI','MCO','CME','ICE','TRV'],
        "Health Care"            : ['JNJ','UNH','PFE','ABBV','MRK','TMO','ABT','BMY','AMGN','LLY',
                                     'GILD','CVS','CI','HUM','MCK','ISRG','REGN','VRTX','ZTS','BDX'],
        "Consumer Discretionary" : ['AMZN','TSLA','HD','NKE','MCD','SBUX','TGT','WMT','COST','DIS',
                                     'NFLX','LOW','TJX','BKNG','MAR','YUM','CMG','ROST','DHI','LEN'],
        "Energy"                 : ['XOM','CVX','COP','SLB','EOG','PSX','VLO','MPC','OXY','HAL',
                                     'DVN','HES','BKR','FANG','MRO','APA','PXD','CVI','VET','RRC'],
        "Industrials"            : ['BA','CAT','GE','HON','LMT','RTX','UPS','FDX','MMM','DE',
                                     'EMR','ITW','ETN','PH','ROK','NOC','GD','TDG','IR','XYL'],
        "Communication Services" : ['GOOGL','META','NFLX','T','VZ','TMUS','CMCSA','DIS','EA','ATVI',
                                     'TTWO','MTCH','ZG','IAC','FOXA','PARA','WBD','LYV','MSGS','NYT'],
        "Consumer Staples"       : ['PG','KO','PEP','PM','MO','MDLZ','CL','GIS','K','CAG',
                                     'HRL','SJM','CHD','CLX','EL','KMB','HSY','MKC','CPB','FLO'],
        "Materials"              : ['LIN','APD','SHW','ECL','PPG','NEM','FCX','NUE','VMC','MLM',
                                     'CF','MOS','ALB','FMC','IFF','PKG','IP','WRK','SEE','SON'],
        "Utilities"              : ['NEE','DUK','SO','D','AEP','XEL','EXC','SRE','WEC','ES',
                                     'AWK','ETR','PPL','CMS','NI','LNT','EVRG','AEE','CNP','PNW'],
        "Real Estate"            : ['AMT','PLD','CCI','EQIX','PSA','SPG','O','EQR','AVB','VTR',
                                     'WELL','ARE','BXP','KIM','REG','FRT','HST','SLG','AIV','CPT'],
    }
    ALL_TICKERS = [t for tickers in WATCHLIST.values() for t in tickers]
    print(f"[OK] {len(ALL_TICKERS)} actions (liste de secours)")

ticker_sector = {t: s for s, tickers in WATCHLIST.items() for t in tickers}

# ============================================================
# TELECHARGEMENT
# ============================================================
print(f"\n[*] Telechargement des donnees ({len(ALL_TICKERS)} tickers)...")
prices = yf.download(ALL_TICKERS, period="6mo", auto_adjust=True, progress=True)['Close']
prices = prices.dropna(thresh=int(len(prices) * 0.7), axis=1)
valid = prices.columns.tolist()
print(f"[OK] {len(valid)} actions disponibles apres filtrage")

# ============================================================
# RSI
# ============================================================
def calc_rsi(series, period=14):
    delta = series.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

# ============================================================
# ANALYSE
# ============================================================
print("[*] Calcul des signaux...")
last   = prices.iloc[-1]
alerts = []

for ticker in valid:
    try:
        serie = prices[ticker].dropna()
        if len(serie) < 63:
            continue

        mom_1m  = (serie.iloc[-1] / serie.iloc[-21]  - 1) * 100 if len(serie) > 21  else 0
        mom_3m  = (serie.iloc[-1] / serie.iloc[-63]  - 1) * 100 if len(serie) > 63  else 0
        mom_6m  = (serie.iloc[-1] / serie.iloc[-126] - 1) * 100 if len(serie) > 126 else 0
        rsi     = calc_rsi(serie).iloc[-1]
        vol     = serie.pct_change().std() * np.sqrt(252) * 100
        high_52 = serie.rolling(252).max().iloc[-1] if len(serie) >= 252 else serie.max()
        pct_52  = (serie.iloc[-1] / high_52 - 1) * 100

        mom_score = mom_1m * 0.2 + mom_3m * 0.5 + mom_6m * 0.3
        score  = 50
        score += min(mom_score * 0.5, 20)
        score += max((50 - rsi) * 0.3, -15)
        score += min((pct_52 + 5) * 0.5, 10)
        score  = max(0, min(100, score))

        if   score >= CONFIG["STRONG_BUY_THRESHOLD"]: signal = "STRONG BUY"
        elif score >= CONFIG["BUY_THRESHOLD"]:        signal = "BUY"
        elif rsi < CONFIG["RSI_OVERSOLD"]:            signal = "OVERSOLD"
        elif rsi > CONFIG["RSI_OVERBOUGHT"]:          signal = "OVERBOUGHT"
        elif mom_1m > CONFIG["MOM_ALERT_PCT"]:        signal = "MOMENTUM"
        else:                                          signal = "WATCH"

        alerts.append({
            'ticker'      : ticker,
            'sector'      : ticker_sector.get(ticker, 'Other'),
            'price'       : round(float(last.get(ticker, 0)), 2),
            'score'       : round(score, 1),
            'signal'      : signal,
            'rsi'         : round(rsi, 1),
            'mom_1m'      : round(mom_1m, 1),
            'mom_3m'      : round(mom_3m, 1),
            'mom_6m'      : round(mom_6m, 1),
            'volatility'  : round(vol, 1),
            'pct_52w_high': round(pct_52, 1),
        })
    except Exception:
        continue

df = pd.DataFrame(alerts).sort_values('score', ascending=False)

# ============================================================
# AFFICHAGE CONSOLE
# ============================================================
color_map = {
    'STRONG BUY' : '#00ff88',
    'BUY'        : '#00aaff',
    'OVERSOLD'   : '#ffaa00',
    'MOMENTUM'   : '#aa00ff',
    'OVERBOUGHT' : '#ff4444',
    'WATCH'      : '#888888',
}

strong_buys = df[df['signal'] == 'STRONG BUY']
buys        = df[df['signal'] == 'BUY']
oversolds   = df[df['signal'] == 'OVERSOLD']

print("\n" + "=" * 70)
print("   TOP 10 — STRONG BUY")
print("=" * 70)
print(f"{'Ticker':<8} {'Secteur':<25} {'Score':>6} {'Prix':>9} {'RSI':>6} {'Mom1M':>8} {'Mom3M':>8}")
print("-" * 75)
for _, row in strong_buys.head(10).iterrows():
    print(f"{row['ticker']:<8} {row['sector'][:24]:<25} {row['score']:>6.1f} "
          f"${row['price']:>8.2f} {row['rsi']:>6.1f} {row['mom_1m']:>+7.1f}% {row['mom_3m']:>+7.1f}%")

print("\n" + "=" * 70)
print("   RESUME EXECUTIF")
print("=" * 70)
print(f"Date          : {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print(f"Actions scannees : {len(df)}")
print(f"STRONG BUY    : {len(strong_buys)}")
print(f"BUY           : {len(buys)}")
print(f"OVERSOLD      : {len(oversolds)}")
print(f"\nTOP 5 PRIORITAIRES :")
for i, (_, row) in enumerate(df.head(5).iterrows(), 1):
    print(f"  {i}. {row['ticker']:<6} | {row['signal']:<11} | Score {row['score']:.1f} | {row['sector'][:25]}")

# ============================================================
# DASHBOARD
# ============================================================
print("\n[*] Generation dashboard...")

df['color'] = df['signal'].map(color_map).fillna('#888888')
top30 = df.head(30)

# Secteur stats
sector_stats = df.groupby('sector').agg(
    avg_score=('score', 'mean'),
    strong_buys=('signal', lambda x: (x == 'STRONG BUY').sum()),
    buys=('signal', lambda x: (x == 'BUY').sum()),
    count=('ticker', 'count')
).reset_index().sort_values('avg_score', ascending=False)

sector_colors = [
    f"rgb({max(0,int(255*(1-s/100)))}, {int(200*s/100)}, {max(0,int(100*(1-s/100)))})"
    for s in sector_stats['avg_score']
]

fig = make_subplots(
    rows=3, cols=2,
    subplot_titles=(
        f'Top 30 Actions par Score (sur {len(df)} scannees)',
        'Score Moyen par Secteur GICS',
        'RSI vs Momentum 3M (Top 150)',
        'Distribution des Signaux',
        'Score vs Volatilite',
        'Strategie — Regles de Signal'
    ),
    specs=[
        [{"type": "bar"},     {"type": "bar"}],
        [{"type": "scatter"}, {"type": "pie"}],
        [{"type": "scatter"}, {"type": "table"}],
    ],
    vertical_spacing=0.10,
    horizontal_spacing=0.08
)

# [1,1] Top 30 bar
fig.add_trace(go.Bar(
    x=top30['score'],
    y=[f"{r['ticker']} [{r['signal']}]" for _, r in top30.iterrows()],
    orientation='h',
    marker_color=top30['color'].tolist(),
    text=[f"{s:.0f}" for s in top30['score']],
    textposition='outside',
    hovertemplate='<b>%{y}</b><br>Score: %{x:.1f}<extra></extra>'
), row=1, col=1)

# [1,2] Secteur heatmap
fig.add_trace(go.Bar(
    x=sector_stats['avg_score'],
    y=sector_stats['sector'],
    orientation='h',
    marker_color=sector_colors,
    text=[f"{s:.1f} | {sb} SB | {b} BUY"
          for s, sb, b in zip(sector_stats['avg_score'],
                               sector_stats['strong_buys'],
                               sector_stats['buys'])],
    textposition='outside',
    hovertemplate='<b>%{y}</b><br>Score moyen: %{x:.1f}<extra></extra>'
), row=1, col=2)

# [2,1] Scatter RSI vs Momentum (top 150)
top150 = df.head(150)
fig.add_trace(go.Scatter(
    x=top150['rsi'],
    y=top150['mom_3m'],
    mode='markers+text',
    text=top150['ticker'],
    textposition='top center',
    textfont=dict(size=6, color='white'),
    marker=dict(
        size=top150['score'] / 6,
        color=top150['score'],
        colorscale='RdYlGn',
        showscale=True,
        colorbar=dict(x=0.45, thickness=10),
        line=dict(width=0.5, color='white')
    ),
    hovertemplate='<b>%{text}</b><br>RSI: %{x:.1f}<br>Mom3M: %{y:.1f}%<extra></extra>'
), row=2, col=1)
fig.add_vline(x=30, line_dash="dash", line_color="#ffaa00", row=2, col=1)
fig.add_vline(x=70, line_dash="dash", line_color="#ff4444", row=2, col=1)
fig.add_hline(y=0,  line_dash="dash", line_color="#555555", row=2, col=1)

# [2,2] Pie signaux
sig_counts = df['signal'].value_counts()
fig.add_trace(go.Pie(
    labels=sig_counts.index,
    values=sig_counts.values,
    hole=0.4,
    marker_colors=[color_map.get(s, '#888') for s in sig_counts.index],
    textinfo='label+percent+value',
    textfont=dict(size=9)
), row=2, col=2)

# [3,1] Score vs Vol
fig.add_trace(go.Scatter(
    x=df['volatility'],
    y=df['score'],
    mode='markers',
    marker=dict(
        size=7,
        color=df['score'],
        colorscale='RdYlGn',
        showscale=False,
        opacity=0.7,
        line=dict(width=0.3, color='white')
    ),
    text=df['ticker'],
    hovertemplate='<b>%{text}</b><br>Vol: %{x:.1f}%<br>Score: %{y:.1f}<extra></extra>'
), row=3, col=1)

# [3,2] Strategie table
strat_headers = ['Signal', 'Condition', 'Interpretation', 'Action']
strat_rows = [
    ['STRONG BUY', 'Score > 70', 'Momentum fort + RSI sain + proche ATH', 'Entree immediate'],
    ['BUY',        'Score 55-70', 'Bon momentum multi-timeframe', 'Entree progressive'],
    ['OVERSOLD',   'RSI < 30', 'Survente technique, rebond possible', 'Surveiller confirmation'],
    ['MOMENTUM',   'Mom1M > 10%', 'Acceleration court terme', 'Ride the trend'],
    ['OVERBOUGHT', 'RSI > 70', 'Surachat, risque de correction', 'Attendre pullback'],
    ['WATCH',      'Autres', 'Pas de signal fort detecte', 'Observation'],
]
cell_colors = [
    ['#161b22'] * 6,
    ['#161b22'] * 6,
    [color_map.get(r[0], '#333') for r in strat_rows],
    ['#161b22'] * 6,
    ['#161b22'] * 6,
]
fig.add_trace(go.Table(
    header=dict(
        values=[f'<b>{h}</b>' for h in strat_headers],
        fill_color='#21262d',
        font=dict(color='white', size=11),
        align='left',
        height=28
    ),
    cells=dict(
        values=[[r[i] for r in strat_rows] for i in range(4)],
        fill_color=[
            ['#161b22'] * 6,
            ['#161b22'] * 6,
            [color_map.get(r[0], '#333333') for r in strat_rows],
            ['#161b22'] * 6,
        ],
        font=dict(color='white', size=10),
        align='left',
        height=25
    )
), row=3, col=2)

fig.update_layout(
    title=dict(
        text=f'TRADING ALERT BOT PRO — S&P 500 | {datetime.now().strftime("%Y-%m-%d %H:%M")} | {len(df)} actions analysees',
        font=dict(size=16, color='white'),
        x=0.5
    ),
    height=1400,
    showlegend=False,
    paper_bgcolor='#0d1117',
    plot_bgcolor='#161b22',
    font=dict(color='white', family='monospace')
)
fig.update_xaxes(gridcolor='#30363d', zerolinecolor='#555', color='#aaa')
fig.update_yaxes(gridcolor='#30363d', zerolinecolor='#555', color='#aaa')

# ============================================================
# SAUVEGARDE
# ============================================================
output_dir = os.path.dirname(os.path.abspath(__file__))

html_path  = os.path.join(output_dir, "alert_dashboard.html")
excel_path = os.path.join(output_dir, "Trading_Alerts.xlsx")

fig.write_html(html_path, auto_open=True)
print(f"[OK] Dashboard ouvert dans le navigateur !")

df.round(1).to_excel(excel_path, index=False)
print(f"[OK] Excel sauvegarde : {excel_path}")

print("\n" + "=" * 60)
print("[OK] ALERT BOT S&P 500 TERMINE !")
print(f"[*] {len(strong_buys)} STRONG BUY detectes")
print(f"[*] {len(buys)} BUY detectes")
print(f"[*] {len(oversolds)} OVERSOLD detectes")
print(f"[*] Secteur le plus fort : {sector_stats.iloc[0]['sector']}")
print("=" * 60)
