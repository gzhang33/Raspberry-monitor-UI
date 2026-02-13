"""Tests for cache module."""

import time

from monitor.cache import RateCalculator, TTLCache


class TestTTLCache:
    """Tests for TTLCache."""

    def test_get_or_compute_caches(self):
        """Test that value is cached."""
        cache = TTLCache(ttl=1.0)
        call_count = 0

        def compute():
            nonlocal call_count
            call_count += 1
            return {"value": 42}

        result1 = cache.get_or_compute(compute)
        result2 = cache.get_or_compute(compute)

        assert result1 == {"value": 42}
        assert result2 == {"value": 42}
        assert call_count == 1  # Should only be called once

    def test_cache_expires(self):
        """Test that cache expires after TTL."""
        cache = TTLCache(ttl=0.1)
        call_count = 0

        def compute():
            nonlocal call_count
            call_count += 1
            return {"value": call_count}

        result1 = cache.get_or_compute(compute)
        time.sleep(0.15)  # Wait for cache to expire
        result2 = cache.get_or_compute(compute)

        assert result1 == {"value": 1}
        assert result2 == {"value": 2}
        assert call_count == 2

    def test_invalidate(self):
        """Test cache invalidation."""
        cache = TTLCache(ttl=10.0)
        call_count = 0

        def compute():
            nonlocal call_count
            call_count += 1
            return {"value": call_count}

        result1 = cache.get_or_compute(compute)
        cache.invalidate()
        result2 = cache.get_or_compute(compute)

        assert result1 == {"value": 1}
        assert result2 == {"value": 2}


class TestRateCalculator:
    """Tests for RateCalculator."""

    def test_first_call_returns_zero(self):
        """Test that first call returns 0."""
        calc = RateCalculator()
        rate = calc.calculate_rate(1000)
        assert rate == 0.0

    def test_calculates_rate(self):
        """Test rate calculation."""
        calc = RateCalculator()

        # First call to initialize
        calc.calculate_rate(1000)
        time.sleep(0.1)

        # Second call should calculate rate
        rate = calc.calculate_rate(2000)
        # Rate should be approximately (2000 - 1000) / 0.1 = 10000/sec
        assert rate > 0

    def test_reset(self):
        """Test calculator reset."""
        calc = RateCalculator()
        calc.calculate_rate(1000)
        calc.reset()

        # After reset, should behave like first call
        rate = calc.calculate_rate(2000)
        assert rate == 0.0
