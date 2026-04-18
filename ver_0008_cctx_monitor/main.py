import asyncio
import ccxt.async_support as ccxt

"""
Введіть назву токена (наприклад, SOL): sol

Шукаємо ціни для SOL на 11 біржах...

✅ [WHITEBIT] SOL/USDT (spot): 88.27
✅ [OKX] SOL/USD (spot): 88.32
✅ [BINGX] SOL/USDT (spot): 88.34
✅ [PARADEX] SOL/USD:USDC (swap): 88.308
✅ [BINANCE] SOL/USDT (spot): 88.27
✅ [BYBIT] SOL/USDT (spot): 88.28
✅ [BITGET] SOL/USDC (spot): 88.36
✅ [HYPERLIQUID] SOL/USDC:USDC (swap): 88.2135
✅ [KUCOIN] SOL/USDT (spot): 88.29
✅ [MEXC] SOL/USDT (spot): 88.26
✅ [GATEIO] SOL/USDC (spot): 88.35
"""

# Список популярних бірж для демонстрації
# У CCXT їх понад 100, ви можете додати будь-які з ccxt.exchanges
EXCHANGES = [
    'binance', 'bybit', 'okx', 'gateio', 'kucoin',
    'mexc',  'whitebit', 'bitget', 'bingx', 'hyperliquid',  'paradex',
]
EXCHANGES_all = ['alpaca', 'apex', 'arkham', 'ascendex', 'backpack',
             'bequant', 'bigone', 'binance', 'binancecoinm', 'binanceus',
             'binanceusdm', 'bingx', 'bit2c', 'bitbank', 'bitbns',
             'bitfinex', 'bitflyer', 'bitget', 'bithumb', 'bitmart',
             'bitmex', 'bitopro', 'bitrue', 'bitso', 'bitstamp',
             'bitteam', 'bittrade', 'bitvavo', 'blockchaincom', 'blofin',
             'btcalpha', 'btcbox', 'btcmarkets', 'btcturk', 'bullish',
             'bybit', 'bydfi', 'cex', 'coinbase', 'coinbaseadvanced',
             'coinbaseexchange', 'coinbaseinternational', 'coincatch', 'coincheck', 'coinex',
             'coinmate', 'coinmetro', 'coinone', 'coinsph', 'coinspot',
             'cryptocom', 'cryptomus', 'deepcoin', 'defx', 'delta',
             'deribit', 'derive', 'digifinex', 'dydx', 'exmo',
             'fmfwio', 'foxbit', 'gate', 'gateio', 'gemini',
             'hashkey', 'hibachi', 'hitbtc', 'hollaex', 'htx',
             'huobi', 'hyperliquid', 'independentreserve', 'indodax',
             'kraken', 'krakenfutures', 'kucoin', 'kucoinfutures', 'latoken',
             'lbank', 'luno', 'mercado', 'mexc', 'modetrade',
             'myokx', 'ndax', 'novadax', 'okx', 'okxus',
             'onetrading', 'oxfun', 'p2b', 'paradex', 'paymium',
             'phemex', 'poloniex', 'probit', 'timex', 'tokocrypto',
             'toobit', 'upbit', 'wavesexchange', 'whitebit', 'woo',
             'woofipro', 'xt', 'yobit', 'zaif', 'zebpay',
             'zonda']



async def get_price1(exchange_id, symbol):
    # Створюємо об'єкт біржі
    exchange_class = getattr(ccxt, exchange_id)
    exchange = exchange_class({'enableRateLimit': True})

    try:
        # Завантажуємо ринки, щоб перевірити наявність пари
        markets = await exchange.load_markets()

        # Формуємо пару (наприклад BTC/USDT)
        trading_pair = f"{symbol.upper()}/USDT"

        if trading_pair in markets:
            ticker = await exchange.fetch_ticker(trading_pair)
            price = ticker['last']
            print(f"✅ [{exchange_id.upper()}] {trading_pair}: {price} USDT")
        else:
            # Формуємо пару (наприклад BTC/USDT)
            trading_pair = f"{symbol.upper()}/USDC"

            if trading_pair in markets:
                ticker = await exchange.fetch_ticker(trading_pair)
                price = ticker['last']
                print(f"✅ [{exchange_id.upper()}] {trading_pair}: {price} USDC")
            else:
                # Формуємо пару (наприклад BTC/USDT)
                trading_pair = f"{symbol.upper()}-USD-PERP"
                print(trading_pair)

                if trading_pair in markets:
                    ticker = await exchange.fetch_ticker(trading_pair)
                    price = ticker['last']
                    print(f"✅ [{exchange_id.upper()}] {trading_pair}: {price} USD")
                else:
                    print(f"❌ [{exchange_id.upper()}] Токен {symbol} не знайдено (немає пари до USDT або USDC або USD)")

    except Exception as e:
        print(f"⚠️ [{exchange_id.upper()}] Помилка підключення")
        print(e)
    finally:
        await exchange.close()


