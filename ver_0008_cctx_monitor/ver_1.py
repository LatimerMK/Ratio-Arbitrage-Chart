import webview
import asyncio
import ccxt.async_support as ccxt
import pandas as pd

HTML_CODE1 = """
<!DOCTYPE html>
<html>
<head>
    <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #131722; color: white; margin: 0; padding: 20px; }
        .controls { display: flex; gap: 10px; margin-bottom: 20px; align-items: center; background: #1e222d; padding: 15px; border-radius: 8px; }
        select, input, button { padding: 10px; border-radius: 6px; border: 1px solid #363c4e; background: #2a2e39; color: white; outline: none; }
        button { background: #2962ff; border: none; cursor: pointer; font-weight: bold; }
        button:hover { background: #1e4bd8; }
        #chart { width: 100%; height: 550px; border-radius: 8px; overflow: hidden; }
        .status { color: #848e9c; font-size: 13px; margin-top: 10px; padding: 0 5px; }
        .legend { position: absolute; left: 30px; top: 120px; z-index: 2; font-size: 14px; pointer-events: none; }
    </style>
</head>
<body>
    <div class="controls">
        <input type="text" id="token" value="BTC" placeholder="Token (BTC)">
        <select id="ex1">
            <option value="binance">Binance</option>
            <option value="bybit">Bybit</option>
            <option value="okx">OKX</option>
            <option value="gateio">Gate.io</option>
            <option value="paradex">Paradex</option>
            <option value="hyperliquid">Hyperliquid</option>
        </select>
        <select id="ex2">
            <option value="bybit">Bybit</option>
            <option value="binance">Binance</option>
            <option value="okx">OKX</option>
            <option value="mexc">MEXC</option>
            <option value="whitebit">WhiteBIT</option>
        </select>
        <select id="tf">
            <option value="1m">1 min</option>
            <option value="5m">5 min</option>
            <option value="15m">15 min</option>
            <option value="1h">1 hour</option>
        </select>
        <button onclick="startMonitoring()">Update Chart</button>
    </div>
    <div class="legend" id="legend">Ratio: --</div>
    <div id="chart"></div>
    <div class="status" id="status">Введіть токен та оберіть біржі...</div>

    <script>
        let chart, lineSeries, baseline;

        function initChart() {
            const chartOptions = { 
                layout: { background: { color: '#131722' }, textColor: '#d1d4dc' },
                grid: { vertLines: { color: 'rgba(42, 46, 57, 0.5)' }, horzLines: { color: 'rgba(42, 46, 57, 0.5)' } },
                timeScale: { timeVisible: true, secondsVisible: false, borderColor: '#485c7b' },
                rightPriceScale: { borderColor: '#485c7b' }
            };
            chart = LightweightCharts.createChart(document.getElementById('chart'), chartOptions);
            lineSeries = chart.addLineSeries({ 
                color: '#2962ff', 
                lineWidth: 2,
                priceFormat: { type: 'price', precision: 6, minMove: 0.000001 }
            });

            // Лінія паритету (Ratio = 1)
            lineSeries.createPriceLine({
                price: 1.0,
                color: '#ef5350',
                lineWidth: 1,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                axisLabelVisible: true,
                title: 'Parity (1.0)',
            });
        }

        async function startMonitoring() {
            const token = document.getElementById('token').value.toUpperCase();
            const ex1 = document.getElementById('ex1').value;
            const ex2 = document.getElementById('ex2').value;
            const tf = document.getElementById('tf').value;

            document.getElementById('status').innerText = `Пошук ${token} на біржах...`;

            const data = await pywebview.api.get_initial_data(token, ex1, ex2, tf);
            if (data && data.length > 0) {
                lineSeries.setData(data);
                document.getElementById('status').innerText = `Моніторинг: ${ex1.toUpperCase()} / ${ex2.toUpperCase()}`;
                document.getElementById('legend').innerText = `Ratio ${token}: ${data[data.length-1].value.toFixed(6)}`;

                if (window.updateInterval) clearInterval(window.updateInterval);
                window.updateInterval = setInterval(async () => {
                    const update = await pywebview.api.get_update(token, ex1, ex2, tf);
                    if (update) {
                        lineSeries.update(update);
                        document.getElementById('legend').innerText = `Ratio ${token}: ${update.value.toFixed(6)}`;
                    }
                }, 5000);
            } else {
                document.getElementById('status').innerText = "Помилка: Токен не знайдено або API недоступне.";
            }
        }
        window.onload = initChart;
    </script>
</body>
</html>
"""

