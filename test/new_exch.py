"""
Тести нових бірж перед інтеграцією в проект.
Перевіряє: ініціалізацію, ринки, OHLCV, параметр since.

Запуск:
    python test_new_exchanges.py
    python test_new_exchanges.py --exchange bitmart   # одна біржа
    python test_new_exchanges.py --quick              # без slow-тестів
"""

import asyncio
import argparse
import time
import ccxt.async_support as ccxt

# ── Налаштування тестів ────────────────────────────────────────────────

NEW_EXCHANGES = ['bitmart', 'coinex', 'xt']

# Які символи спробувати для OHLCV (перший що спрацює)
PROBE_SYMBOLS = ['BTC/USDT', 'BTC/USDT:USDT', 'ETH/USDT', 'ETH/USDT:USDT']

TIMEFRAME = '1h'
OHLCV_LIMIT = 10

# Референсна біржа для тесту ratio (вже є в проекті)
REF_EXCHANGE = 'binance'
REF_SYMBOL   = 'BTC/USDT:USDT'

# ── Утиліти ────────────────────────────────────────────────────────────

RESET  = '\033[0m'
GREEN  = '\033[92m'
RED    = '\033[91m'
YELLOW = '\033[93m'
BLUE   = '\033[94m'
BOLD   = '\033[1m'

def ok(msg):    print(f"  {GREEN}✅ {msg}{RESET}")
def fail(msg):  print(f"  {RED}❌ {msg}{RESET}")
def warn(msg):  print(f"  {YELLOW}⚠️  {msg}{RESET}")
def info(msg):  print(f"  {BLUE}ℹ️  {msg}{RESET}")
def header(msg):print(f"\n{BOLD}{'─'*55}\n  {msg}\n{'─'*55}{RESET}")

results: dict[str, dict] = {}

def record(exchange_id, key, value):
    results.setdefault(exchange_id, {})[key] = value

# ── Тест 1: Ініціалізація ──────────────────────────────────────────────

async def test_init(exchange_id: str) -> ccxt.Exchange | None:
    header(f"[{exchange_id}] 1. Ініціалізація")
    try:
        cls = getattr(ccxt, exchange_id)
        ex = cls({'enableRateLimit': True})
        ok(f"Клас знайдено: {type(ex).__name__}")
        record(exchange_id, 'init', True)
        return ex
    except Exception as e:
        fail(f"Помилка ініціалізації: {e}")
        record(exchange_id, 'init', False)
        return None

# ── Тест 2: Типи ринків і рекомендовані options ────────────────────────

async def test_market_types(ex: ccxt.Exchange, exchange_id: str):
    header(f"[{exchange_id}] 2. Типи ринків та options")
    try:
        markets = await ex.load_markets()
        types = {}
        for m in markets.values():
            t = m.get('type', 'unknown')
            types[t] = types.get(t, 0) + 1

        info(f"Типи ринків: {dict(sorted(types.items()))}")
        record(exchange_id, 'market_types', types)

        # Рекомендація options для _get_exchange
        has_swap = any(m.get('swap') or m.get('type') == 'swap' for m in markets.values())
        has_linear = any(m.get('linear') for m in markets.values())

        if has_swap or has_linear:
            warn(f"Є swap/linear ринки → можливо потрібен defaultType")
            record(exchange_id, 'needs_options', True)

            # Перевіряємо defaultType
            for dtype in ('swap', 'future', 'linear'):
                try:
                    cls = getattr(ccxt, exchange_id)
                    ex2 = cls({'enableRateLimit': True,
                               'options': {'defaultType': dtype}})
                    m2 = await ex2.load_markets()
                    count = sum(1 for mm in m2.values()
                                if mm.get('swap') or mm.get('linear'))
                    info(f"  defaultType='{dtype}' → {count} swap/linear ринків")
                    await ex2.close()
                except Exception as e:
                    warn(f"  defaultType='{dtype}' → помилка: {e}")
        else:
            ok("Специфічні options не потрібні")
            record(exchange_id, 'needs_options', False)

        ok(f"Всього ринків: {len(markets)}")
        record(exchange_id, 'total_markets', len(markets))

    except Exception as e:
        fail(f"load_markets: {e}")
        record(exchange_id, 'market_types', None)

