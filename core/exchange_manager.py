import asyncio
import ccxt.async_support as ccxt
import pandas as pd
from core.config import EXCHANGE_LIMITS, DEFAULT_LIMIT, TF_MS
from core.cache import load_cache, save_cache


class ExchangeManager:
    """Manages async exchange instances and market/OHLCV fetching."""

    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.exchanges: dict = {}
        self.loop = loop

    # ── Exchange factory ───────────────────────────────────────────────
    async def _get_exchange(self, exchange_id: str):
        if exchange_id not in self.exchanges:
            print(f"⚙️  Ініціалізація {exchange_id}…")
            exch_class = getattr(ccxt, exchange_id)
            options = {'enableRateLimit': True}
            if exchange_id == 'binance':
                options['options'] = {
                    'defaultType': 'future',
                    'fetchMarkets': ['linear'],
                }
            elif exchange_id == 'htx':
                options['options'] = {
                    'defaultType': 'swap',
                    'fetchMarkets': ['linear'],
                }
            elif exchange_id == 'bitmart':
                options['options'] = {'defaultType': 'swap'}

            elif exchange_id == 'coinex':
                options['options'] = {'defaultType': 'swap'}

            elif exchange_id == 'xt':
                options['options'] = {'defaultType': 'swap'}
            self.exchanges[exchange_id] = exch_class(options)
        return self.exchanges[exchange_id]

    async def close_all(self):
        for ex in self.exchanges.values():
            await ex.close()

    # ── Markets ────────────────────────────────────────────────────────
    async def _fetch_markets_from_exchange(self, exchange_id: str) -> list:
        e = await self._get_exchange(exchange_id)
        raw = await e.load_markets(reload=True)
        result = []
        for sym, m in raw.items():
            if m.get('swap') or m.get('linear') or m.get('inverse'):
                mtype = 'swap'
            elif m.get('option'):
                mtype = 'option'
            elif m.get('future') and not m.get('spot'):
                mtype = 'future'
            else:
                raw_type = m.get('type', 'spot')
                if raw_type in ('swap', 'linear', 'inverse'):
                    mtype = 'swap'
                elif raw_type == 'future':
                    mtype = 'future'
                elif raw_type == 'option':
                    mtype = 'option'
                else:
                    mtype = 'spot'
            result.append({
                'symbol': sym,
                'type': mtype,
                'base': m.get('base', ''),
                'quote': m.get('quote', ''),
            })
        order = {'swap': 0, 'future': 1, 'spot': 2, 'option': 3}
        result.sort(key=lambda x: (order.get(x['type'], 9), x['symbol']))
        return result

    async def get_markets(self, exchange_id: str, force_refresh: bool = False) -> list:
        try:
            if not force_refresh:
                cached = load_cache(exchange_id)
                if cached is not None:
                    print(f"📦 Кеш для {exchange_id}: {len(cached)} ринків")
                    return cached
            print(f"🌐 Завантаження ринків з {exchange_id}…")
            markets = await self._fetch_markets_from_exchange(exchange_id)
            save_cache(exchange_id, markets)
            print(f"✅ {exchange_id}: {len(markets)} ринків збережено")
            return markets
        except Exception as e:
            print(f"⚠️  get_markets {exchange_id}: {e}")
            return []

    # ── OHLCV / ratio ─────────────────────────────────────────────────
    def _max_limit(self, exchange_id: str) -> int:
        return EXCHANGE_LIMITS.get(exchange_id, DEFAULT_LIMIT)

    async def fetch_ratio(
        self,
        sym1: str, ex1_id: str,
        sym2: str, ex2_id: str,
        tf: str,
        limit: int | None = None,
        since: int | None = None,
    ) -> list | None:
        try:
            e1 = await self._get_exchange(ex1_id)
            e2 = await self._get_exchange(ex2_id)

            if limit is None:
                limit = min(self._max_limit(ex1_id), self._max_limit(ex2_id))

            params1 = {'price': 'mark'} if ex1_id.lower() == 'paradex' else {}
            params2 = {'price': 'mark'} if ex2_id.lower() == 'paradex' else {}

            kw1 = dict(limit=limit, params=params1)
            kw2 = dict(limit=limit, params=params2)
            if since:
                kw1['since'] = since
                kw2['since'] = since

            ohlcv1, ohlcv2 = await asyncio.gather(
                e1.fetch_ohlcv(sym1, tf, **kw1),
                e2.fetch_ohlcv(sym2, tf, **kw2),
            )

            if not ohlcv1 or not ohlcv2:
                print(f"⚠️  Порожні дані: {ex1_id if not ohlcv1 else ex2_id}")
                return None

            df1 = pd.DataFrame(ohlcv1, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
            df2 = pd.DataFrame(ohlcv2, columns=['time', 'open', 'high', 'low', 'close', 'vol'])

            df = pd.merge(df1, df2, on='time', how='inner', suffixes=('_1', '_2'))
            if df.empty:
                df = pd.merge(df1, df2, on='time', how='outer', suffixes=('_1', '_2')).sort_values('time')
                df.ffill(inplace=True)
                df.dropna(inplace=True)

            if df.empty:
                print("⚠️  Merge порожній навіть після outer+ffill")
                return None

            df['open']  = df['open_1']  / df['open_2']
            df['high']  = df['high_1']  / df['high_2']
            df['low']   = df['low_1']   / df['low_2']
            df['close'] = df['close_1'] / df['close_2']
            df['time']  = df['time'] / 1000

            return df[['time', 'open', 'high', 'low', 'close']].to_dict('records')

        except Exception as e:
            print(f"⚠️  fetch_ratio: {e}")
            return None

    def load_more_candles(self, sym1, ex1, sym2, ex2, tf, before_ms):
        # Біржі що ігнорують since — потребують post-filter
        SINCE_BROKEN = {'coinex', 'xt'}

        limit = min(self._max_limit(ex1), self._max_limit(ex2))
        tf_ms = TF_MS.get(tf, 3_600_000)
        since = int(before_ms) - limit * tf_ms

        async def _load():
            data = await self.fetch_ratio(sym1, ex1, sym2, ex2, tf, limit=limit, since=since)
            if not data:
                return []
            cutoff = before_ms / 1000

            # Якщо хоча б одна з бірж ігнорує since — фільтруємо тільки по cutoff
            # (дані прийдуть "останні N", а не "з since" — scroll back не працює)
            if ex1 in SINCE_BROKEN or ex2 in SINCE_BROKEN:
                result = [c for c in data if c['time'] < cutoff]
                if not result:
                    # since ігнорується і всі свічки новіші — повернути порожньо
                    # щоб UI зупинив scroll
                    return []
                return result

            return [c for c in data if c['time'] < cutoff]

        future = asyncio.run_coroutine_threadsafe(_load(), self.loop)
        return future.result()
    def load_more_candles111(
        self,
        sym1: str, ex1: str,
        sym2: str, ex2: str,
        tf: str,
        before_ms: int,
    ) -> list:
        limit = min(self._max_limit(ex1), self._max_limit(ex2))
        tf_ms = TF_MS.get(tf, 3_600_000)
        since = int(before_ms) - limit * tf_ms

        async def _load():
            data = await self.fetch_ratio(sym1, ex1, sym2, ex2, tf, limit=limit, since=since)
            if not data:
                return []
            cutoff = before_ms / 1000
            return [c for c in data if c['time'] < cutoff]

        import asyncio as _aio
        future = _aio.run_coroutine_threadsafe(_load(), self.loop)
        return future.result()

