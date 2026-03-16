from __future__ import annotations

import functools
import time
import typing as t

_HASHABLE = (str, int, float, bool, bytes)

F = t.TypeVar("F", bound=t.Callable[..., t.Any])


class CacheStore:
    """Simple TTL + LRU cache store."""

    def __init__(self, ttl: t.Union[int, float], maxsize: int = 1024) -> None:
        self.ttl = ttl
        self.maxsize = maxsize
        self._data: t.Dict[str, t.Tuple[t.Any, float]] = {}

    def get(self, key: str) -> t.Tuple[bool, t.Any]:
        """Lookup key. Returns (hit, value).

        :param key: Cache key.
        :return: Tuple of (hit, value). If missed, value is None.
        """
        entry = self._data.get(key)
        if entry is None:
            return False, None
        value, expiry = entry
        if self.ttl > 0 and time.monotonic() > expiry:
            del self._data[key]
            return False, None
        return True, value

    def set(self, key: str, value: t.Any) -> None:
        """Store value under key.

        :param key: Cache key.
        :param value: Value to cache.
        """
        if len(self._data) >= self.maxsize:
            self._evict()
        expiry = time.monotonic() + self.ttl if self.ttl > 0 else float("inf")
        self._data[key] = (value, expiry)

    def clear(self) -> None:
        """Remove all entries."""
        self._data.clear()

    @staticmethod
    def build_key(name: str, args: tuple, kwargs: dict) -> str:  # type: ignore[type-arg]
        """Build cache key from function name and hashable arguments.

        :param name: Function name.
        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :return: Cache key string.
        """
        parts: t.List[str] = [name]
        for a in args:
            if isinstance(a, _HASHABLE):
                parts.append(str(a))
        for k in sorted(kwargs):
            v = kwargs[k]
            if isinstance(v, _HASHABLE):
                parts.append(f"{k}={v!r}")
        return ":".join(parts)

    def _evict(self) -> None:
        """Remove oldest entry (by insertion order)."""
        if self._data:
            oldest_key = next(iter(self._data))
            del self._data[oldest_key]


class CachedFunction(t.Protocol):
    """Protocol for functions decorated with async_ttl_cache."""

    cache: CacheStore
    cache_clear: t.Callable[[], None]

    def __call__(self, *args: t.Any, **kwargs: t.Any) -> t.Any: ...


def async_ttl_cache(ttl: t.Union[int, float]) -> t.Callable[[F], F]:
    """Decorator factory for async functions with TTL caching.

    Builds cache key from hashable args (str, int, float, bool, bytes).
    Skips complex objects (app_ctx, client, etc.).

    The returned function has ``.cache`` (CacheStore) and
    ``.cache_clear()`` attributes.

    :param ttl: Time-to-live in seconds. 0 = permanent (session lifetime).
    :return: Decorator that wraps an async function with caching.
    """
    store = CacheStore(ttl=ttl)

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        async def wrapper(*args: t.Any, **kwargs: t.Any) -> t.Any:
            key = CacheStore.build_key(fn.__name__, args, kwargs)
            hit, value = store.get(key)
            if hit:
                return value
            result = await fn(*args, **kwargs)
            store.set(key, result)
            return result

        wrapper.cache = store  # type: ignore[attr-defined]
        wrapper.cache_clear = store.clear  # type: ignore[attr-defined]
        return wrapper  # type: ignore[return-value]

    return decorator
