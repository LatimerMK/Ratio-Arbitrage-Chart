import json
import ccxt.async_support as ccxt
import asyncio


async def print_all_markets_line_by_line(exchange_id):
    exchange = getattr(ccxt, exchange_id)()

    try:
        # Завантажуємо всі дані ринків
        markets = await exchange.load_markets()

        print(f"{'=' * 50}")
        print(f"ПОВНИЙ СПИСОК РИНКІВ ДЛЯ {exchange_id.upper()}")
        print(f"{'=' * 50}\n")

        for symbol, info in markets.items():
            # Виводимо роздільник для кожного токена
            print(f"--- РИНОК: {symbol} ---")

            # Виводимо всі дані у форматі JSON з відступами для читабельності
            # indent=4 робить гарну структуру, sort_keys=True впорядковує поля
            print(json.dumps(info, indent=4, ensure_ascii=False))

            print("-" * 30)  # Маленька лінія між токенами

    except Exception as e:
        print(f"Помилка: {e}")
    finally:
        await exchange.close()


# Запуск
asyncio.run(print_all_markets_line_by_line('mexc'))