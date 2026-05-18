from pathlib import Path

# ── Logging ────────────────────────────────────────────────────────────
# Controls verbosity of the application log (file + console).
# "INFO"    — normal use: exchange init, market counts, errors only (recommended)
# "DEBUG"   — full HTTP request/response dump from ccxt (use only for troubleshooting)
# "WARNING" — errors and warnings only
LOG_LEVEL = "INFO"

# ── Markets cache ──────────────────────────────────────────────────────
MARKETS_CACHE_DIR = Path("markets_cache")
MARKETS_CACHE_DIR.mkdir(exist_ok=True)
CACHE_TTL_HOURS = 24

# ── Exchange OHLCV limits ──────────────────────────────────────────────
EXCHANGE_LIMITS: dict[str, int] = {
    'binance': 1000, 'bybit': 1000, 'okx': 300,
    'gateio': 1000, 'whitebit': 1000, 'kucoinfutures': 200,
    'mexc': 1000, 'bitget': 1000, 'bingx': 1000,
    'hyperliquid': 500, 'paradex': 100, 'htx': 2000,
    'kraken': 720, 'kucoin': 1500, 'deribit': 1000,
    'bitmex': 750, 'phemex': 1000, 'coinbase': 300,
    'bitmart': 200, 'xt': 1000, 'coinex': 1000,
    'aster': 1500,  # AsterDEX (ccxt id: aster) — max 1500 per docs
}
DEFAULT_LIMIT = 500

# ── Timeframe → milliseconds ───────────────────────────────────────────
TF_MS: dict[str, int] = {
    '1m': 60_000, '3m': 180_000, '5m': 300_000,
    '15m': 900_000, '30m': 1_800_000,
    '1h': 3_600_000, '2h': 7_200_000, '4h': 14_400_000,
    '6h': 21_600_000, '12h': 43_200_000,
    '1d': 86_400_000, '1w': 604_800_000,
}