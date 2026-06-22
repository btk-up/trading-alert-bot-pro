# Trading Alert Bot Pro

> Automated stock scanner — 500 S&P 500 stocks | Real-time signals | Interactive dashboard

---

## Live Results (Latest Run)

| Signal | Ticker | Score | Price | RSI | Mom 3M | Sector |
|--------|--------|-------|-------|-----|--------|--------|
| STRONG BUY | AMD | 70.7 | $537 | 53.1 | +166.9% | Technology |
| BUY | QCOM | 69.9 | — | — | — | Technology |
| BUY | MU | 69.7 | — | — | — | Technology |
| BUY | INTC | 69.2 | $133 | 61.0 | +205.4% | Technology |
| OVERSOLD | MSFT | 49.9 | $379 | 18.6 | -0.4% | Technology |

*Run daily before market open for fresh signals.*

---

## What It Does

- Scans **500+ S&P 500 stocks** across **11 GICS sectors** (live from Wikipedia)
- Calculates **Momentum** (1M / 3M / 6M), **RSI**, **Volatility**, **52-week position**
- Generates **6 signal types** with a composite score (0–100)
- Opens an **interactive Plotly dashboard** automatically in your browser
- Exports all signals to **Excel** in one click
- Shows **sector heatmap** — which sectors are strongest right now
- Built-in **strategy table** — rules explained visually

---

## Signal Logic

| Signal | Condition | Meaning | Action |
|--------|-----------|---------|--------|
| STRONG BUY | Score > 70 | Strong momentum + healthy RSI | Entry candidate |
| BUY | Score 55–70 | Good multi-timeframe momentum | Progressive entry |
| OVERSOLD | RSI < 30 | Technical oversell, bounce possible | Wait for confirmation |
| MOMENTUM | Mom 1M > 10% | Short-term acceleration | Ride the trend |
| OVERBOUGHT | RSI > 70 | Overextended, pullback risk | Wait / take profit |
| WATCH | Other | No strong signal detected | Monitor only |

---

## Dashboard (6 Charts)

| Chart | What It Shows |
|-------|--------------|
| Top 30 by Score | Best current opportunities |
| Sector Heatmap | Strongest GICS sectors right now |
| RSI vs Momentum | Market positioning map (top 150 stocks) |
| Signal Distribution | How many STRONG BUY / BUY / OVERSOLD etc |
| Score vs Volatility | Risk/reward scatter |
| Strategy Table | Signal rules explained |

---

## Installation

```bash
# 1. Clone
git clone https://github.com/btk-up/trading-alert-bot-pro.git
cd trading-alert-bot-pro

# 2. Install dependencies (Windows: double-click install.bat)
pip install -r requirements.txt

# 3. Run (Windows: double-click run.bat)
python alert_bot.py
```

Dashboard opens automatically in browser. Excel saved in the same folder.

---

## Tech Stack

```
Python 3.x  |  yfinance  |  pandas  |  numpy  |  plotly  |  openpyxl  |  requests
```

---

## How to Use for Trading

1. Run every morning before market open
2. Focus on **STRONG BUY** first, then **BUY**
3. Check **OVERSOLD** for bounce setups
4. Use the **Sector Heatmap** to confirm sector strength
5. Cross-reference with your own analysis before entering

---

## Need a Custom Version?

I build custom trading bots, EAs (MetaTrader 5), NinjaTrader strategies, and Python scanners.

**Fiverr:** [fiverr.com/btk_up](https://fiverr.com/btk_up)

---

*Part of a Quantitative Finance Python Portfolio — built by a Forex & Gold trader.*
