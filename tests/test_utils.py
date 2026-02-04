"""Tests for circuit breaker, cache, and metrics."""
import os
import sys
import time
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCircuitBreaker:
    """Test cases for CircuitBreaker."""

    def test_circuit_closed_initially(self):
        """Test circuit starts in closed state."""
        from src.utils.circuit_breaker import CircuitBreaker, CircuitConfig

        breaker = CircuitBreaker("test", CircuitConfig(failure_threshold=3))
        assert breaker.state.value == "closed"

    def test_circuit_opens_after_failures(self):
        """Test circuit opens after threshold failures."""
        from src.utils.circuit_breaker import CircuitBreaker, CircuitConfig, CircuitBreakerError

        breaker = CircuitBreaker("test", CircuitConfig(failure_threshold=3))

        def fail():
            raise ValueError("Test failure")

        # First 2 calls should fail with ValueError
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(fail)

        # After 3rd failure, circuit opens and CircuitBreakerError is raised
        with pytest.raises(CircuitBreakerError):
            breaker.call(fail)

        assert breaker.state.value == "open"
        assert not breaker.can_execute()

    def test_circuit_rejects_when_open(self):
        """Test circuit rejects calls when open."""
        from src.utils.circuit_breaker import CircuitBreaker, CircuitConfig, CircuitBreakerError

        breaker = CircuitBreaker("test", CircuitConfig(failure_threshold=2, timeout_seconds=0.1))

        def fail():
            raise ValueError("Test failure")

        # First call - should raise ValueError
        with pytest.raises(ValueError):
            breaker.call(fail)

        assert breaker.state.value == "closed"

        # Second call - should raise CircuitBreakerError because circuit opens after failure
        with pytest.raises(CircuitBreakerError):
            breaker.call(fail)

        assert breaker.state.value == "open"

    def test_circuit_half_open_after_timeout(self):
        """Test circuit transitions to half-open after timeout."""
        from src.utils.circuit_breaker import CircuitBreaker, CircuitConfig, CircuitBreakerError

        breaker = CircuitBreaker("test", CircuitConfig(
            failure_threshold=2,
            success_threshold=2,
            timeout_seconds=0.05
        ))

        def fail():
            raise ValueError("Test failure")

        # Open the circuit
        with pytest.raises((ValueError, CircuitBreakerError)):
            breaker.call(fail)
        with pytest.raises(CircuitBreakerError):
            breaker.call(fail)

        assert breaker.state.value == "open"

        # Wait for timeout
        time.sleep(0.1)

        # Circuit should transition to half-open
        assert breaker.state.value == "half_open"

    def test_circuit_closes_after_successes(self):
        """Test circuit closes after success threshold."""
        from src.utils.circuit_breaker import CircuitBreaker, CircuitConfig, CircuitBreakerError

        breaker = CircuitBreaker("test", CircuitConfig(
            failure_threshold=2,
            success_threshold=2,
            timeout_seconds=0.05
        ))

        def succeed():
            return "success"

        def fail():
            raise ValueError("Test failure")

        # Open the circuit
        with pytest.raises((ValueError, CircuitBreakerError)):
            breaker.call(fail)
        with pytest.raises(CircuitBreakerError):
            breaker.call(fail)
        assert breaker.state.value == "open"

        # Wait for timeout
        time.sleep(0.1)

        # Circuit should be half-open
        assert breaker.state.value == "half_open"

        # Add successes to close circuit
        breaker.call(succeed)
        breaker.call(succeed)

        # Circuit should be closed
        assert breaker.state.value == "closed"

    def test_circuit_records_metrics(self):
        """Test circuit records success/failure metrics."""
        from src.utils.circuit_breaker import CircuitBreaker, CircuitConfig

        breaker = CircuitBreaker("test", CircuitConfig(failure_threshold=5))

        breaker.call(lambda: "success")
        try:
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        except ValueError:
            pass

        metrics = breaker.metrics
        assert metrics.successes == 1
        assert metrics.failures == 1
        assert metrics.total_calls == 2

    def test_circuit_repr(self):
        """Test circuit string representation."""
        from src.utils.circuit_breaker import CircuitBreaker, CircuitConfig

        breaker = CircuitBreaker("my_circuit", CircuitConfig())
        repr_str = repr(breaker)
        assert "my_circuit" in repr_str
        assert "closed" in repr_str


