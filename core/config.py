from pathlib import Path

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
