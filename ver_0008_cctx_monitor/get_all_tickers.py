import ccxt.async_support as ccxt
import asyncio


async def get_all_prices(exchange_id):
    # Ініціалізуємо біржу
    exchange = getattr(ccxt, exchange_id)()

    try:
        # fetch_tickers без аргументів зазвичай повертає всі пари на біржі
        # Це набагато швидше і легше, ніж load_markets()
        tickers = await exchange.fetch_tickers()

        result = []
        for symbol, data in tickers.items():
            result.append({
                'symbol': symbol,
                'price': data['last'],  # Остання ціна
                'timestamp': data['timestamp'],  # UTC Timestamp у мілісекундах
                'datetime': data['datetime']  # Читабельна дата та час
            })

        return result

    except Exception as e:
        print(f"Помилка: {e}")
    finally:
        await exchange.close()


async def get_fast_token_list(exchange_id):
    """отримати всі тікери швидко якщо ні то через load_markets"""
    try:
        # Спроба отримати все одним махом
        tickers = await exchange_id.fetch_tickers()
        print(f"Отримано {len(tickers)} токенів без повного завантаження")
        return tickers
    except Exception:
        # Якщо біржа "капризна", доводиться вантажити ринки
        print("Біржа потребує load_markets... завантажую")
        await exchange_id.load_markets()
        return await exchange_id.fetch_tickers()

async def main():
    EXCHANGES = [
        'binance', 'bybit', 'okx', 'gateio', 'kucoin',
        'mexc', 'whitebit', 'bitget', 'bingx', 'hyperliquid', 'paradex',
    ]

    exchange= "binance"
    prices = await get_all_prices(exchange)  # можливо швидший варіант отримати назви всіх токенів
    # Виведемо перші 5 для прикладу
    count = len(prices)
    print(prices)


    """for p in prices:
        print(f"{p['symbol']}: {p['price']} (Час: {p['datetime']})")

    print(f"\n Біржа {exchange} повернула ціни для {count} токенів.")"""


asyncio.run(main())