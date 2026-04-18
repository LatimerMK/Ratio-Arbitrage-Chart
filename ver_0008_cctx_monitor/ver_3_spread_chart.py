import webview
import asyncio
import ccxt.async_support as ccxt
import pandas as pd
import time

HTML_CODE = """
<!DOCTYPE html>
<html>
<head>
    <script src="https://unpkg.com/lightweight-charts@4.1.1/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        html, body { height: 100%; margin: 0; padding: 0; background: #131722; overflow: hidden; }
        body { font-family: -apple-system, sans-serif; color: white; display: flex; flex-direction: column; height: 100vh; padding: 10px; box-sizing: border-box; }
        #chart { flex: 1; width: 100%; min-height: 0; background: #131722; }
        .controls { display: flex; gap: 10px; align-items: center; background: #1e222d; padding: 10px 20px; border-radius: 8px; flex-wrap: wrap; }
        select, input, button { padding: 8px; border-radius: 6px; border: 1px solid #363c4e; background: #2a2e39; color: white; outline: none; }
        button { background: #2962ff; border: none; cursor: pointer; font-weight: bold; min-width: 100px; }
        button:hover { background: #1e4bd8; }
        .legend { position: absolute; left: 20px; top: 80px; z-index: 2; font-size: 18px; color: #2962ff; font-weight: bold; pointer-events: none; background: rgba(19, 23, 34, 0.7); padding: 5px; }
        .status { color: #848e9c; font-size: 13px; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="controls">
        <input type="text" id="token" value="BTC" style="width: 60px; text-transform: uppercase;">
        <span>BUY:</span>
        <select id="ex1" style="border-left: 4px solid #00ff00;">
            <option value="binance">Binance</option>
            <option value="bybit">Bybit</option>
            <option value="okx">OKX</option>
            <option value="hyperliquid">Hyperliquid</option>
        </select>
        <span>SELL:</span>
        <select id="ex2" style="border-left: 4px solid #ff0000;">
            <option value="bybit">Bybit</option>
            <option value="binance">Binance</option>
            <option value="okx">OKX</option>
        </select>
        <select id="tf">
            <option value="1m">1 min (History)</option>
            <option value="5m">5 min</option>
        </select>
        <button onclick="startMonitoring()">СТАРТ</button>
    </div>
    <div class="legend" id="legend">Ratio: --</div>
    <div id="chart"></div>
    <div class="status" id="status">Натисніть СТАРТ для запуску тікового графіку</div>

    <script>
        let chart, lineSeries;
        let lastTime = 0;

        function initChart() {
            const container = document.getElementById('chart');
            chart = LightweightCharts.createChart(container, { 
                layout: { background: { color: '#131722' }, textColor: '#d1d4dc' },
                grid: { vertLines: { color: '#2b2b43' }, horzLines: { color: '#2b2b43' } },
                timeScale: { timeVisible: true, secondsVisible: true },
                crosshair: { mode: LightweightCharts.CrosshairMode.Normal }
            });

            lineSeries = chart.addLineSeries({
                color: '#2962ff',
                lineWidth: 2,
                priceFormat: { type: 'price', precision: 6, minMove: 0.000001 },
            });

            lineSeries.createPriceLine({
                price: 1.0, color: '#f0b90b', lineWidth: 1, lineStyle: 2, title: 'PARITY'
            });

            window.addEventListener('resize', () => chart.resize(container.offsetWidth, container.offsetHeight));
        }

        async function startMonitoring() {
            const token = document.getElementById('token').value.toUpperCase();
            const ex1 = document.getElementById('ex1').value;
            const ex2 = document.getElementById('ex2').value;
            const tf = document.getElementById('tf').value;

            if (window.updateInterval) clearInterval(window.updateInterval);
            lineSeries.setData([]); // Очистка

            document.getElementById('status').innerText = "Завантаження історії...";

            // 1. Завантажуємо історію (свічки перетворюємо в лінію)
            const history = await pywebview.api.get_initial_history(token, ex1, ex2, tf);
            if (history && history.length > 0) {
                lineSeries.setData(history);
                lastTime = history[history.length - 1].time;
                chart.timeScale().fitContent();
            }

            document.getElementById('status').innerText = "Real-time тіки активовано";

            // 2. Цикл оновлення тіків (щосекунди)
            window.updateInterval = setInterval(async () => {
                const tick = await pywebview.api.get_current_tick(token, ex1, ex2);
                if (tick) {
                    // Щоб малювати лінію між тіками в межах секунди, 
                    // використовуємо поточний JS timestamp (в секундах)
                    const now = Math.floor(Date.now() / 1000);

                    // Перевірка, щоб час не йшов назад
                    const tickTime = now > lastTime ? now : lastTime + 1;

                    const updateObj = { time: tickTime, value: tick.ratio };
                    lineSeries.update(updateObj);

                    lastTime = tickTime;
                    document.getElementById('legend').innerText = `Ratio: ${tick.ratio.toFixed(6)}`;
                }
            }, 1000); 
        }

        window.onload = initChart;
    </script>
</body>
</html>
"""


