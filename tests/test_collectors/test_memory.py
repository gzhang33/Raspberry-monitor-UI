"""Tests for memory collector."""

import pytest

from monitor.collectors.memory import MemoryCollector


class TestMemoryCollector:
    """Tests for MemoryCollector."""

    def test_name(self):
        """Test collector name."""
        collector = MemoryCollector()
        assert collector.name == "memory"

    def test_collect_returns_dict(self):
        """Test that collect returns a dictionary."""
        collector = MemoryCollector()
        result = collector.collect()
        assert isinstance(result, dict)

    def test_collect_has_required_keys(self):
        """Test that result has required keys."""
        collector = MemoryCollector()
        result = collector.collect()
        assert "percent" in result
        assert "used_gb" in result
        assert "total_gb" in result
        assert "swap_percent" in result

    def test_values_are_positive(self):
        """Test that values are non-negative."""
        collector = MemoryCollector()
        result = collector.collect()
        assert result["percent"] >= 0
        assert result["used_gb"] >= 0
        assert result["total_gb"] > 0  # Total should always be > 0
