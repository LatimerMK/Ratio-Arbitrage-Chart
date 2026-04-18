import webview
import asyncio
import ccxt.async_support as ccxt
import pandas as pd
import time
import json
import os
from pathlib import Path

MARKETS_CACHE_DIR = Path("markets_cache")
MARKETS_CACHE_DIR.mkdir(exist_ok=True)
CACHE_TTL_HOURS = 24

HTML_CODE = """
<!DOCTYPE html>
<html>
<head>
    <script src="https://unpkg.com/lightweight-charts@3.8.0/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Space+Grotesk:wght@300;400;500;600&display=swap');

        :root {
            --bg: #0d0f14;
            --bg2: #13151c;
            --bg3: #1a1d27;
            --bg4: #222636;
            --border: #2a2e3f;
            --border2: #353a52;
            --text: #c8cdd8;
            --text2: #6b7280;
            --text3: #9ca3af;
            --accent: #3b82f6;
            --accent2: #60a5fa;
            --green: #10b981;
            --red: #ef4444;
            --yellow: #f59e0b;
            --purple: #8b5cf6;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        html, body {
            height: 100%;
            background: var(--bg);
            color: var(--text);
            font-family: 'Space Grotesk', sans-serif;
            overflow: hidden;
        }

        body {
            display: flex;
            flex-direction: column;
            height: 100vh;
        }

        /* ── TOP BAR ── */
        #topbar {
            display: flex;
            align-items: stretch;
            gap: 0;
            background: var(--bg2);
            border-bottom: 1px solid var(--border);
            padding: 8px 12px;
            flex-shrink: 0;
            gap: 8px;
            flex-wrap: wrap;
        }

        .side-block {
            display: flex;
            align-items: center;
            gap: 6px;
            background: var(--bg3);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 6px 10px;
            flex: 1;
            min-width: 300px;
        }

        .side-label {
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            padding: 3px 7px;
            border-radius: 4px;
            flex-shrink: 0;
        }

        .side-label.buy  { background: rgba(16,185,129,0.15); color: var(--green); border: 1px solid rgba(16,185,129,0.3); }
        .side-label.sell { background: rgba(239,68,68,0.15);  color: var(--red);   border: 1px solid rgba(239,68,68,0.3); }

        .ctrl-select {
            background: var(--bg4);
            border: 1px solid var(--border2);
            color: var(--text);
            border-radius: 6px;
            padding: 5px 8px;
            font-family: 'Space Grotesk', sans-serif;
            font-size: 12px;
            outline: none;
            cursor: pointer;
            transition: border-color .2s;
        }
        .ctrl-select:hover, .ctrl-select:focus { border-color: var(--accent); }

        .market-search-wrap {
            position: relative;
            flex: 1;
            min-width: 140px;
        }

        .market-search {
            width: 100%;
            background: var(--bg4);
            border: 1px solid var(--border2);
            color: var(--text);
            border-radius: 6px;
            padding: 5px 8px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            outline: none;
            transition: border-color .2s;
        }
        .market-search:hover, .market-search:focus { border-color: var(--accent); }
        .market-search::placeholder { color: var(--text2); }

        .market-dropdown {
            display: none;
            position: absolute;
            top: calc(100% + 4px);
            left: 0;
            right: 0;
            background: var(--bg3);
            border: 1px solid var(--border2);
            border-radius: 8px;
            max-height: 280px;
            overflow-y: auto;
            z-index: 1000;
            box-shadow: 0 8px 32px rgba(0,0,0,.6);
        }
        .market-dropdown.open { display: block; }

        .market-dropdown::-webkit-scrollbar { width: 4px; }
        .market-dropdown::-webkit-scrollbar-track { background: transparent; }
        .market-dropdown::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 2px; }

        .market-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 7px 10px;
            cursor: pointer;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            border-bottom: 1px solid rgba(255,255,255,.03);
            transition: background .1s;
        }
        .market-item:hover { background: var(--bg4); }
        .market-item.selected { background: rgba(59,130,246,.15); }

        .market-item-symbol { color: var(--text); }

        .market-type-badge {
            font-size: 9px;
            font-weight: 700;
            padding: 2px 5px;
            border-radius: 3px;
            letter-spacing: .06em;
            flex-shrink: 0;
        }
        .badge-spot   { background: rgba(16,185,129,.2); color: var(--green); }
        .badge-swap   { background: rgba(59,130,246,.2); color: var(--accent2); }
        .badge-future { background: rgba(245,158,11,.2); color: var(--yellow); }
        .badge-option { background: rgba(139,92,246,.2); color: var(--purple); }

        .market-no-results {
            padding: 12px;
            text-align: center;
            color: var(--text2);
            font-size: 11px;
        }

        .refresh-btn {
            background: none;
            border: 1px solid var(--border2);
            color: var(--text2);
            border-radius: 6px;
            width: 28px;
            height: 28px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
            transition: all .2s;
            flex-shrink: 0;
        }
        .refresh-btn:hover { border-color: var(--accent); color: var(--accent); }
        .refresh-btn.spinning { animation: spin .8s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }

        .divider {
            width: 1px;
            background: var(--border);
            align-self: stretch;
            flex-shrink: 0;
            margin: 0 4px;
        }

        /* TF + GO */
        .right-controls {
            display: flex;
            align-items: center;
            gap: 6px;
            flex-shrink: 0;
        }

        .go-btn {
            background: var(--accent);
            border: none;
            color: white;
            border-radius: 6px;
            padding: 6px 14px;
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 600;
            font-size: 12px;
            cursor: pointer;
            transition: background .2s, transform .1s;
            letter-spacing: .04em;
        }
        .go-btn:hover  { background: var(--accent2); }
        .go-btn:active { transform: scale(.97); }
        .go-btn:disabled { background: var(--bg4); color: var(--text2); cursor: not-allowed; }

        /* ── CHART AREA ── */
        #chart-wrap {
            flex: 1;
            position: relative;
            overflow: hidden;
            min-height: 0;
        }

        #chart {
            width: 100%;
            height: 100%;
        }

        /* ── LEGEND ── */
        #legend {
            position: absolute;
            top: 10px;
            left: 12px;
            z-index: 10;
            pointer-events: none;
        }

        .legend-ratio {
            font-family: 'JetBrains Mono', monospace;
            font-size: 22px;
            font-weight: 700;
            color: var(--accent2);
            text-shadow: 0 0 20px rgba(96,165,250,.4);
        }

        .legend-pair {
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            color: var(--text2);
            margin-top: 2px;
            letter-spacing: .05em;
        }

        /* ── STATUS BAR ── */
        #statusbar {
            display: flex;
            align-items: center;
            gap: 10px;
            background: var(--bg2);
            border-top: 1px solid var(--border);
            padding: 5px 12px;
            flex-shrink: 0;
        }

        .status-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: var(--text2);
            flex-shrink: 0;
            transition: background .3s;
        }
        .status-dot.live { background: var(--green); box-shadow: 0 0 6px var(--green); animation: pulse 2s infinite; }
        .status-dot.loading { background: var(--yellow); animation: pulse 1s infinite; }
        .status-dot.error { background: var(--red); }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }

        #status-text {
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            color: var(--text2);
            flex: 1;
        }

        .candle-count {
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            color: var(--text2);
        }

        /* ── LOADING OVERLAY ── */
        #loading-overlay {
            display: none;
            position: absolute;
            inset: 0;
            background: rgba(13,15,20,.7);
            backdrop-filter: blur(4px);
            z-index: 20;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            gap: 12px;
        }
        #loading-overlay.visible { display: flex; }

        .spinner {
            width: 36px;
            height: 36px;
            border: 3px solid var(--border2);
            border-top-color: var(--accent);
            border-radius: 50%;
            animation: spin .7s linear infinite;
        }

        .loading-text {
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            color: var(--text2);
        }

        /* ── TOAST ── */
        #toast {
            position: fixed;
            bottom: 40px;
            left: 50%;
            transform: translateX(-50%) translateY(10px);
            background: var(--bg3);
            border: 1px solid var(--border2);
            color: var(--text);
            padding: 8px 16px;
            border-radius: 8px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            z-index: 100;
            opacity: 0;
            transition: opacity .3s, transform .3s;
            pointer-events: none;
        }
        #toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }

        /* scrollbar for dropdowns */
        select option { background: var(--bg3); }
    </style>
</head>
<body>

<div id="topbar">
    <!-- SIDE 1 (BUY) -->
    <div class="side-block" id="block1">
        <span class="side-label buy">BUY</span>

        <select class="ctrl-select" id="ex1" onchange="onExchangeChange(1)">
            <option value="binance">Binance</option>
            <option value="bybit">Bybit</option>
            <option value="okx">OKX</option>
            <option value="gateio">Gate.io</option>
            <option value="whitebit">WhiteBIT</option>
            <option value="kucoinfutures">KuCoin Futures</option>
            <option value="mexc">MEXC</option>
            <option value="bitget">Bitget</option>
            <option value="bingx">BingX</option>
            <option value="hyperliquid">Hyperliquid</option>
            <option value="paradex">Paradex</option>
            <option value="htx">HTX</option>
            <option value="kraken">Kraken</option>
            <option value="kucoin">KuCoin</option>
            <option value="deribit">Deribit</option>
            <option value="bitmex">BitMEX</option>
            <option value="phemex">Phemex</option>
            <option value="coinbase">Coinbase</option>
        </select>

        <button class="refresh-btn" id="refresh1" onclick="refreshMarkets(1)" title="Оновити ринки">↻</button>

        <div class="market-search-wrap">
            <input class="market-search" id="search1" placeholder="Пошук ринку…" 
                   oninput="filterMarkets(1)" onfocus="openDropdown(1)" autocomplete="off">
            <div class="market-dropdown" id="dropdown1"></div>
        </div>
    </div>

    <div class="divider"></div>

    <!-- SIDE 2 (SELL) -->
    <div class="side-block" id="block2">
        <span class="side-label sell">SELL</span>

        <select class="ctrl-select" id="ex2" onchange="onExchangeChange(2)">
            <option value="binance">Binance</option>
            <option value="bybit">Bybit</option>
            <option value="okx">OKX</option>
            <option value="gateio">Gate.io</option>
            <option value="whitebit">WhiteBIT</option>
            <option value="kucoinfutures">KuCoin Futures</option>
            <option value="mexc">MEXC</option>
            <option value="bitget">Bitget</option>
            <option value="bingx">BingX</option>
            <option value="hyperliquid">Hyperliquid</option>
            <option value="paradex">Paradex</option>
            <option value="htx">HTX</option>
            <option value="kraken">Kraken</option>
            <option value="kucoin">KuCoin</option>
            <option value="deribit">Deribit</option>
            <option value="bitmex">BitMEX</option>
            <option value="phemex">Phemex</option>
            <option value="coinbase">Coinbase</option>
        </select>

        <button class="refresh-btn" id="refresh2" onclick="refreshMarkets(2)" title="Оновити ринки">↻</button>

        <div class="market-search-wrap">
            <input class="market-search" id="search2" placeholder="Пошук ринку…"
                   oninput="filterMarkets(2)" onfocus="openDropdown(2)" autocomplete="off">
            <div class="market-dropdown" id="dropdown2"></div>
        </div>
    </div>

    <div class="divider"></div>

    <!-- RIGHT CONTROLS -->
    <div class="right-controls">
        <select class="ctrl-select" id="tf">
            <option value="1m">1m</option>
            <option value="5m">5m</option>
            <option value="15m">15m</option>
            <option value="1h" selected>1h</option>
            <option value="4h">4h</option>
            <option value="1d">1d</option>
        </select>
        <button class="go-btn" id="goBtn" onclick="startChart()">▶ GO</button>
    </div>
</div>

<div id="chart-wrap">
    <div id="chart"></div>
    <div id="legend">
        <div class="legend-ratio" id="legend-ratio">—</div>
        <div class="legend-pair" id="legend-pair">Оберіть ринки та натисніть GO</div>
    </div>
    <div id="loading-overlay">
        <div class="spinner"></div>
        <div class="loading-text" id="loading-text">Завантаження…</div>
    </div>
</div>

<div id="statusbar">
    <div class="status-dot" id="status-dot"></div>
    <div id="status-text">Готово</div>
    <div class="candle-count" id="candle-count"></div>
</div>

<div id="toast"></div>

<script>
// ─── STATE ───────────────────────────────────────────────────────────
let chart, candleSeries;
let allMarkets = { 1: [], 2: [] };
let selectedSymbol = { 1: null, 2: null };
let loadedCandles = [];          // всі завантажені свічки (відсортовані за часом)
let isLoadingMore = false;
let noMoreData = false;
let updateInterval = null;
let currentParams = null;

// ─── KEYBOARD LAYOUT FIX ─────────────────────────────────────────────
const UA_EN = {'й':'q','ц':'w','у':'e','к':'r','е':'t','н':'y','г':'u','ш':'i','щ':'o','з':'p',
    'ф':'a','и':'b','с':'c','в':'d','а':'f','п':'g','р':'h','і':'s','л':'k','д':'l',
    'я':'z','ч':'x','м':'v','т':'n','ь':'m','б':',','ю':'.'};

function fixLayout(str) {
    return str.toLowerCase().split('').map(c => UA_EN[c] || c).join('').toUpperCase().replace(/[^A-Z0-9/:\.@-]/g,'');
}

// ─── MARKET HELPERS ──────────────────────────────────────────────────
function getTypeBadge(m) {
    if (m.type === 'spot')   return '<span class="market-type-badge badge-spot">SPOT</span>';
    if (m.type === 'swap')   return '<span class="market-type-badge badge-swap">PERP</span>';
    if (m.type === 'future') return '<span class="market-type-badge badge-future">FUTURE</span>';
    if (m.type === 'option') return '<span class="market-type-badge badge-option">OPT</span>';
    return `<span class="market-type-badge badge-spot">${(m.type||'').toUpperCase()}</span>`;
}

function renderDropdown(side) {
    const query = fixLayout(document.getElementById(`search${side}`).value);
    const dd = document.getElementById(`dropdown${side}`);
    const markets = allMarkets[side];

    const filtered = query.length >= 1
        ? markets.filter(m => m.symbol.toUpperCase().includes(query))
        : markets.slice(0, 80);

    if (filtered.length === 0) {
        dd.innerHTML = `<div class="market-no-results">Нічого не знайдено для "${query}"</div>`;
        return;
    }

    dd.innerHTML = filtered.slice(0, 120).map(m => `
        <div class="market-item ${selectedSymbol[side] === m.symbol ? 'selected' : ''}"
             onclick="selectMarket(${side}, '${m.symbol.replace(/'/g,"\\'")}', '${m.type}')">
            <span class="market-item-symbol">${m.symbol}</span>
            ${getTypeBadge(m)}
        </div>
    `).join('');
}

function openDropdown(side) {
    document.getElementById(`dropdown${side}`).classList.add('open');
    renderDropdown(side);
}

function closeDropdown(side) {
    document.getElementById(`dropdown${side}`).classList.remove('open');
}

function filterMarkets(side) {
    const val = document.getElementById(`search${side}`).value;
    document.getElementById(`search${side}`).value = fixLayout(val);
    openDropdown(side);
    renderDropdown(side);
}

function selectMarket(side, symbol, type) {
    selectedSymbol[side] = symbol;
    document.getElementById(`search${side}`).value = symbol;
    closeDropdown(side);
    showToast(`${side === 1 ? 'BUY' : 'SELL'}: ${symbol}`);
}

// Close dropdowns on outside click
document.addEventListener('click', e => {
    [1,2].forEach(side => {
        const wrap = document.querySelector(`#block${side} .market-search-wrap`);
        if (wrap && !wrap.contains(e.target)) closeDropdown(side);
    });
});

// ─── LOAD MARKETS ────────────────────────────────────────────────────
async function loadMarkets(side, forceRefresh = false) {
    const exId = document.getElementById(`ex${side}`).value;
    const btn = document.getElementById(`refresh${side}`);
    const search = document.getElementById(`search${side}`);

    btn.classList.add('spinning');
    search.placeholder = 'Завантаження…';

    try {
        const markets = await pywebview.api.get_markets(exId, forceRefresh);
        allMarkets[side] = markets || [];
        search.placeholder = `Пошук у ${allMarkets[side].length} ринках…`;
        showToast(`${exId}: завантажено ${allMarkets[side].length} ринків`);
    } catch(e) {
        search.placeholder = 'Помилка завантаження';
        showToast('Помилка завантаження ринків');
    } finally {
        btn.classList.remove('spinning');
    }
}

function onExchangeChange(side) {
    selectedSymbol[side] = null;
    allMarkets[side] = [];
    document.getElementById(`search${side}`).value = '';
    document.getElementById(`search${side}`).placeholder = 'Пошук ринку…';
    loadMarkets(side, false);
}

function refreshMarkets(side) {
    loadMarkets(side, true);
}

// ─── CHART INIT ──────────────────────────────────────────────────────
function initChart() {
    const container = document.getElementById('chart');
    chart = LightweightCharts.createChart(container, {
        layout: { backgroundColor: '#0d0f14', textColor: '#6b7280' },
        crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
        grid: { vertLines: { color: '#1a1d27' }, horzLines: { color: '#1a1d27' } },
        timeScale: { timeVisible: true, borderColor: '#2a2e3f' },
        rightPriceScale: {
            borderColor: '#2a2e3f',
            scaleMargins: { top: 0.1, bottom: 0.1 },
            entireTextOnly: false,
            ticksVisible: true,
        },
    });

    candleSeries = chart.addCandlestickSeries({
        upColor: '#10b981', downColor: '#ef4444',
        borderVisible: false,
        wickUpColor: '#10b981', wickDownColor: '#ef4444'
    });
    





    candleSeries.createPriceLine({
        price: 1.0, color: '#f59e0b', lineWidth: 1,
        lineStyle: 2, title: 'PARITY'
    });

    window.addEventListener('resize', () => {
        chart.resize(container.offsetWidth, container.offsetHeight);
    });

    // ── INFINITE SCROLL: підвантаження при докручуванні вліво ──
    chart.timeScale().subscribeVisibleLogicalRangeChange(async (range) => {
        if (!range || isLoadingMore || noMoreData || !currentParams) return;
        // Якщо лівий край менше 20 свічок від початку — підтягуємо
        if (range.from < 20) {
            await loadMoreCandles();
        }
    });

    // Оновлення легенди при наведенні
    chart.subscribeCrosshairMove(param => {
        if (!param || !param.seriesPrices) return;
        const price = param.seriesPrices.get(candleSeries);
        if (price) {
            document.getElementById('legend-ratio').innerText = price.close.toFixed(6);
        }
    });
}

// ─── LOAD MORE (infinite scroll) ────────────────────────────────────
async function loadMoreCandles() {
    if (isLoadingMore || noMoreData || loadedCandles.length === 0) return;
    isLoadingMore = true;

    const oldestTime = loadedCandles[0].time * 1000; // повертаємо в мс для API
    setStatus('loading', `Підвантаження свічок до ${new Date(oldestTime).toLocaleDateString()}…`);

    try {
        const { sym1, sym2, ex1, ex2, tf } = currentParams;
        const newData = await pywebview.api.load_more_candles(sym1, ex1, sym2, ex2, tf, oldestTime);

        if (!newData || newData.length === 0) {
            noMoreData = true;
            setStatus('live', 'Початок доступної історії досягнуто');
            return;
        }

        // Фільтруємо дублікати і мерджимо
        const existingTimes = new Set(loadedCandles.map(c => c.time));
        const unique = newData.filter(c => !existingTimes.has(c.time));

        if (unique.length === 0) {
            noMoreData = true;
            return;
        }

        loadedCandles = [...unique, ...loadedCandles];
        loadedCandles.sort((a,b) => a.time - b.time);
        candleSeries.setData(loadedCandles);

        updateCandleCount();
        setStatus('live', `+${unique.length} свічок | всього: ${loadedCandles.length}`);
    } catch(e) {
        console.error('loadMoreCandles error:', e);
        setStatus('error', 'Помилка підвантаження');
    } finally {
        isLoadingMore = false;
    }
}

// ─── START CHART ────────────────────────────────────────────────────
async function startChart() {
    const ex1 = document.getElementById('ex1').value;
    const ex2 = document.getElementById('ex2').value;
    const tf  = document.getElementById('tf').value;
    const sym1 = selectedSymbol[1];
    const sym2 = selectedSymbol[2];

    if (!sym1) { showToast('⚠ Оберіть ринок BUY'); return; }
    if (!sym2) { showToast('⚠ Оберіть ринок SELL'); return; }

    // Зупиняємо старий інтервал
    if (updateInterval) { clearInterval(updateInterval); updateInterval = null; }
    noMoreData = false;
    loadedCandles = [];

    currentParams = { sym1, sym2, ex1, ex2, tf };

    document.getElementById('legend-pair').innerText = `${sym1} (${ex1}) ÷ ${sym2} (${ex2})`;

    showLoading(`Завантаження ${sym1} / ${sym2}…`);
    setStatus('loading', 'Запит до бірж…');
    document.getElementById('goBtn').disabled = true;

    try {
        const data = await pywebview.api.get_initial_data(sym1, ex1, sym2, ex2, tf);

        if (!data || data.length === 0) {
            setStatus('error', 'Дані не отримано. Перевірте символи.');
            showToast('❌ Немає даних');
            return;
        }

        loadedCandles = data;
        candleSeries.setData(data);
        chart.timeScale().fitContent();

        const last = data[data.length - 1];
        document.getElementById('legend-ratio').innerText = last.close.toFixed(6);
        updateCandleCount();
        setStatus('live', `${ex1}:${sym1} ÷ ${ex2}:${sym2} | ${tf}`);

        // Авто-оновлення
        let lastTs = 0;
        updateInterval = setInterval(async () => {
            try {
                const upd = await pywebview.api.get_update(sym1, ex1, sym2, ex2, tf);
                if (upd && upd.time >= lastTs) {
                    candleSeries.update(upd);
                    lastTs = upd.time;
                    document.getElementById('legend-ratio').innerText = upd.close.toFixed(6);

                    // Оновлюємо або додаємо останню свічку в loadedCandles
                    const idx = loadedCandles.findIndex(c => c.time === upd.time);
                    if (idx >= 0) loadedCandles[idx] = upd;
                    else { loadedCandles.push(upd); updateCandleCount(); }
                }
            } catch(e) {}
        }, 1500);

    } catch(e) {
        setStatus('error', 'Помилка: ' + e);
        showToast('❌ ' + e);
    } finally {
        hideLoading();
        document.getElementById('goBtn').disabled = false;
    }
}

// ─── UI HELPERS ──────────────────────────────────────────────────────
function showLoading(text) {
    document.getElementById('loading-text').innerText = text;
    document.getElementById('loading-overlay').classList.add('visible');
}
function hideLoading() {
    document.getElementById('loading-overlay').classList.remove('visible');
}
function setStatus(type, text) {
    const dot = document.getElementById('status-dot');
    dot.className = 'status-dot' + (type ? ' ' + type : '');
    document.getElementById('status-text').innerText = text;
}
function updateCandleCount() {
    document.getElementById('candle-count').innerText = loadedCandles.length ? `${loadedCandles.length} свічок` : '';
}
function showToast(msg) {
    const t = document.getElementById('toast');
    t.innerText = msg;
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 2500);
}

// ─── INIT ────────────────────────────────────────────────────────────
window.onload = () => {
    initChart();
    // Завантажуємо ринки для обох бірж при старті
    loadMarkets(1, false);
    loadMarkets(2, false);
};
</script>
</body>
</html>
"""


