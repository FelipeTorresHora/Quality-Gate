from collections.abc import Sequence
from functools import lru_cache
from typing import Any

from app.core.config import get_settings

CACHE_NAMESPACE = "quality-gate"


def get_json(key: str) -> Any | None:
    cache = _get_cache()
    if cache is None:
        return None
    try:
        value = cache.get(key)
    except Exception:
        return None
    return value


def set_json(
    key: str,
    value: Any,
    *,
    ttl: int,
    tags: Sequence[str],
) -> None:
    cache = _get_cache()
    if cache is None:
        return
    try:
        cache.set(key, value, {"ttl": ttl, "tags": list(tags)})
    except Exception:
        return


def expire_tags(tags: Sequence[str]) -> None:
    cache = _get_cache()
    if cache is None:
        return
    try:
        cache.expire_tag(list(tags))
    except Exception:
        return


@lru_cache
def _get_cache():
    if not get_settings().runtime_cache_enabled:
        return None
    try:
        from vercel.functions import RuntimeCache
    except Exception:
        return None
    try:
        return RuntimeCache(namespace=CACHE_NAMESPACE)
    except Exception:
        return None
