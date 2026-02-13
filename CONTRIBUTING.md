# Contributing to OpenClaw Monitor

Thank you for your interest in contributing to OpenClaw Monitor! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. Please read our [Code of Conduct](CODE_OF_CONDUCT.md) for details.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/openclaw/monitor/issues)
2. If not, create a new issue using the Bug Report template
3. Include:
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - System information (OS, Python version, hardware)

### Suggesting Features

1. Check existing issues for similar suggestions
2. Create a new issue using the Feature Request template
3. Describe the feature and its use case clearly

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Commit with clear messages
7. Push to your fork
8. Open a Pull Request

## Development Setup

### Prerequisites

- Python 3.9 or higher
- pip

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/monitor.git
cd monitor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=openclaw_monitor

# Run specific test file
pytest tests/test_config.py
```

### Code Style

We use Ruff for linting and formatting:

```bash
# Check for issues
ruff check src tests

# Format code
ruff format src tests
```

### Type Checking

We use mypy for static type checking:

```bash
mypy src
```

## Project Structure

```
openclaw-monitor/
├── src/openclaw_monitor/    # Main package
│   ├── collectors/          # Metric collectors
│   ├── handlers/            # HTTP handlers
│   ├── static/              # Frontend files
│   ├── config.py            # Configuration
│   ├── server.py            # HTTP server
│   └── ...
├── tests/                   # Test suite
├── pyproject.toml           # Package configuration
└── ...
```

## Release Process

1. Update version in `src/openclaw_monitor/__init__.py`
2. Update `CHANGELOG.md`
3. Create a GitHub release
4. CI will automatically publish to PyPI

## Questions?

Feel free to open an issue for any questions or discussions.

Thank you for contributing!