class API:
    def __init__(self):
        self.exchanges = {}
        self.symbols_cache = {}
        self.loop = asyncio.new_event_loop()
        import threading
        threading.Thread(target=self._run_loop, daemon=True).start()

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def get_exchange(self, exchange_id):
        if exchange_id not in self.exchanges:
            exch_class = getattr(ccxt, exchange_id)
            self.exchanges[exchange_id] = exch_class({'enableRateLimit': True})
        return self.exchanges[exchange_id]

    async def _get_symbols(self, e1, e2, token):
        key = f"{e1.id}_{e2.id}_{token}"
        if key not in self.symbols_cache:
            # Спрощений пошук (можна замінити на ваші розширені методи)
            await asyncio.gather(e1.load_markets(), e2.load_markets())
            s1 = f"{token}/USDT" if f"{token}/USDT" in e1.markets else None
            s2 = f"{token}/USDT" if f"{token}/USDT" in e2.markets else None
            self.symbols_cache[key] = (s1, s2)
        return self.symbols_cache[key]

    def get_initial_history(self, token, ex1_id, ex2_id, tf):
        """Завантажує історію свічок і повертає їх як точки для лінії"""

        async def _fetch():
            e1 = await self.get_exchange(ex1_id)
            e2 = await self.get_exchange(ex2_id)
            s1, s2 = await self._get_symbols(e1, e2, token)

            ohlcv1, ohlcv2 = await asyncio.gather(
                e1.fetch_ohlcv(s1, tf, limit=100),
                e2.fetch_ohlcv(s2, tf, limit=100)
            )
            df1 = pd.DataFrame(ohlcv1, columns=['time', 'o', 'h', 'l', 'close', 'v'])
            df2 = pd.DataFrame(ohlcv2, columns=['time', 'o', 'h', 'l', 'close', 'v'])

            df = pd.merge(df1, df2, on='time', suffixes=('_1', '_2'))
            df['value'] = df['close_1'] / df['close_2']
            df['time'] = df['time'] / 1000
            return df[['time', 'value']].to_dict('records')

        return asyncio.run_coroutine_threadsafe(_fetch(), self.loop).result()

    def get_current_tick(self, token, ex1_id, ex2_id):
        """Отримує поточну ціну (Last Price) з обох бірж одночасно"""

        async def _fetch():
            try:
                e1 = await self.get_exchange(ex1_id)
                e2 = await self.get_exchange(ex2_id)
                s1, s2 = await self._get_symbols(e1, e2, token)

                # Використовуємо fetch_ticker для отримання останньої ціни (тіка)
                t1, t2 = await asyncio.gather(
                    e1.fetch_ticker(s1),
                    e2.fetch_ticker(s2)
                )
                ratio = t1['last'] / t2['last']
                return {'ratio': ratio}
            except:
                return None

        return asyncio.run_coroutine_threadsafe(_fetch(), self.loop).result()


if __name__ == "__main__":
    api = API()
    window = webview.create_window('Tick Arbitrage Chart', html=HTML_CODE, js_api=api, width=1100, height=750)
    webview.start()