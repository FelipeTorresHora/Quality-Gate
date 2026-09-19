from app.core.config import Settings
from app.services import runtime_cache_service


def test_get_json_returns_none_when_cache_disabled(monkeypatch):
    monkeypatch.setattr(
        runtime_cache_service,
        "_get_cache",
        lambda: None,
    )
    assert runtime_cache_service.get_json("key") is None
    runtime_cache_service.set_json("key", {"a": 1}, ttl=10, tags=["t"])
    runtime_cache_service.expire_tags(["t"])


class _BrokenCache:
    def get(self, key):
        raise RuntimeError("boom")

    def set(self, key, value, options):
        raise RuntimeError("boom")

    def expire_tag(self, tags):
        raise RuntimeError("boom")


def test_cache_operations_swallow_errors(monkeypatch):
    monkeypatch.setattr(runtime_cache_service, "_get_cache", lambda: _BrokenCache())
    assert runtime_cache_service.get_json("k") is None
    runtime_cache_service.set_json("k", 1, ttl=1, tags=[])
    runtime_cache_service.expire_tags(["x"])


class _FakeCache:
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value, options):
        self.store[key] = value

    def expire_tag(self, tags):
        self.store.clear()


def test_get_cache_returns_none_when_vercel_import_fails(monkeypatch):
    runtime_cache_service._get_cache.cache_clear()
    monkeypatch.setattr(
        runtime_cache_service,
        "get_settings",
        lambda: Settings(runtime_cache_enabled=True),
    )

    def fail_import(name, *args, **kwargs):
        raise ImportError("no vercel")

    import builtins

    real_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "vercel.functions":
            raise ImportError("no vercel")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    assert runtime_cache_service._get_cache() is None
    runtime_cache_service._get_cache.cache_clear()


def test_get_cache_returns_none_when_runtime_cache_ctor_fails(monkeypatch):
    runtime_cache_service._get_cache.cache_clear()
    monkeypatch.setattr(
        runtime_cache_service,
        "get_settings",
        lambda: Settings(runtime_cache_enabled=True),
    )

    class BrokenRuntimeCache:
        def __init__(self, namespace):
            raise RuntimeError("init failed")

    import sys
    from types import ModuleType

    fake_vercel = ModuleType("vercel")
    fake_functions = ModuleType("vercel.functions")
    fake_functions.RuntimeCache = BrokenRuntimeCache
    fake_vercel.functions = fake_functions
    monkeypatch.setitem(sys.modules, "vercel", fake_vercel)
    monkeypatch.setitem(sys.modules, "vercel.functions", fake_functions)

    assert runtime_cache_service._get_cache() is None
    runtime_cache_service._get_cache.cache_clear()
