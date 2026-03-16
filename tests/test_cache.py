from __future__ import annotations

import asyncio
import time
from unittest import IsolatedAsyncioTestCase, TestCase

from ton_mcp.constants import (
    CACHE_TTL_JETTON_METADATA,
    CACHE_TTL_PUBLIC_KEY,
    CACHE_TTL_RESOLVE_DESTINATION,
    CACHE_TTL_ROYALTY_PARAMS,
    CACHE_TTL_WALLET_ADDRESS,
)
from ton_mcp.utils.cache import CacheStore, async_ttl_cache


class TestCacheStore(TestCase):
    """Low-level CacheStore behavior."""

    def test_set_and_get_hit(self) -> None:
        store = CacheStore(ttl=60)
        store.set("k", "v")
        hit, value = store.get("k")
        self.assertTrue(hit)
        self.assertEqual(value, "v")

    def test_get_miss(self) -> None:
        store = CacheStore(ttl=60)
        hit, value = store.get("missing")
        self.assertFalse(hit)
        self.assertIsNone(value)

    def test_ttl_expiry(self) -> None:
        store = CacheStore(ttl=0.1)
        store.set("k", "v")
        time.sleep(0.15)
        hit, _ = store.get("k")
        self.assertFalse(hit)

    def test_permanent_never_expires(self) -> None:
        store = CacheStore(ttl=0)
        store.set("k", "v")
        hit, value = store.get("k")
        self.assertTrue(hit)
        self.assertEqual(value, "v")

    def test_maxsize_evicts_oldest(self) -> None:
        store = CacheStore(ttl=60, maxsize=2)
        store.set("a", 1)
        store.set("b", 2)
        store.set("c", 3)
        hit_a, _ = store.get("a")
        hit_c, val_c = store.get("c")
        self.assertFalse(hit_a)
        self.assertTrue(hit_c)
        self.assertEqual(val_c, 3)

    def test_clear(self) -> None:
        store = CacheStore(ttl=60)
        store.set("a", 1)
        store.set("b", 2)
        store.clear()
        self.assertFalse(store.get("a")[0])
        self.assertFalse(store.get("b")[0])


class TestBuildKey(TestCase):
    """Cache key construction from function args."""

    def test_hashable_args_included(self) -> None:
        key = CacheStore.build_key("fn", ("hello", 42), {})
        self.assertEqual(key, "fn:hello:42")

    def test_complex_args_skipped(self) -> None:
        obj = object()
        key = CacheStore.build_key("fn", (obj, "addr"), {})
        self.assertEqual(key, "fn:addr")

    def test_kwargs_included(self) -> None:
        key = CacheStore.build_key("fn", (), {"address": "EQ...", "index": 5})
        self.assertEqual(key, "fn:address='EQ...':index=5")

    def test_kwargs_sorted(self) -> None:
        key1 = CacheStore.build_key("fn", (), {"b": "2", "a": "1"})
        key2 = CacheStore.build_key("fn", (), {"a": "1", "b": "2"})
        self.assertEqual(key1, key2)

    def test_different_args_different_keys(self) -> None:
        k1 = CacheStore.build_key("fn", ("a",), {})
        k2 = CacheStore.build_key("fn", ("b",), {})
        self.assertNotEqual(k1, k2)

    def test_bool_and_float_included(self) -> None:
        key = CacheStore.build_key("fn", (True, 3.14), {})
        self.assertEqual(key, "fn:True:3.14")


class TestAsyncTTLCacheDecorator(IsolatedAsyncioTestCase):
    """Decorator integration tests."""

    def setUp(self) -> None:
        self.call_count = 0

    async def test_cache_hit(self) -> None:
        @async_ttl_cache(60)
        async def cached_fn(x: str) -> str:
            self.call_count += 1
            return f"{x}_{self.call_count}"

        r1 = await cached_fn("a")
        r2 = await cached_fn("a")
        self.assertEqual(r1, r2)
        self.assertEqual(self.call_count, 1)

    async def test_cache_miss_different_args(self) -> None:
        @async_ttl_cache(60)
        async def cached_fn(x: str) -> str:
            self.call_count += 1
            return f"{x}_{self.call_count}"

        await cached_fn("a")
        await cached_fn("b")
        self.assertEqual(self.call_count, 2)

    async def test_ttl_expiry(self) -> None:
        @async_ttl_cache(1)
        async def cached_fn(x: str) -> str:
            self.call_count += 1
            return f"{x}_{self.call_count}"

        r1 = await cached_fn("a")
        await asyncio.sleep(1.1)
        r2 = await cached_fn("a")
        self.assertNotEqual(r1, r2)
        self.assertEqual(self.call_count, 2)

    async def test_permanent_cache(self) -> None:
        @async_ttl_cache(0)
        async def cached_fn(x: str) -> str:
            self.call_count += 1
            return f"{x}_{self.call_count}"

        r1 = await cached_fn("a")
        r2 = await cached_fn("a")
        self.assertEqual(r1, r2)
        self.assertEqual(self.call_count, 1)

    async def test_complex_args_ignored_in_key(self) -> None:
        @async_ttl_cache(60)
        async def cached_fn(client: object, addr: str) -> str:
            self.call_count += 1
            return addr

        obj1 = object()
        obj2 = object()
        await cached_fn(obj1, "EQ...")
        await cached_fn(obj2, "EQ...")
        self.assertEqual(self.call_count, 1)

    async def test_cache_clear(self) -> None:
        @async_ttl_cache(60)
        async def cached_fn(x: str) -> str:
            self.call_count += 1
            return f"{x}_{self.call_count}"

        await cached_fn("a")
        cached_fn.cache_clear()
        await cached_fn("a")
        self.assertEqual(self.call_count, 2)


class TestCacheTTLConstants(TestCase):
    """Verify CACHE_TTL constants."""

    def test_all_non_negative(self) -> None:
        for val in (
            CACHE_TTL_RESOLVE_DESTINATION,
            CACHE_TTL_WALLET_ADDRESS,
            CACHE_TTL_PUBLIC_KEY,
            CACHE_TTL_JETTON_METADATA,
            CACHE_TTL_ROYALTY_PARAMS,
        ):
            self.assertGreaterEqual(val, 0)

    def test_immutable_are_permanent(self) -> None:
        self.assertEqual(CACHE_TTL_WALLET_ADDRESS, 0)
        self.assertEqual(CACHE_TTL_PUBLIC_KEY, 0)

    def test_mutable_have_positive_ttl(self) -> None:
        self.assertGreater(CACHE_TTL_RESOLVE_DESTINATION, 0)
        self.assertGreater(CACHE_TTL_JETTON_METADATA, 0)
        self.assertGreater(CACHE_TTL_ROYALTY_PARAMS, 0)