HTML_CODE = """
<!DOCTYPE html>
<html>
<head>
    <script src="https://unpkg.com/lightweight-charts@3.8.0/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        body { font-family: -apple-system, sans-serif; background: #131722; color: white; margin: 0; padding: 20px; }
        .controls { display: flex; gap: 10px; margin-bottom: 20px; align-items: center; background: #1e222d; padding: 15px; border-radius: 8px; }
        select, input, button { padding: 10px; border-radius: 6px; border: 1px solid #363c4e; background: #2a2e39; color: white; outline: none; }
        button { background: #2962ff; border: none; cursor: pointer; font-weight: bold; min-width: 120px; }
        button:hover { background: #1e4bd8; }
        #chart { width: 100%; height: calc(100vh - 150px); border-radius: 8px; overflow: hidden; background: #131722; }
        .status { color: #848e9c; font-size: 13px; margin-top: 10px; }
        .legend { position: absolute; left: 30px; top: 130px; z-index: 2; font-size: 18px; color: #2962ff; font-weight: bold; pointer-events: none; }
    </style>
</head>
<body>
    <div class="controls">
        <input type="text" id="token" value="BTC" style="width: 80px;">
        <select id="ex1">
            <option value="binance">Binance</option>
            <option value="bybit">Bybit</option>
            <option value="okx">OKX</option>
            <option value="gateio">Gate.io</option>
            <option value="whitebit">WhiteBIT</option>
            <option value="kucoin">kucoin</option>
            <option value="mexc">MEXC</option>
            <option value="bitget">bitget</option>
            <option value="bingx">bingx</option>
            <option value="hyperliquid">hyperliquid</option>
            <option value="paradex">Paradex</option>
        </select>
        <select id="ex2">
            <option value="binance">Binance</option>
            <option value="bybit">Bybit</option>
            <option value="okx">OKX</option>
            <option value="gateio">Gate.io</option>
            <option value="whitebit">WhiteBIT</option>
            <option value="kucoin">kucoin</option>
            <option value="mexc">MEXC</option>
            <option value="bitget">bitget</option>
            <option value="bingx">bingx</option>
            <option value="hyperliquid">hyperliquid</option>
            <option value="paradex">Paradex</option>
        </select>
        <select id="tf">
            <option value="1m">1 min</option>
            <option value="5m">5 min</option>
            <option value="1h">1 hour</option>
        </select>
        <button onclick="startMonitoring()">Оновити</button>
    </div>
    <div class="legend" id="legend">Ratio: --</div>
    <div id="chart"></div>
    <div class="status" id="status">Налаштуйте параметри та натисніть "Оновити"</div>

    <script>
        let chart, candleSeries;

        function initChart() {
            const container = document.getElementById('chart');
            chart = LightweightCharts.createChart(container, { 
                layout: { backgroundColor: '#131722', textColor: '#d1d4dc' },
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

            const statusEl = document.getElementById('status');
            const legendEl = document.getElementById('legend');

            statusEl.innerText = `Завантаження даних для ${token} ... ${ex1} vs ${ex2}`;

            try {
                const data = await pywebview.api.get_initial_data(token, ex1, ex2, tf);

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
                    window.updateInterval = setInterval(async () => {
                        const update = await pywebview.api.get_update(token, ex1, ex2, tf);
                        if (update) {
                            candleSeries.update(update);
                            legendEl.innerText = `Ratio: ${update.close.toFixed(6)}`;
                        }
                    }, 5000);
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
    async def _find_best_symbol(self, exchange, token):
        """Шукає символ на біржі: спочатку Спот, потім Ф'ючерси"""
        markets = await exchange.load_markets()
        token = token.upper()

        # Пріоритети пошуку
        search_quotes = ['USDT', 'USDC', 'USD']

        # 1. Спробуємо знайти Спот
        for quote in search_quotes:
            s = f"{token}/{quote}"
            if s in markets and markets[s].get('spot'):
                return s

        # 2. Спробуємо знайти Swap (Perpetual Futures)
        for quote in search_quotes:
            # Формати для різних бірж (Binance, Bybit, OKX використовують :USDT або подібне)
            for s in markets:
                m = markets[s]
                if m.get('base') == token and m.get('quote') in search_quotes:
                    if m.get('swap') or m.get('future'):
                        return s
        return None

    async def _fetch_ratio_data(self, token, ex1_id, ex2_id, tf):
        try:
            e1 = getattr(ccxt, ex1_id)({'enableRateLimit': True})
            e2 = getattr(ccxt, ex2_id)({'enableRateLimit': True})

            symbol1 = await self._find_best_symbol(e1, token)
            symbol2 = await self._find_best_symbol(e2, token)

            if not symbol1 or not symbol2:
                await e1.close();
                await e2.close()
                return None

            ohlcv1 = await e1.fetch_ohlcv(symbol1, tf, limit=1000)
            ohlcv2 = await e2.fetch_ohlcv(symbol2, tf, limit=1000)

            await e1.close();
            await e2.close()

            # Створюємо DataFrame для обох бірж
            cols = ['time', 'open', 'high', 'low', 'close', 'vol']
            df1 = pd.DataFrame(ohlcv1, columns=cols)
            df2 = pd.DataFrame(ohlcv2, columns=cols)

            # Об'єднуємо дані за часом
            df = pd.merge(df1, df2, on='time', suffixes=('_1', '_2'))

            # Розраховуємо кожне значення свічки Ratio
            df['open'] = df['open_1'] / df['open_2']
            df['high'] = df['high_1'] / df['high_2']
            df['low'] = df['low_1'] / df['low_2']
            df['close'] = df['close_1'] / df['close_2']

            # Форматуємо для JS (час в секундах)
            df['time'] = df['time'] / 1000
            return df[['time', 'open', 'high', 'low', 'close']].to_dict('records')
        except Exception as e:
            print(f"Помилка: {e}")
            return None

    def get_initial_data(self, token, ex1, ex2, tf):
        return asyncio.run(self._fetch_ratio_data(token, ex1, ex2, tf))

    def get_update(self, token, ex1, ex2, tf):
        data = asyncio.run(self._fetch_ratio_data(token, ex1, ex2, tf))
        return data[-1] if data and len(data) > 0 else None


if __name__ == "__main__":
    api = API()
    window = webview.create_window(
        'Crypto Arbitrage Ratio Scanner',
        html=HTML_CODE,
        js_api=api,
        width=1100,
        height=750,
        background_color='#131722'
    )
    webview.start(debug=True)