"""Tests for CPU collector."""

from monitor.collectors.cpu import CPUCollector


class TestCPUCollector:
    """Tests for CPUCollector."""

    def test_name(self):
        """Test collector name."""
        collector = CPUCollector()
        assert collector.name == "cpu"

    def test_collect_returns_dict(self):
        """Test that collect returns a dictionary."""
        collector = CPUCollector()
        result = collector.collect()
        assert isinstance(result, dict)

    def test_collect_has_required_keys(self):
        """Test that result has required keys."""
        collector = CPUCollector()
        result = collector.collect()
        assert "percent" in result
        assert "freq" in result

    def test_percent_is_float(self):
        """Test that percent is a float."""
        collector = CPUCollector()
        result = collector.collect()
        assert isinstance(result["percent"], float)
        assert 0 <= result["percent"] <= 100

    def test_freq_is_int(self):
        """Test that freq is an int."""
        collector = CPUCollector()
        result = collector.collect()
        assert isinstance(result["freq"], int)
        assert result["freq"] >= 0