async def get_price11(exchange_id, symbol):
    exchange_class = getattr(ccxt, exchange_id)
    exchange = exchange_class({'enableRateLimit': True})

    try:
        markets = await exchange.load_markets()
        symbol_upper = symbol.upper()

        # 1. Складаємо список потенційних назв пар для пошуку
        # Деякі біржі використовують '/', інші '-', треті ':USDT'
        potential_symbols = [
            f"{symbol_upper}/USDT",
            f"{symbol_upper}/USDC",
            f"{symbol_upper}-USD-PERP",  # Популярно на DEX
            f"{symbol_upper}/USD:USDC",  # Формат CCXT для Paradex
            f"{symbol_upper}/USD:USD"  # Формат CCXT для Hyperliquid
        ]

        found_symbol = None
        # Шукаємо пряме співпадіння з нашого списку
        for s in potential_symbols:
            if s in markets:
                found_symbol = s
                break

        # 2. Якщо прямого співпадіння немає, шукаємо будь-яку пару, де є ім'я токена
        if not found_symbol:
            for m_symbol in markets.keys():
                # Шукаємо, щоб токен був на початку (напр. SOL/...)
                if m_symbol.startswith(symbol_upper):
                    found_symbol = m_symbol
                    break

        if found_symbol:
            ticker = await exchange.fetch_ticker(found_symbol)
            price = ticker['last']
            #print(f"✅ [{exchange_id.upper()}] {found_symbol}: {price}")
            # Отримуємо інформацію про ринок для знайденого символу
            market = markets[found_symbol]

            market_type = market.get('type')  # 'spot', 'swap' (perp), 'future' чи 'option'
            is_linear = market.get('linear')  # True, якщо розрахунок у USDT/USDC

            print(f"✅ [{exchange_id.upper()}] {found_symbol} ({market_type}): {price}")
        else:
            print(f"❌ [{exchange_id.upper()}] {symbol_upper} не знайдено.")

    except Exception as e:
        print(f"⚠️ [{exchange_id.upper()}] Помилка: {e}")
    finally:
        await exchange.close()


async def get_price(exchange_id, symbol):
    exchange_class = getattr(ccxt, exchange_id)
    exchange = exchange_class({'enableRateLimit': True})
    symbol_upper = symbol.upper()

    try:
        markets = await exchange.load_markets()

        # Шукаємо правильний маркет серед тисяч доступних
        found_market = None

        for s, m in markets.items():
            # Перевіряємо три умови:
            # 1. Базовий актив — це саме наш токен (наприклад, 'BTC')
            # 2. Актив котування — USDT або USDC (або USD для перпів)
            # 3. Це не опціон (бо там теж є BTC у назві)
            if m.get('base') == symbol_upper and m.get('quote') in ['USDT', 'USDC', 'USD']:
                if m.get('type') in ['spot', 'swap']:  # Тільки спот або перпи
                    found_market = m
                    break

        if found_market:
            symbol_id = found_market['symbol']
            ticker = await exchange.fetch_ticker(symbol_id)
            price = ticker['last']
            m_type = found_market['type']

            print(f"✅ [{exchange_id.upper()}] {symbol_id} ({m_type}): {price}")
        else:
            print(f"❌ [{exchange_id.upper()}] {symbol_upper} не знайдено.")

    except Exception as e:
        print(f"⚠️ [{exchange_id.upper()}] Помилка: {e}")
    finally:
        await exchange.close()


async def main():
    token = input("Введіть назву токена (наприклад, SOL): ").strip()
    print(f"\nШукаємо ціни для {token.upper()} на {len(EXCHANGES)} біржах...\n")

    # Запускаємо перевірку на всіх біржах одночасно
    tasks = [get_price(ex_id, token) for ex_id in EXCHANGES]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())

