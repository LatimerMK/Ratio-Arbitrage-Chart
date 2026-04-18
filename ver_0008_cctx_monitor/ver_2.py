import webview
import asyncio
import ccxt.async_support as ccxt
import pandas as pd
import time


HTML_CODE = """
<!DOCTYPE html>
<html>
<head>
    <script src="https://unpkg.com/lightweight-charts@3.8.0/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        html, body {
            height: 100%;
            margin: 0;
            padding: 0;
            background: #131722;
            overflow: hidden; /* Прибирає подвійну прокрутку */
        }
        
        body {
            font-family: -apple-system, sans-serif;
            color: white;
            display: flex;
            flex-direction: column;
            height: 100vh; /* Жорстко фіксуємо висоту під вікно */
            padding: 10px;
            box-sizing: border-box;
        }
        
        #chart {
            flex: 1;
            width: 100%;
            min-height: 0; /* Цей рядок дозволяє елементу стискатися менше його вмісту */
            background: #131722;
        }
        
        .status {
            padding-top: 5px;
            flex-shrink: 0; /* Не дає тексту стискатися */
            color: #848e9c; font-size: 13px; margin-top: 10px;
            
        }
        .body1111 { font-family: -apple-system, sans-serif; background: #131722; color: white; margin: 0; padding: 2px; }
        .controls { display: flex; gap: 10px;  align-items: center; background: #1e222d; padding: 0px 0px 0px 20px; border-radius: 8px; height: 50px; }
        select, input, button { padding: 10px; border-radius: 6px; border: 1px solid #363c4e; background: #2a2e39; color: white; outline: none; }
        button { background: #2962ff; border: none; cursor: pointer; font-weight: bold; min-width: 120px; }
        button:hover { background: #1e4bd8; }
        #chart11111 { width: 100%; height: calc(100vh - 150px); border-radius: 8px; overflow: hidden; background: #131722; }
        .status1111 { color: #848e9c; font-size: 13px; margin-top: 10px; }
        .legend { position: absolute; left: 20px; top: 60px; z-index: 2; font-size: 18px; color: #2962ff; font-weight: bold; pointer-events: none; }
    </style>
</head>
<body>
    <div class="controls">
        <input type="text" id="token" value="BTC" style="width: 80px; text-transform: uppercase;" oninput="fixLayout(this)">
        <h5>BUY: </h5>
        <select id="ex1" style="background: #00800099;">
            <option value="binance">Binance</option>
            <option value="bybit">Bybit</option>
            <option value="okx">OKX</option>
            <option value="gateio">Gate.io</option>
            <option value="whitebit">WhiteBIT</option>
            <option value="kucoinfutures">kucoin futures</option>
            <option value="mexc">MEXC</option>
            <option value="bitget">bitget</option>
            <option value="bingx">bingx</option>
            <option value="hyperliquid">hyperliquid</option>
            <option value="paradex">Paradex</option>
            <option value="htx">HTX</option>
            <option value="aster">Aster</option>
        </select>
        <h5>SELL: </h5>
        <select id="ex2" style="background: #9B131399;">
            <option value="binance">Binance</option>
            <option value="bybit">Bybit</option>
            <option value="okx">OKX</option>
            <option value="gateio">Gate.io</option>
            <option value="whitebit">WhiteBIT</option>
            <option value="kucoinfutures">kucoin futures</option>
            <option value="mexc">MEXC</option>
            <option value="bitget">bitget</option>
            <option value="bingx">bingx</option>
            <option value="hyperliquid">hyperliquid</option>
            <option value="paradex">Paradex</option>
            <option value="htx">HTX</option>
            <option value="aster">Aster</option>
        </select>
        <select id="tf">
            <option value="1m">1 min</option>
            <option value="5m">5 min</option>
            <option value="1h">1 hour</option>
        </select>
        <input type="number" id="limit" value=1000 style="width: 80px;">
        <button onclick="startMonitoring()">Оновити</button>
        
    </div>
    <div class="legend" id="legend">Ratio: --</div>
    <div id="chart"></div>
    <div class="status" id="status">Налаштуйте параметри та натисніть "Оновити"</div>

    <script>
        let chart, candleSeries;
        
        // Функція для виправлення розкладки
        function fixLayout(el) {
            const mapping = {
                'й':'q', 'ц':'w', 'у':'e', 'к':'r', 'е':'t', 'н':'y', 'г':'u', 'ш':'i', 'щ':'o', 'з':'p', 'х':'[', 'ъ':']', 'ё':'`',
                'ф':'a', 'ы':'s', 'і':'s', 'в':'d', 'а':'f', 'п':'g', 'р':'h', 'о':'j', 'л':'k', 'д':'l', 'ж':';',
                'я':'z', 'ч':'x', 'с':'c', 'м':'v', 'и':'b', 'т':'n', 'ь':'m', 'б':',', 'ю':'.'
            };
    
            let value = el.value.toLowerCase();
            let fixedValue = "";
    
            for (let char of value) {
                fixedValue += mapping[char] || char;
            }
    
            el.value = fixedValue.toUpperCase().replace(/[^A-Z0-9]/g, '');
            
        }

        function initChart() {
            const container = document.getElementById('chart');
            chart = LightweightCharts.createChart(container, { 
                layout: { backgroundColor: '#131722', textColor: '#d1d4dc' },
                crosshair: {mode: LightweightCharts.CrosshairMode.Normal},
                grid: { vertLines: { color: '#2b2b43' }, horzLines: { color: '#2b2b43' } },
                timeScale: { timeVisible: true }
            });

            // Замінюємо лінію на свічки
            candleSeries = chart.addCandlestickSeries({
                upColor: '#26a69a', downColor: '#ef5350', 
                borderVisible: false, wickUpColor: '#26a69a', wickDownColor: '#ef5350'
            });

            // Лінія паритету (1.0)
            candleSeries.createPriceLine({
                price: 1.0, color: '#f0b90b', lineWidth: 2,
                lineStyle: 2, title: 'PARITY'
            });
            
            // Респонсивність
            window.addEventListener('resize', () => {
                chart.resize(container.offsetWidth, container.offsetHeight);
            });
        }
        
        
        

        async function startMonitoring() {
            const token = document.getElementById('token').value.toUpperCase();
            const ex1 = document.getElementById('ex1').value;
            const ex2 = document.getElementById('ex2').value;
            const tf = document.getElementById('tf').value;
            const limit = parseInt(document.getElementById('limit').value) || 1000;
        
            const statusEl = document.getElementById('status');
            const legendEl = document.getElementById('legend');
        
            statusEl.innerText = `Завантаження даних для ${token} ... ${ex1} vs ${ex2}`;
        
            try {
                const data = await pywebview.api.get_initial_data(token, ex1, ex2, tf, limit);
                
                if (data && data.length > 0) {
                    // Встановлюємо дані для свічок
                    candleSeries.setData(data); 
                    chart.timeScale().fitContent();
        
                    statusEl.innerText = `Моніторинг: ${ex1} vs ${ex2} (${tf})`;
                    
                    // Беремо ціну закриття (close) останньої свічки для легенди
                    const lastClose = data[data.length - 1].close;
                    legendEl.innerText = `Ratio: ${lastClose.toFixed(6)}`;
        
                    // Очищуємо старий інтервал, якщо він був
                    if (window.updateInterval) clearInterval(window.updateInterval);
                    
                    // Запускаємо оновлення
                    let lastTimestamp = 0; // Зберігаємо час останньої доданої свічки

                    window.updateInterval = setInterval(async () => {
                        const update = await pywebview.api.get_update(token, ex1, ex2, tf, limit);
                        
                        if (update && update.time >= lastTimestamp) {
                            candleSeries.update(update);
                            lastTimestamp = update.time; // Оновлюємо мітку часу
                            legendEl.innerText = `Ratio: ${update.close.toFixed(6)}`;
                        } else {
                            console.warn("Пропущено застарілу свічку:", update?.time);
                        }
                    }, 1000);  /// швидкість оновлення графіків 
                } else {
                    statusEl.innerText = "Помилка: Символ не знайдено або дані порожні.";
                }
            } catch (err) {
                statusEl.innerText = "Помилка виклику API. Перевірте консоль Python.";
                console.error(err);
            }
        }

        // Чекаємо завантаження сторінки
        window.onload = initChart;
    </script>
</body>
</html>
"""