class TestLRUCache:
    """Test cases for LRUCache."""

    def test_basic_operations(self):
        """Test basic get/set operations."""
        from src.utils.cache import LRUCache

        cache = LRUCache(max_size=3)

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        assert "key1" in cache
        assert len(cache) == 1

    def test_lru_eviction(self):
        """Test LRU eviction when capacity reached."""
        from src.utils.cache import LRUCache

        cache = LRUCache(max_size=3)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Access key1 to make it most recently used
        cache.get("key1")

        # Add new item, should evict key2
        cache.set("key4", "value4")

        assert cache.get("key1") == "value1"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"
        assert cache.get("key2") is None

    def test_ttl_expiration(self):
        """Test TTL-based expiration."""
        from src.utils.cache import LRUCache

        cache = LRUCache(max_size=10, ttl_seconds=0.1)

        cache.set("key", "value")
        assert cache.get("key") == "value"

        time.sleep(0.15)

        assert cache.get("key") is None

    def test_delete(self):
        """Test cache deletion."""
        from src.utils.cache import LRUCache

        cache = LRUCache()
        cache.set("key", "value")

        assert cache.delete("key") is True
        assert cache.delete("key") is False
        assert cache.get("key") is None

    def test_clear(self):
        """Test cache clear."""
        from src.utils.cache import LRUCache

        cache = LRUCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()

        assert len(cache) == 0
        assert cache.get("key1") is None

    def test_get_or_set(self):
        """Test get_or_set with factory."""
        from src.utils.cache import LRUCache

        cache = LRUCache()
        calls = []

        def factory():
            calls.append(1)
            return "computed"

        result1 = cache.get_or_set("key", factory)
        assert result1 == "computed"
        assert len(calls) == 1

        result2 = cache.get_or_set("key", factory)
        assert result2 == "computed"
        assert len(calls) == 1

    def test_cleanup(self):
        """Test cleanup of expired entries."""
        from src.utils.cache import LRUCache

        cache = LRUCache(max_size=10, ttl_seconds=0.1)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        time.sleep(0.15)

        removed = cache.cleanup()
        assert removed == 2
        assert len(cache) == 0

    def test_cache_stats(self):
        """Test cache statistics."""
        from src.utils.cache import LRUCache

        cache = LRUCache()

        cache.set("key1", "value1")
        cache.get("key1")
        cache.get("missing")

        stats = cache.stats
        assert stats.hits == 1
        assert stats.misses == 1
        assert stats.total_items == 1

    def test_cache_repr(self):
        """Test cache string representation."""
        from src.utils.cache import LRUCache

        cache = LRUCache(max_size=100)
        cache.set("key", "value")

        repr_str = repr(cache)
        assert "LRUCache" in repr_str
        assert "100" in repr_str


class TestMetrics:
    """Test cases for Prometheus metrics."""

    def test_counter(self):
        """Test counter metric."""
        from src.utils.metrics import Counter

        counter = Counter("test_counter", "A test counter", ["method"])
        counter.inc(1, {"method": "GET"})
        counter.inc(1, {"method": "POST"})

        samples = counter.collect()
        assert len(samples) == 2

    def test_gauge(self):
        """Test gauge metric."""
        from src.utils.metrics import Gauge

        gauge = Gauge("test_gauge", "A test gauge", ["status"])
        gauge.set(10, {"status": "active"})
        gauge.inc(5, {"status": "active"})
        gauge.dec(3, {"status": "active"})

        samples = gauge.collect()
        assert len(samples) == 1
        assert samples[0].value == 12.0

    def test_histogram(self):
        """Test histogram metric."""
        from src.utils.metrics import Histogram

        histogram = Histogram("test_histogram", "A test histogram", ["operation"])
        histogram.observe(0.1, {"operation": "read"})
        histogram.observe(0.5, {"operation": "read"})
        histogram.observe(1.0, {"operation": "write"})

        samples = histogram.collect()
        assert len(samples) > 0

    def test_summary(self):
        """Test summary metric."""
        from src.utils.metrics import Summary

        summary = Summary("test_summary", "A test summary", ["operation"])
        summary.observe(10.0, {"operation": "query"})
        summary.observe(20.0, {"operation": "query"})

        samples = summary.collect()
        assert len(samples) > 0

    def test_registry(self):
        """Test metrics registry."""
        from src.utils.metrics import registry

        counter = registry.counter("my_counter", "My counter", ["label"])
        counter.inc(1)

        output = registry.collect()
        assert "my_counter" in output
        assert "# TYPE my_counter counter" in output


class TestCacheKey:
    """Test cache key generation."""

    def test_cache_key_from_prompt(self):
        """Test cache key generation from prompt."""
        from src.utils.cache import cache_key_from_prompt

        key1 = cache_key_from_prompt("  Write Python code  ")
        key2 = cache_key_from_prompt("write python code")
        key3 = cache_key_from_prompt("Different prompt")

        assert key1 == key2
        assert key1 != key3
        assert len(key1) == 32  # MD5 hex digest


class TestCircuitManager:
    """Test cases for CircuitManager."""

    def test_manager_operations(self):
        """Test circuit manager operations."""
        from src.utils.circuit_breaker import CircuitManager, CircuitConfig

        manager = CircuitManager()

        c1 = manager.get_or_create("circuit1", CircuitConfig(failure_threshold=2))
        c2 = manager.get_or_create("circuit2")

        assert c1 is not None
        assert c2 is not None
        assert c1 is not c2

    def test_health_check(self):
        """Test circuit manager health check."""
        from src.utils.circuit_breaker import CircuitManager, CircuitConfig

        manager = CircuitManager()

        healthy = manager.health_check()
        assert healthy["healthy"] is True
        assert healthy["total_circuits"] == 0
