"""import pandas as pd
import ccxt

exchange = ccxt.binance()
markets = exchange.load_markets()
print(markets)
# Перетворюємо в DataFrame
df = pd.DataFrame(markets).transpose()

# Тепер можна дивитися тільки на важливі колонки
print(df[['symbol', 'type', 'base', 'quote', 'active']])"""

import pandas as pd

df = pd.read_csv('mkt.csv')
total_change = df['Change'].sum()

print(f"Загальна сума Change: {total_change}")

