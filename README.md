# Trading Alert Bot Pro

Automated trading alert system that scans 50 S&P 500 stocks across 5 sectors and generates real-time STRONG BUY / BUY / OVERSOLD signals.

## Today's Alerts (Live Results)

| Signal | Ticker | Score | Price | RSI | Mom 3M |
|--------|--------|-------|-------|-----|--------|
| STRONG BUY | AMD | 70.7 | $537 | 53.1 | +166.9% |
| BUY | INTC | 69.2 | $133 | 61.0 | +205.4% |
| BUY | CSCO | 63.0 | $119 | 48.9 | +54.8% |
| OVERSOLD | MSFT | 49.9 | $379 | 18.6 | -0.4% |

## What It Does

- Scans 50 stocks across 5 sectors (Tech, Finance, Healthcare, Consumer, Energy)
- Calculates momentum (1M, 3M, 6M), RSI, volatility, 52-week position
- Generates 5 signal types: STRONG BUY / BUY / OVERSOLD / MOMENTUM / WATCH
- Produces an interactive Plotly dashboard (4 charts)
- Exports all signals to Excel automatically

## Signal Types

| Signal | Condition | Action |
|--------|-----------|--------|
| STRONG BUY | Score > 70 | Strong entry candidate |
| BUY | Score > 55 | Good entry candidate |
| OVERSOLD | RSI < 30 | Potential bounce play |
| MOMENTUM | 1M gain > 10% | Trend continuation |
| OVERBOUGHT | RSI > 70 | Take profit / avoid |

## Sectors Monitored

- Technology (AAPL, MSFT, GOOGL, NVDA, META...)
- Financial Services (JPM, BAC, GS, MS...)
- Healthcare (JNJ, UNH, PFE, ABBV...)
- Consumer (AMZN, TSLA, HD, NKE...)
- Energy (XOM, CVX, COP...)

## Tech Stack

```
Python 3.x | yfinance | pandas | numpy | plotly | openpyxl
```

## How to Run

```bash
pip install yfinance plotly openpyxl pandas numpy
python alert_bot.py
```

Dashboard opens automatically in browser + Excel exported locally.

## How to Use for Trading

1. Run the bot every morning before market open
2. Check STRONG BUY and BUY signals
3. Cross-reference with your own analysis
4. Use OVERSOLD signals for potential bounce plays

## How Hedge Funds Use Similar Systems

Firms like **Citadel**, **Point72**, and **Two Sigma** run systematic screening across thousands of stocks every millisecond. This project replicates the core signal generation logic at retail scale.

---

*Part of a Quantitative Finance Python Portfolio*
