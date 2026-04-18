import json
import time
from core.config import MARKETS_CACHE_DIR, CACHE_TTL_HOURS


def cache_path(exchange_id: str):
    return MARKETS_CACHE_DIR / f"{exchange_id}.json"


def load_cache(exchange_id: str):
    path = cache_path(exchange_id)
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


def save_cache(exchange_id: str, markets: list):
    path = cache_path(exchange_id)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'updated_at': time.time(), 'markets': markets}, f, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️  Помилка збереження кешу: {e}")