# ── Тест 3: Знайти робочий символ ─────────────────────────────────────

async def test_find_symbol(ex: ccxt.Exchange, exchange_id: str) -> str | None:
    header(f"[{exchange_id}] 3. Пошук робочого символу")
    try:
        markets = ex.markets or await ex.load_markets()
    except Exception as e:
        fail(f"Не вдалося отримати ринки: {e}")
        return None

    for sym in PROBE_SYMBOLS:
        if sym in markets:
            ok(f"Символ знайдено: {sym}")
            record(exchange_id, 'test_symbol', sym)
            return sym

    # fallback: перший BTC пара
    btc_pairs = [s for s in markets if s.startswith('BTC')]
    if btc_pairs:
        sym = btc_pairs[0]
        warn(f"Стандартні символи не знайдено, використовуємо: {sym}")
        record(exchange_id, 'test_symbol', sym)
        return sym

    fail("Жодного BTC символу не знайдено")
    record(exchange_id, 'test_symbol', None)
    return None

# ── Тест 4: fetch_ohlcv базовий ───────────────────────────────────────

async def test_ohlcv(ex: ccxt.Exchange, exchange_id: str, symbol: str):
    header(f"[{exchange_id}] 4. fetch_ohlcv (базовий)")
    try:
        if not ex.has.get('fetchOHLCV'):
            fail("fetchOHLCV не підтримується!")
            record(exchange_id, 'ohlcv', False)
            return

        # Перевіряємо доступні таймфрейми
        tfs = list(ex.timeframes.keys()) if ex.timeframes else []
        info(f"Таймфрейми: {tfs[:15]}{'...' if len(tfs) > 15 else ''}")
        record(exchange_id, 'timeframes', tfs)

        tf = TIMEFRAME if TIMEFRAME in tfs else (tfs[0] if tfs else '1h')
        if tf != TIMEFRAME:
            warn(f"'{TIMEFRAME}' відсутній, використовуємо '{tf}'")

        t0 = time.time()
        data = await ex.fetch_ohlcv(symbol, tf, limit=OHLCV_LIMIT)
        elapsed = time.time() - t0

        if not data:
            fail("Порожня відповідь")
            record(exchange_id, 'ohlcv', False)
            return

        ok(f"Отримано {len(data)} свічок за {elapsed:.2f}с")
        first = data[0]
        info(f"  Перша свічка: ts={first[0]}, o={first[1]}, h={first[2]}, l={first[3]}, c={first[4]}, v={first[5]}")

        # Перевірка структури
        if len(first) == 6:
            ok("Структура OHLCV коректна [ts,o,h,l,c,v]")
        else:
            warn(f"Нестандартна структура: {len(first)} полів")

        record(exchange_id, 'ohlcv', True)
        record(exchange_id, 'ohlcv_tf', tf)

    except Exception as e:
        fail(f"fetch_ohlcv: {e}")
        record(exchange_id, 'ohlcv', False)

# ── Тест 5: fetch_ohlcv з параметром since ────────────────────────────

