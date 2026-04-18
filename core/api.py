import asyncio
import threading
from core.exchange_manager import ExchangeManager


class API:
    """
    pywebview JS bridge.
    All public methods are called from the frontend via pywebview.api.*
    """

    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._em = ExchangeManager(self.loop)

    # ── Event loop ────────────────────────────────────────────────────
    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def _run_async(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result()

    # ── Public API ────────────────────────────────────────────────────
    def get_markets(self, exchange_id: str, force_refresh: bool = False) -> list:
        return self._run_async(self._em.get_markets(exchange_id, force_refresh))

    def get_initial_data(self, sym1, ex1, sym2, ex2, tf) -> list | None:
        return self._run_async(self._em.fetch_ratio(sym1, ex1, sym2, ex2, tf))

    def get_update(self, sym1, ex1, sym2, ex2, tf) -> dict | None:
        data = self._run_async(self._em.fetch_ratio(sym1, ex1, sym2, ex2, tf, limit=10))
        return data[-1] if data else None

    def load_more_candles(self, sym1, ex1, sym2, ex2, tf, before_ms) -> list:
        return self._em.load_more_candles(sym1, ex1, sym2, ex2, tf, before_ms)

    # ── Cleanup ───────────────────────────────────────────────────────
    def on_close(self):
        async def _close_all():
            await self._em.close_all()
            self.loop.stop()

        if self.loop.is_running():
            asyncio.run_coroutine_threadsafe(_close_all(), self.loop)