class API:
    def __init__(self):
        self.exchanges = {}  # Кеш об'єктів бірж
        self.symbols_cache = {}  # Кеш знайдених пар
        self.loop = asyncio.new_event_loop()
        import threading
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def _run_async(self, coro):
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result()

    async def get_exchange(self, exchange_id):
        if exchange_id not in self.exchanges:
            print(f"⚙️ Ініціалізація {exchange_id}...")
            exch_class = getattr(ccxt, exchange_id)
            self.exchanges[exchange_id] = exch_class({'enableRateLimit': True})
        return self.exchanges[exchange_id]

    async def get_exchange_tes(self, exchange_id):
        if exchange_id not in self.exchanges:
            print(f"⚙️ Ініціалізація {exchange_id}...")

            # Спеціальна логіка для KuCoin ф'ючерсів
            if exchange_id.lower() == "kucoin":
                # Використовуємо спеціалізований клас для ф'ючерсів
                self.exchanges[exchange_id] = ccxt.kucoinfutures({
                    'enableRateLimit': True,
                    # 'options': {'defaultType': 'swap'} # Додаткова страховка
                })
            else:
                # Стандартна ініціалізація для інших бірж
                exch_class = getattr(ccxt, exchange_id)
                self.exchanges[exchange_id] = exch_class({'enableRateLimit': True})

        return self.exchanges[exchange_id]

    async def _find_best_symbol(self, exchange, token):
        print(exchange)
        """не найшла хайперліквід токени"""
        if exchange.id.lower() == "hyperliquid":
            # Викликаємо спец. функцію (self передається автоматично)
            symbol = await self._find_best_symbol_hype(exchange, token)
            return symbol

        if exchange.id.lower() == "kucoin":
            # Викликаємо спец. функцію (self передається автоматично)
            symbol = await self._find_best_symbol_kucoin(exchange, token)
            return symbol


        markets = await exchange.load_markets()
        token = token.upper()

        search_quotes = ['USDT', 'USDC', 'USD', 'USDTM']



        # 2. Шукаємо Ф'ючерси (Swap/Future)
        for s, m in markets.items():
            if m.get('base') == token and m.get('quote') in search_quotes:
                if m.get('swap') or m.get('future') or m.get('linear'):
                    return s

        # 1. Шукаємо Спот
        for quote in search_quotes:
            s = f"{token}/{quote}"
            if s in markets and markets[s].get('spot'): return s

        print(f"Стандартний метод не знайшов {token}, запускаємо глибокий пошук...")
        return

    async def _find_best_symbol_kucoin(self, exchange, token):
        """Шукає пари у форматі FUSDTM через внутрішні ID KuCoin"""
        markets = await exchange.load_markets()
        token = token.upper()
        print(markets)


        # Формуємо цільовий ID, який KuCoin використовує для ф'ючерсів
        target_id = f"{token}USDTM"

        for symbol, m in markets.items():
            # m['id'] — це якраз те, що приходить від біржі (напр. 'FUSDTM')
            if m.get('id') == target_id:
                return symbol  # Поверне 'F/USDT:USDT' (формат для ордерів CCXT)

        # Якщо не знайшли FUSDTM, спробуємо знайти будь-який лінійний своп на USDT
        for symbol, m in markets.items():
            if m.get('base') == token and m.get('linear') and 'USDT' in m.get('quote', ''):
                return symbol

        return None

        print(f"[{exchange.id}] Символ для {token} не знайдено.")
        return None

    async def _find_best_symbol_hype(self, exchange, token):

        """находить хайпер"""
        markets = await exchange.load_markets()
        token = token.upper()
        search_quotes = ['USDC', 'USDT', 'USD', 'USDTM']

        best_spot = None
        best_swap = None

        for symbol, m in markets.items():
            # Перевіряємо базу
            if m.get('base') != token:
                continue

            # Перевіряємо котирувану валюту
            if m.get('quote') not in search_quotes:
                continue

            # ПЕРЕВІРКА НА "ЖИВУ" ПАРУ (важливо для Hyperliquid)
            info = m.get('info', {})
            # Якщо об'єм за день "0.0" або 0 - це мертвий ринок, ігноруємо його
            volume = float(info.get('dayBaseVlm', 0))
            if volume <= 0:
                continue

            # Якщо ми тут - значить пара "жива"

                # Якщо знайшли живий спот, можна зупинятися

            if m.get('swap') or m.get('linear'):
                best_swap = symbol
                break
            elif m.get('spot'):
                best_spot = symbol


        # Повертаємо спот, якщо ні - то своп
        final_symbol = best_spot or best_swap

        print(f"DEBUG: Found for {token} -> {final_symbol}")
        return final_symbol


    # Додаємо аргумент is_update зі значенням False за замовчуванням
    async def _fetch_ratio_data1111(self, token, ex1_id, ex2_id, tf, limit, is_update=False):
        start_total = time.perf_counter()
        try:
            e1 = await self.get_exchange(ex1_id)
            e2 = await self.get_exchange(ex2_id)

            cache_key = f"{ex1_id}_{ex2_id}_{token}"

            # Шукаємо символи тільки якщо їх немає в кеші
            if cache_key not in self.symbols_cache:
                s1, s2 = await asyncio.gather(
                    self._find_best_symbol(e1, token),
                    self._find_best_symbol(e2, token)
                )
                self.symbols_cache[cache_key] = (s1, s2)

            symbol1, symbol2 = self.symbols_cache[cache_key]

            if not symbol1:
                print(f"⚠️ Не знайдено пару для {token} на {ex1_id}")
                return None
            if not symbol2:
                print(f"⚠️ Не знайдено пару для {token} на {ex2_id}")
                return None

            # ГОЛОВНИЙ СЕКРЕТ ШВИДКОСТІ:
            # Якщо це оновлення (is_update=True), тягнемо лише 5 свічок

            limit_ui = limit

            limit = 2 if is_update else limit_ui
            #if e1 == "KuCoin Futures" or e2 == "KuCoin Futures":
            #    limit = 5 if is_update else 190

            # Визначаємо ліміт
            if is_update:
                # Якщо це Paradex, беремо запас свічок (наприклад 50),
                # щоб точно знайти хоча б одну останню угоду
                limit = 50 if (ex1_id == "paradex" or ex2_id == "paradex") else 2
            else:
                limit = limit_ui

            print(f"limit {limit}")
            print(ex1_id)
            print(ex2_id)


            t_net = time.perf_counter()
            ohlcv1, ohlcv2 = await asyncio.gather(
                e1.fetch_ohlcv(symbol1, tf, limit=limit),
                e2.fetch_ohlcv(symbol2, tf, limit=limit)
            )
            # 1. Перевірка, чи не прийшли порожні дані від API
            if not ohlcv1 or not ohlcv2:
                print(f"⚠️ Одна з бірж повернула порожні дані: {ex1_id if not ohlcv1 else ex2_id}")
                print(ohlcv1)
                return None

            # Обробка Pandas
            df1 = pd.DataFrame(ohlcv1, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
            df2 = pd.DataFrame(ohlcv2, columns=['time', 'open', 'high', 'low', 'close', 'vol'])


            df = pd.merge(df1, df2, on='time', how='inner', suffixes=('_1', '_2'))
            if df.empty:
                print(f"⚠️ Немає спільних точок у часі для {ex1_id} та {ex2_id} (merge result is empty)")
                print(df1)
                return None

            print(f"BUY: {symbol1} - {df['close_1'].iat[-1]} >>>  SELL: {symbol2} - {df['close_2'].iat[-1]}")
            #print(f"df1={df['close_1']}  df2={df['close_2']}")
            df['open'] = df['open_1'] / df['open_2']
            df['high'] = df['high_1'] / df['high_2']
            df['low'] = df['low_1'] / df['low_2']
            df['close'] = df['close_1'] / df['close_2']

            df['time'] = df['time'] / 1000
            data = df[['time', 'open', 'high', 'low', 'close']].to_dict('records')

            if not is_update:
                print(f"🚀 Початкове завантаження (limit=1000): {time.perf_counter() - start_total:.3f} сек")
            return data

        except Exception as e:
            print(f"⚠️ Помилка в _fetch_ratio_data: {e}")
            return None

    async def _fetch_ratio_data(self, token, ex1_id, ex2_id, tf, limit, is_update=False):
        start_total = time.perf_counter()
        try:
            e1 = await self.get_exchange(ex1_id)
            e2 = await self.get_exchange(ex2_id)

            # 1. Формуємо ключі кешу та отримуємо символи
            cache_key = f"{ex1_id}_{ex2_id}_{token}"
            if cache_key not in self.symbols_cache:
                s1, s2 = await asyncio.gather(
                    self._find_best_symbol(e1, token),
                    self._find_best_symbol(e2, token)
                )
                self.symbols_cache[cache_key] = (s1, s2)
            symbol1, symbol2 = self.symbols_cache[cache_key]

            # 2. Налаштовуємо параметри для кожної біржі
            # Для Paradex використовуємо Mark Price
            params1 = {'price': 'mark'} if ex1_id.lower() == 'paradex' else {}
            params2 = {'price': 'mark'} if ex2_id.lower() == 'paradex' else {}

            # 3. Розраховуємо ліміт та часове вікно (since)
            # Це важливо, щоб Paradex віддавав історію, а не 1 свічку
            limit_ui = limit
            current_limit = 10 if is_update else limit_ui


            # 4. Запитуємо дані паралельно
            ohlcv1, ohlcv2 = await asyncio.gather(
                e1.fetch_ohlcv(symbol1, tf, limit=current_limit, params=params1),
                e2.fetch_ohlcv(symbol2, tf, limit=current_limit, params=params2)
            )

            if not ohlcv1 or not ohlcv2:
                print(f"⚠️ Порожні дані від: {ex1_id if not ohlcv1 else ex2_id}")
                return None

            # 5. Обробка в Pandas
            df1 = pd.DataFrame(ohlcv1, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
            df2 = pd.DataFrame(ohlcv2, columns=['time', 'open', 'high', 'low', 'close', 'vol'])

            # Використовуємо 'inner' для синхронізації або 'outer' з ffill для максимальної стабільності
            df = pd.merge(df1, df2, on='time', how='inner', suffixes=('_1', '_2'))

            if df.empty:
                # Якщо inner merge порожній, спробуємо outer+ffill
                df = pd.merge(df1, df2, on='time', how='outer', suffixes=('_1', '_2')).sort_values('time')
                df.ffill(inplace=True)
                df.dropna(inplace=True)

            # 6. Розрахунок Ratio
            df['open'] = df['open_1'] / df['open_2']
            df['high'] = df['high_1'] / df['high_2']
            df['low'] = df['low_1'] / df['low_2']
            df['close'] = df['close_1'] / df['close_2']

            # Якщо це оновлення, нам потрібен тільки останній результат
            if is_update:
                df = df.tail(1)

            df['time'] = df['time'] / 1000
            data = df[['time', 'open', 'high', 'low', 'close']].to_dict('records')

            return data

        except Exception as e:
            print(f"⚠️ Помилка в _fetch_ratio_data: {e}")
            return None

    # Вказуємо is_update=False для першого запуску
    def get_initial_data(self, token, ex1, ex2, tf, limit):
        return self._run_async(self._fetch_ratio_data(token, ex1, ex2, tf, limit, is_update=False))

    # Вказуємо is_update=True для регулярного оновлення
    def get_update(self, token, ex1, ex2, tf, limit):
        data = self._run_async(self._fetch_ratio_data(token, ex1, ex2, tf, limit, is_update=True))
        return data[-1] if data and len(data) > 0 else None

    def on_close(self):
        async def close_all():
            for ex in self.exchanges.values(): await ex.close()
            self.loop.stop()

        if self.loop.is_running():
            asyncio.run_coroutine_threadsafe(close_all(), self.loop)


if __name__ == "__main__":
    api = API()
    window = webview.create_window(
        'Crypto Arbitrage Ratio Scanner',
        html=HTML_CODE,
        js_api=api,
        width=1100,
        height=700,
        background_color='#131722'
    )
    webview.start(debug=True)

"""['alp', 'alpaca', 'apex', 'arkham', 'ascendex', 'aster', 'backpack', 'bequant', 'bigone', 'binance', 'binancecoinm', 'binanceus', 'binanceusdm', 'bingx', 'bit2c', 'bitbank', 'bitbns', 'bitfinex', 'bitflyer', 'bitget', 'bithumb', 'bitmart', 'bitmex', 'bitopro', 'bitrue', 'bitso', 'bitstamp', 'bitteam', 'bittrade', 'bitvavo', 'blockchaincom', 'blofin', 'btcbox', 'btcmarkets', 'btcturk', 'bullish', 'bybit', 'bydfi', 'cex', 'coinbase', 'coinbaseadvanced', 'coinbaseexchange', 'coinbaseinternational', 'coincatch', 'coincheck', 'coinex', 'coinmate', 'coinmetro', 'coinone', 'coinsph', 'coinspot', 'cryptocom', 'cryptomus', 'deepcoin', 'defx', 'delta', 'deribit', 'derive', 'digifinex', 'dydx', 'exmo', 'fmfwio', 'foxbit', 'gate', 'gateio', 'gemini', 'hashkey', 'hibachi', 'hitbtc', 'hollaex', 'htx', 'huobi', 'hyperliquid', 'independentreserve', 'indodax', 'kraken', 'krakenfutures', 'kucoin', 'kucoinfutures', 'latoken', 'lbank', 'luno', 'mercado', 'mexc', 'modetrade', 'myokx', 'ndax', 'novadax', 'okx', 'okxus', 'onetrading', 'oxfun', 'p2b', 'paradex', 'paymium', 'phemex', 'poloniex', 'timex', 'tokocrypto', 'toobit', 'upbit', 'wavesexchange', 'whitebit', 'woo', 'woofipro', 'xt', 'yobit', 'zaif', 'zebpay', 'zonda']
"""