async def test_ohlcv_since(ex: ccxt.Exchange, exchange_id: str, symbol: str):
    header(f"[{exchange_id}] 5. fetch_ohlcv з since (load_more_candles)")
    try:
        tf = results[exchange_id].get('ohlcv_tf', TIMEFRAME)
        tfs_ms = {'1m': 60000, '5m': 300000, '15m': 900000, '1h': 3600000}
        tf_ms = tfs_ms.get(tf, 3600000)

        # since = 200 свічок назад
        since = int(time.time() * 1000) - 200 * tf_ms

        t0 = time.time()
        data = await ex.fetch_ohlcv(symbol, tf, since=since, limit=OHLCV_LIMIT)
        elapsed = time.time() - t0

        if not data:
            fail("Порожня відповідь при since")
            record(exchange_id, 'since_works', False)
            return

        first_ts = data[0][0]
        diff_candles = (first_ts - since) / tf_ms

        ok(f"Отримано {len(data)} свічок з since, за {elapsed:.2f}с")
        info(f"  since={since}, перша_ts={first_ts}, зсув≈{diff_candles:.1f} свічок")

        if abs(diff_candles) < 5:
            ok("since дотримується точно")
            record(exchange_id, 'since_works', True)
        elif abs(diff_candles) < 20:
            warn(f"since неточний (~{diff_candles:.0f} свічок зсуву) — прийнятно")
            record(exchange_id, 'since_works', 'partial')
        else:
            fail(f"since ігнорується (зсув {diff_candles:.0f} свічок)!")
            record(exchange_id, 'since_works', False)

    except Exception as e:
        fail(f"fetch_ohlcv з since: {e}")
        record(exchange_id, 'since_works', False)

# ── Тест 6: Рекомендований ліміт ──────────────────────────────────────

async def test_limit(ex: ccxt.Exchange, exchange_id: str, symbol: str):
    header(f"[{exchange_id}] 6. Визначення максимального ліміту")
    try:
        tf = results[exchange_id].get('ohlcv_tf', TIMEFRAME)

        # Перевіряємо різні ліміти
        for lim in [200, 500, 1000]:
            try:
                data = await ex.fetch_ohlcv(symbol, tf, limit=lim)
                got = len(data)
                if got >= lim * 0.9:  # отримали ~те що просили
                    ok(f"limit={lim} → {got} свічок ✓")
                    record(exchange_id, 'recommended_limit', lim)
                else:
                    warn(f"limit={lim} → {got} свічок (менше запитаного)")
                    record(exchange_id, 'recommended_limit', got)
                    break
            except Exception as e:
                warn(f"limit={lim} → помилка: {e}")
                break

    except Exception as e:
        fail(f"Тест ліміту: {e}")

# ── Тест 7: Ratio з reference exchange ───────────────────────────────

async def test_ratio_compatibility(ex: ccxt.Exchange, exchange_id: str, symbol: str):
    header(f"[{exchange_id}] 7. Сумісність для ratio з {REF_EXCHANGE}")
    try:
        import pandas as pd

        ref_cls = getattr(ccxt, REF_EXCHANGE)
        ref_ex = ref_cls({'enableRateLimit': True,
                          'options': {'defaultType': 'future',
                                      'fetchMarkets': ['linear']}})
        tf = results[exchange_id].get('ohlcv_tf', TIMEFRAME)

        data1, data2 = await asyncio.gather(
            ref_ex.fetch_ohlcv(REF_SYMBOL, tf, limit=50),
            ex.fetch_ohlcv(symbol, tf, limit=50),
        )
        await ref_ex.close()

        df1 = pd.DataFrame(data1, columns=['time','o','h','l','c','v'])
        df2 = pd.DataFrame(data2, columns=['time','o','h','l','c','v'])

        df_inner = pd.merge(df1, df2, on='time', how='inner')
        df_outer = pd.merge(df1, df2, on='time', how='outer')

        info(f"  {REF_EXCHANGE} свічок: {len(df1)}, {exchange_id}: {len(df2)}")
        info(f"  Inner merge: {len(df_inner)}, Outer: {len(df_outer)}")

        if len(df_inner) > 5:
            ok(f"Inner merge дає {len(df_inner)} свічок — ratio працюватиме")
            record(exchange_id, 'ratio_compatible', True)
        elif len(df_outer) > 5:
            warn(f"Inner merge малий ({len(df_inner)}), але outer={len(df_outer)} — потрібен ffill")
            record(exchange_id, 'ratio_compatible', 'needs_ffill')
        else:
            fail("Дані не перетинаються — ratio неможливий")
            record(exchange_id, 'ratio_compatible', False)

    except Exception as e:
        fail(f"Тест ratio: {e}")
        record(exchange_id, 'ratio_compatible', False)

