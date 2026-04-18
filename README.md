# Ratio Arbitrage Chart

A desktop application for real-time cross-exchange ratio (spread) charting. Select any two instruments from any two supported exchanges, and the app renders a live candlestick chart of their price ratio — letting you visually identify arbitrage opportunities and mean-reversion setups across perpetual swaps, futures, and spot markets.

---

## Features

- **Cross-exchange ratio chart** — displays `price(A) / price(B)` as OHLCV candlesticks in real time
- **18 supported exchanges** — Binance, Bybit, OKX, Gate.io, WhiteBIT, KuCoin Futures, MEXC, Bitget, BingX, Hyperliquid, Paradex, HTX, Kraken, KuCoin, Deribit, BitMEX, Phemex, Coinbase
- **All market types** — perpetual swaps, futures, spot, options
- **Infinite scroll** — lazy-loads historical candles as you scroll left
- **Auto-refresh** — live candle updates every 1.5 seconds
- **Markets cache** — exchange market lists are cached locally for 24 hours to reduce API calls
- **Adaptive price scale** — automatic decimal precision based on the visible price range
- **Parity line** — horizontal reference at ratio = 1.0
- **Ukrainian keyboard layout fix** — Cyrillic input is auto-converted when searching symbols

---

## Project Structure

```
ratio_arbitrage_chart/
├── main.py                  # Entry point — creates the pywebview window
├── requirements.txt         # Python dependencies
├── README.md
│
├── core/
│   ├── __init__.py
│   ├── api.py               # pywebview JS bridge (public API methods)
│   ├── config.py            # Constants: cache TTL, exchange limits, TF map
│   ├── exchange_manager.py  # Async exchange instances, market fetching, OHLCV ratio
│   └── cache.py             # Markets cache read/write helpers
│
└── ui/
    ├── __init__.py
    └── template.py          # Self-contained HTML/CSS/JS frontend (LightweightCharts)
```

---

## Requirements

- Python 3.11+
- See `requirements.txt`

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Running

```bash
python main.py
```

---

## Usage

1. **BUY side** — select an exchange and search for a symbol (e.g. `BTC/USDT:USDT`)
2. **SELL side** — select a second exchange and symbol
3. Choose a timeframe and press **▶ GO**
4. The chart shows `BUY price / SELL price` over time
5. Scroll left to load historical data; the chart updates live every ~1.5 s

---

## Architecture Notes

| Layer | Responsibility |
|---|---|
| `main.py` | Bootstraps the pywebview window |
| `core/api.py` | Thin synchronous wrapper around async logic; called by JS via `pywebview.api.*` |
| `core/exchange_manager.py` | Owns all `ccxt` exchange instances; fetches markets and OHLCV; computes ratio DataFrame |
| `core/cache.py` | JSON file cache for exchange market lists (TTL: 24 h) |
| `core/config.py` | Centralised constants — no magic numbers elsewhere |
| `ui/template.py` | Complete single-file frontend: HTML + CSS (CSS variables theme) + vanilla JS (LightweightCharts v3) |

The Python backend runs a persistent `asyncio` event loop in a daemon thread. All `ccxt` calls are dispatched into that loop via `asyncio.run_coroutine_threadsafe`, keeping the pywebview main thread non-blocking.

---

## Exchange-specific Notes

- **Binance** — forced to `linear` futures (`fapi.binance.com`) to avoid the `dapi` (coin-margined) endpoint
- **HTX** — forced to `linear` swaps to avoid `hbdm`
- **Paradex** — uses `price: mark` parameter for OHLCV requests
- **KuCoin Futures** — separate `kucoinfutures` ccxt class (not `kucoin`)

---

## License

Private / internal use.
