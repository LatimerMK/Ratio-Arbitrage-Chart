import webview
import asyncio
import ccxt.async_support as ccxt
import pandas as pd
import time
import logging

# Налаштування логування для консолі
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

HTML_CODE = """
<!DOCTYPE html>
<html>
<head>
    <script src="https://unpkg.com/lightweight-charts@4.1.1/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        html, body { height: 100%; margin: 0; padding: 0; background: #131722; overflow: hidden; }
        body { font-family: -apple-system, sans-serif; color: white; display: flex; flex-direction: column; height: 100vh; padding: 10px; box-sizing: border-box; }
        #chart { flex: 1; width: 100%; min-height: 0; background: #131722; position: relative; }
        .controls { display: flex; gap: 10px; align-items: center; background: #1e222d; padding: 10px 20px; border-radius: 8px; flex-wrap: wrap; margin-bottom: 5px; }
        select, input, button { padding: 8px; border-radius: 6px; border: 1px solid #363c4e; background: #2a2e39; color: white; outline: none; font-size: 13px; }
        button { background: #2962ff; border: none; cursor: pointer; font-weight: bold; min-width: 100px; }
        button:hover { background: #1e4bd8; }
        .legend { position: absolute; left: 20px; top: 20px; z-index: 2; font-size: 14px; pointer-events: none; background: rgba(30, 34, 45, 0.9); padding: 12px; border-radius: 6px; border: 1px solid #363c4e; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        .l-ask { color: #26a69a; font-weight: bold; margin-bottom: 5px; }
        .l-bid { color: #ef5350; font-weight: bold; }
        .status { color: #848e9c; font-size: 12px; margin-top: 5px; padding-left: 5px; }
        h5 { margin: 0; color: #848e9c; font-size: 12px; text-transform: uppercase; }
    </style>
</head>
<body>
    <div class="controls">
        <input type="text" id="token" value="BTC" style="width: 70px; text-transform: uppercase;">
        <h5>Buy:</h5>
        <select id="ex1" style="background: rgba(0, 128, 0, 0.4);">
            <option value="binance">Binance</option>
            <option value="bybit">Bybit</option>
            <option value="okx">OKX</option>
            <option value="gateio">Gate.io</option>
            <option value="whitebit">WhiteBIT</option>
            <option value="kucoin">KuCoin</option>
            <option value="mexc">MEXC</option>
            <option value="bitget">Bitget</option>
            <option value="bingx">BingX</option>
            <option value="hyperliquid">Hyperliquid</option>
        </select>
        <h5>Sell:</h5>
        <select id="ex2" style="background: rgba(155, 19, 19, 0.4);">
            <option value="bybit">Bybit</option>
            <option value="binance">Binance</option>
            <option value="okx">OKX</option>
            <option value="gateio">Gate.io</option>
            <option value="whitebit">WhiteBIT</option>
            <option value="kucoin">KuCoin</option>
            <option value="mexc">MEXC</option>
            <option value="bitget">Bitget</option>
            <option value="bingx">BingX</option>
        </select>
        <select id="tf">
            <option value="1m">1m Hist</option>
            <option value="5m">5m Hist</option>
            <option value="15m">15m Hist</option>
            <option value="1h">1h Hist</option>
        </select>
        <button onclick="startMonitoring()">СТАРТ</button>
    </div>

    <div id="chart">
        <div class="legend" id="legend">
            <div class="l-ask">Ask/Bid (Long/Short): <span id="val_ask">--</span></div>
            <div class="l-bid">Bid/Ask (Short/Long): <span id="val_bid">--</span></div>
        </div>
    </div>
    <div class="status" id="status">Консоль дебагу активована. Чекаю на старт...</div>

    <script>
        let chart, askSeries, bidSeries, historySeries;
        let lastTime = 0;

        function initChart() {
            const container = document.getElementById('chart');
            chart = LightweightCharts.createChart(container, { 
                layout: { background: { color: '#131722' }, textColor: '#d1d4dc' },
                grid: { vertLines: { color: '#2b2b43' }, horzLines: { color: '#2b2b43' } },
                timeScale: { timeVisible: true, secondsVisible: true, borderVisible: false },
                rightPriceScale: { 
                    borderVisible: false, 
                    autoScale: true,
                    scaleMargins: { top: 0.1, bottom: 0.1 },
                    ticksVisible: true, // Додає мітки на шкалу
                },
                crosshair: { mode: LightweightCharts.CrosshairMode.Normal }
            });

            historySeries = chart.addLineSeries({ 
                color: '#804a00', 
                lineWidth: 2, 
                lineStyle: 2,
                title: 'History',
                priceFormat: { type: 'price', precision: 6, minMove: 0.00001 }
            });
            
            const seriesOptions = {
                priceFormat: {
                    type: 'price',
                    precision: 6,
                    minMove: 0.00001, // Робимо крок ще меншим для деталізації
                }
            };

            askSeries = chart.addLineSeries({ 
                color: '#26a69a', 
                lineWidth: 2,
                priceFormat: {
                    type: 'price',
                    precision: 6,      // Кількість знаків після коми
                    minMove: 0.0001,   // Мінімальний крок ціни (сітки)
                },
            });
            
            bidSeries = chart.addLineSeries({ 
                color: '#ef5350', 
                lineWidth: 2,
                priceFormat: {
                    type: 'price',
                    precision: 6,
                    minMove: 0.0001,
                },
            });

            askSeries.createPriceLine({ price: 1.0, color: '#f0b90b', lineWidth: 1, lineStyle: 2, title: 'PARITY' });

            window.addEventListener('resize', () => chart.resize(container.offsetWidth, container.offsetHeight));
        }

        async function startMonitoring() {
            const token = document.getElementById('token').value.toUpperCase();
            const ex1 = document.getElementById('ex1').value;
            const ex2 = document.getElementById('ex2').value;
            const tf = document.getElementById('tf').value;

            if (window.updateInterval) clearInterval(window.updateInterval);

            historySeries.setData([]);
            askSeries.setData([]);
            bidSeries.setData([]);
            lastTime = 0;

            document.getElementById('status').innerText = `Завантаження історії ${token}...`;

            try {
                const history = await pywebview.api.get_initial_history(token, ex1, ex2, tf);
                if (history && history.length > 0) {
                    historySeries.setData(history);
                    lastTime = history[history.length - 1].time;
                    chart.timeScale().fitContent();
                }

                document.getElementById('status').innerText = `Live: ${ex1} / ${ex2} (1s)`;

                window.updateInterval = setInterval(async () => {
                    const tick = await pywebview.api.get_dual_tick(token, ex1, ex2);
                    if (tick && tick.ask_ratio) {
                        const now = Math.floor(Date.now() / 1000);
                        const tickTime = now > lastTime ? now : lastTime + 1;

                        askSeries.update({ time: tickTime, value: tick.ask_ratio });
                        bidSeries.update({ time: tickTime, value: tick.bid_ratio });

                        document.getElementById('val_ask').innerText = tick.ask_ratio.toFixed(6);
                        document.getElementById('val_bid').innerText = tick.bid_ratio.toFixed(6);

                        lastTime = tickTime;
                    }
                }, 500); 
            } catch (e) {
                document.getElementById('status').innerText = "Помилка: " + e;
                console.error(e);
            }
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
            logging.info(f"⚙️ Ініціалізація {exchange_id}...")
            # CCXT підтримує kucoin для обох типів, але для ф'ючерсів іноді потрібні опції
            exch_class = getattr(ccxt, exchange_id)
            self.exchanges[exchange_id] = exch_class({'enableRateLimit': True})
        return self.exchanges[exchange_id]

    async def _find_symbol_old(self, exchange, token):
        key = f"{exchange.id}_{token}"
        if key in self.symbols_cache: return self.symbols_cache[key]

        if not exchange.markets: await exchange.load_markets()

        token = token.upper()
        # Пошук USDT/USDC пар
        for s, m in exchange.markets.items():
            if m['base'] == token and m['quote'] in ['USDT', 'USDC']:
                logging.info(f"✅ Знайдено символ на {exchange.id}: {s}")
                self.symbols_cache[key] = s
                return s
        return f"{token}/USDT"

    async def _find_symbol(self, exchange, token):
        key = f"{exchange.id}_{token}_perp"
        if key in self.symbols_cache: return self.symbols_cache[key]

        if not exchange.markets: await exchange.load_markets()

        token = token.upper()
        # 1. Шукаємо Безстрокові Ф'ючерси (Swap)
        for s, m in exchange.markets.items():
            if m.get('base') == token and m.get('quote') in ['USDT', 'USDC']:
                if m.get('swap', False) or m.get('type') == 'swap':  # Перевірка на ф'ючерс
                    logging.info(f"🔥 Знайдено Ф'ЮЧЕРС на {exchange.id}: {s}")
                    self.symbols_cache[key] = s
                    return s

        # 2. Якщо ф'юча немає, шукаємо спот (як запасний варіант)
        for s, m in exchange.markets.items():
            if m.get('base') == token and m.get('quote') in ['USDT', 'USDC']:
                logging.warning(f"⚠️ Ф'ючерс не знайдено, беру СПОТ на {exchange.id}: {s}")
                self.symbols_cache[key] = s
                return s

        return f"{token}/USDT"

    def get_initial_history(self, token, ex1_id, ex2_id, tf):
        async def _fetch():
            try:
                e1, e2 = await asyncio.gather(self.get_exchange(ex1_id), self.get_exchange(ex2_id))
                s1, s2 = await asyncio.gather(self._find_symbol(e1, token), self._find_symbol(e2, token))

                logging.info(f"📊 Запит історії {tf} для {s1} та {s2}")
                ohlcv1, ohlcv2 = await asyncio.gather(
                    e1.fetch_ohlcv(s1, tf, limit=100),
                    e2.fetch_ohlcv(s2, tf, limit=100)
                )

                df1 = pd.DataFrame(ohlcv1, columns=['time', 'o', 'h', 'l', 'c', 'v'])
                df2 = pd.DataFrame(ohlcv2, columns=['time', 'o', 'h', 'l', 'c', 'v'])
                df = pd.merge(df1, df2, on='time')

                df['value'] = df['c_x'] / df['c_y']
                df['time'] = df['time'] / 1000
                return df[['time', 'value']].to_dict('records')
            except Exception as e:
                logging.error(f"❌ Помилка історії: {e}")
                return []

        return asyncio.run_coroutine_threadsafe(_fetch(), self.loop).result()

    def get_dual_tick(self, token, ex1_id, ex2_id):
        async def _fetch():
            try:
                e1, e2 = await asyncio.gather(self.get_exchange(ex1_id), self.get_exchange(ex2_id))
                s1, s2 = await asyncio.gather(self._find_symbol(e1, token), self._find_symbol(e2, token))

                t1, t2 = await asyncio.gather(
                    e1.fetch_ticker(s1),
                    e2.fetch_ticker(s2)
                )
                logging.info(f"t1_ask: {t1['ask']} // t1_bid: {t1['bid']} // t2_ask: {t2['ask']} // t2_bid: {t2['bid']}")

                t1_ask = float(t1['ask'])
                t2_ask = float(t2['ask'])
                t1_bid = float(t1['bid'])
                t2_bid = float(t2['bid'])

                # Ratio: Ask1/Bid2 (Купівля на 1, продаж на 2)
                ask_ratio = t1_ask / t2_bid if t2_bid else 0
                # Ratio: Bid1/Ask2 (Продаж на 1, купівля на 2)
                bid_ratio = t1_bid / t2_ask if t2_ask else 0

                logging.info(f"🔄 Tick {token}: AskRatio={ask_ratio:.6f}, BidRatio={bid_ratio:.6f}")
                return {'ask_ratio': ask_ratio, 'bid_ratio': bid_ratio}
            except Exception as e:
                logging.error(f"❌ Помилка тіка: {e}")
                return None

        return asyncio.run_coroutine_threadsafe(_fetch(), self.loop).result()


if __name__ == "__main__":
    api = API()
    window = webview.create_window(
        'Crypto Arbitrage Pro Scanner',
        html=HTML_CODE,
        js_api=api,
        width=1200,
        height=800,
        background_color='#131722'
    )
    # ТУТ ВІН, НІКУДИ БІЛЬШЕ НЕ ДІНЕТЬСЯ :)
    webview.start(debug=True)