# ── Підсумок ──────────────────────────────────────────────────────────

def print_summary():
    print(f"\n{BOLD}{'═'*55}")
    print("  ПІДСУМОК ТА РЕКОМЕНДОВАНІ ЗМІНИ")
    print(f"{'═'*55}{RESET}\n")

    config_lines = []
    options_lines = []

    for ex_id, r in results.items():
        print(f"{BOLD}▸ {ex_id.upper()}{RESET}")

        # init
        if not r.get('init'):
            print(f"  {RED}Ініціалізація провалилась — пропустити інтеграцію{RESET}")
            continue

        # ліміт
        lim = r.get('recommended_limit', 500)
        config_lines.append(f"    '{ex_id}': {lim},")
        print(f"  Ліміт: {lim}")

        # since
        since_ok = r.get('since_works')
        if since_ok == True:
            print(f"  {GREEN}since: працює коректно{RESET}")
        elif since_ok == 'partial':
            print(f"  {YELLOW}since: неточний, але прийнятний{RESET}")
        else:
            print(f"  {RED}since: не працює → load_more_candles може давати неточні дані!{RESET}")

        # ratio
        ratio = r.get('ratio_compatible')
        if ratio == True:
            print(f"  {GREEN}ratio: сумісний{RESET}")
        elif ratio == 'needs_ffill':
            print(f"  {YELLOW}ratio: потрібен ffill (вже є в коді){RESET}")
        else:
            print(f"  {RED}ratio: проблеми із сумісністю{RESET}")

        # options
        if r.get('needs_options'):
            options_lines.append(f"""
        elif exchange_id == '{ex_id}':
            options['options'] = {{
                'defaultType': 'swap',  # ← уточни після перегляду тестів
            }}""")
        print()

    # --- config.py patch ---
    print(f"{BOLD}── Зміни в config.py (EXCHANGE_LIMITS) ──{RESET}")
    print("EXCHANGE_LIMITS: dict[str, int] = {")
    print("    # ... існуючі ...")
    for line in config_lines:
        print(line)
    print("}")

    # --- exchange_manager.py patch ---
    if options_lines:
        print(f"\n{BOLD}── Зміни в exchange_manager.py (_get_exchange) ──{RESET}")
        print("Додай в блок if/elif після існуючих бірж:")
        for line in options_lines:
            print(line)
    else:
        print(f"\n{GREEN}exchange_manager.py: специфічні options не потрібні{RESET}")

# ── Runner ─────────────────────────────────────────────────────────────

async def run_exchange(exchange_id: str, quick: bool):
    ex = await test_init(exchange_id)
    if ex is None:
        return

    try:
        await test_market_types(ex, exchange_id)
        symbol = await test_find_symbol(ex, exchange_id)

        if symbol:
            await test_ohlcv(ex, exchange_id, symbol)
            if results[exchange_id].get('ohlcv'):
                await test_ohlcv_since(ex, exchange_id, symbol)
                if not quick:
                    await test_limit(ex, exchange_id, symbol)
                    await test_ratio_compatibility(ex, exchange_id, symbol)
    finally:
        await ex.close()

async def main(exchanges: list[str], quick: bool):
    for ex_id in exchanges:
        await run_exchange(ex_id, quick)
        await asyncio.sleep(0.5)  # ввічлива пауза між біржами
    print_summary()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--exchange', help='Запустити тільки одну біржу')
    parser.add_argument('--quick', action='store_true',
                        help='Пропустити тест ліміту та ratio (швидший запуск)')
    args = parser.parse_args()

    target = [args.exchange] if args.exchange else NEW_EXCHANGES

    # Якщо є невалідна біржа — одразу попередити
    for e in target:
        if e not in ccxt.exchanges:
            print(f"{RED}❌ '{e}' відсутня в ccxt. Доступні: {[x for x in ccxt.exchanges if e in x]}{RESET}")
            exit(1)

    asyncio.run(main(target, args.quick))