class API:
    def __init__(self):
        self.exchanges = {}
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

    # ─── EXCHANGE ────────────────────────────────────────────────────
    async def _get_exchange(self, exchange_id):
        if exchange_id not in self.exchanges:
            print(f"⚙️  Ініціалізація {exchange_id}…")
            exch_class = getattr(ccxt, exchange_id)
            self.exchanges[exchange_id] = exch_class({'enableRateLimit': True})
        return self.exchanges[exchange_id]

    # ─── MARKETS CACHE ───────────────────────────────────────────────
    def _cache_path(self, exchange_id):
        return MARKETS_CACHE_DIR / f"{exchange_id}.json"

    def _load_cache(self, exchange_id):
        path = self._cache_path(exchange_id)
        if not path.exists():
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            age_h = (time.time() - data.get('updated_at', 0)) / 3600
            if age_h > CACHE_TTL_HOURS:
                return None
            return data.get('markets', [])
        except Exception:
            return None

    def _save_cache(self, exchange_id, markets):
        path = self._cache_path(exchange_id)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({'updated_at': time.time(), 'markets': markets}, f, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  Помилка збереження кешу: {e}")

    async def _fetch_markets_from_exchange(self, exchange_id):
        e = await self._get_exchange(exchange_id)
        raw = await e.load_markets(reload=True)
        result = []
        for sym, m in raw.items():
            mtype = 'spot'
            if m.get('swap') or m.get('linear') or m.get('inverse'):
                mtype = 'swap'
            elif m.get('future'):
                mtype = 'future'
            elif m.get('option'):
                mtype = 'option'
            result.append({
                'symbol': sym,
                'type': mtype,
                'base': m.get('base', ''),
                'quote': m.get('quote', ''),
            })
        # Сортування: спочатку swap/future, потім spot; за алфавітом
        order = {'swap': 0, 'future': 1, 'spot': 2, 'option': 3}
        result.sort(key=lambda x: (order.get(x['type'], 9), x['symbol']))
        return result

    def get_markets(self, exchange_id, force_refresh=False):
        return self._run_async(self._get_markets_async(exchange_id, force_refresh))

    async def _get_markets_async(self, exchange_id, force_refresh=False):
        try:
            if not force_refresh:
                cached = self._load_cache(exchange_id)
                if cached is not None:
                    print(f"📦 Кеш для {exchange_id}: {len(cached)} ринків")
                    return cached

            print(f"🌐 Завантаження ринків з {exchange_id}…")
            markets = await self._fetch_markets_from_exchange(exchange_id)
            self._save_cache(exchange_id, markets)
            print(f"✅ {exchange_id}: {len(markets)} ринків збережено")
            return markets
        except Exception as e:
            print(f"⚠️  get_markets {exchange_id}: {e}")
            return []

    # ─── EXCHANGE MAX LIMIT ──────────────────────────────────────────
    def _get_max_limit(self, exchange_id):
        """Максимальні ліміти для популярних бірж"""
        limits = {
            'binance': 1000, 'bybit': 1000, 'okx': 300,
            'gateio': 1000, 'whitebit': 1000, 'kucoinfutures': 200,
            'mexc': 1000, 'bitget': 1000, 'bingx': 1000,
            'hyperliquid': 500, 'paradex': 100, 'htx': 2000,
            'kraken': 720, 'kucoin': 1500, 'deribit': 1000,
            'bitmex': 750, 'phemex': 1000, 'coinbase': 300,
        }
        return limits.get(exchange_id, 500)

    # ─── FETCH RATIO DATA ────────────────────────────────────────────
    async def _fetch_ratio(self, sym1, ex1_id, sym2, ex2_id, tf, limit=None, since=None):
        """
        Завантажує OHLCV для обох символів і повертає список свічок-спреду.
        since  — мітка часу в мілісекундах (для підвантаження старої історії)
        limit  — якщо None, береться максимум для повільнішої з бірж
        """
        try:
            e1 = await self._get_exchange(ex1_id)
            e2 = await self._get_exchange(ex2_id)

            if limit is None:
                limit = min(
                    self._get_max_limit(ex1_id),
                    self._get_max_limit(ex2_id)
                )

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

            df1 = pd.DataFrame(ohlcv1, columns=['time','open','high','low','close','vol'])
            df2 = pd.DataFrame(ohlcv2, columns=['time','open','high','low','close','vol'])

            df = pd.merge(df1, df2, on='time', how='inner', suffixes=('_1','_2'))
            if df.empty:
                df = pd.merge(df1, df2, on='time', how='outer', suffixes=('_1','_2')).sort_values('time')
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

            return df[['time','open','high','low','close']].to_dict('records')

        except Exception as e:
            print(f"⚠️  _fetch_ratio: {e}")
            return None

    # ─── PUBLIC API ──────────────────────────────────────────────────
    def get_initial_data(self, sym1, ex1, sym2, ex2, tf):
        return self._run_async(self._fetch_ratio(sym1, ex1, sym2, ex2, tf))

    def get_update(self, sym1, ex1, sym2, ex2, tf):
        data = self._run_async(self._fetch_ratio(sym1, ex1, sym2, ex2, tf, limit=10))
        return data[-1] if data else None

    def load_more_candles(self, sym1, ex1, sym2, ex2, tf, before_ms):
        """
        Підвантажує свічки ДО мітки before_ms.
        Повертає список свічок старіших за before_ms.
        """
        limit1 = self._get_max_limit(ex1)
        limit2 = self._get_max_limit(ex2)
        limit  = min(limit1, limit2)

        tf_ms = {
            '1m': 60_000, '3m': 180_000, '5m': 300_000,
            '15m': 900_000, '30m': 1_800_000,
            '1h': 3_600_000, '2h': 7_200_000, '4h': 14_400_000,
            '6h': 21_600_000, '12h': 43_200_000,
            '1d': 86_400_000, '1w': 604_800_000,
        }.get(tf, 3_600_000)

        since = int(before_ms) - limit * tf_ms

        async def _load():
            data = await self._fetch_ratio(sym1, ex1, sym2, ex2, tf, limit=limit, since=since)
            if not data:
                return []
            # Повертаємо тільки свічки ДО before_ms (в секундах)
            cutoff = before_ms / 1000
            return [c for c in data if c['time'] < cutoff]

        return self._run_async(_load())

    def on_close(self):
        async def _close_all():
            for ex in self.exchanges.values():
                await ex.close()
            self.loop.stop()
        if self.loop.is_running():
            asyncio.run_coroutine_threadsafe(_close_all(), self.loop)


if __name__ == "__main__":
    api = API()
    window = webview.create_window(
        'Spread Scanner v5',
        html=HTML_CODE,
        js_api=api,
        width=1280,
        height=750,
        background_color='#0d0f14'
    )
    webview.start(debug=True)