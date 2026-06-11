# Testing Guide

## CI-safe Tests

The default pytest suite runs in CI/CD environments and on developer machines without a desktop session. These tests are designed to work with `QT_QPA_PLATFORM=offscreen` and are the ones run by GitHub Actions:

```bash
python -m pytest
python -m pytest -q
```

Current test count: **181 passing tests**

### Test Environment Variables

The CI-safe test suite uses:

```bash
QT_QPA_PLATFORM=offscreen   # Headless Qt rendering (no X11/Wayland/Windows display)
CI=true                     # Optional flag for CI-specific behavior
```

These are automatically set in the GitHub Actions workflow. To run tests locally with the same environment:

```bash
export QT_QPA_PLATFORM=offscreen
python -m pytest
```

### Verify Test Count

To confirm the current test count:

```bash
python -m pytest --collect-only -q    # List all tests
python -m pytest -q                    # Run and report count
```

## GUI / Manual Tests

Some GUI behavior is validated manually or with tests that are not suitable for GitHub Actions because they require:

- A live display server (X11, Wayland, or macOS/Windows desktop)
- User interaction (mouse clicks, keyboard input)
- Native file dialogs
- Platform-specific desktop integration
- Real window focus and rendering behavior

These tests are intentionally excluded from the default pytest discovery via `norecursedirs = ["tests/gui"]` in `pyproject.toml`.

### Running GUI Tests Locally

To run GUI tests on a machine with a working desktop session:

```bash
python -m pytest tests/gui -v
```

Or run both CI-safe and GUI tests:

```bash
python -m pytest tests/ -v
```

This requires a display server and will fail in headless environments like GitHub Actions.

## Test Organization

The test suite is organized as follows:

- **`tests/`** — Main test directory for CI-safe, headless tests
  - `test_*.py` — Test modules for each component
  - `gui/` — GUI/manual tests excluded from GitHub Actions

- **Test Scopes:**
  - Unit tests — Individual classes and functions
  - Integration tests — Round-trip YAML loading/saving, code generation validation
  - Smoke tests — GUI smoke tests with offscreen Qt rendering
  - Functional tests — End-to-end flows with mock providers

## Local Development Testing

When developing locally:

```bash
# Run all CI-safe tests (headless)
python -m pytest

# Run specific test file
python -m pytest tests/test_runner.py -v

# Run with coverage report
python -m pytest --cov=src --cov-report=html

# Run with verbose output
python -m pytest -vv

# Run matching test name pattern
python -m pytest -k "subflow" -v
```

## GitHub Actions

The test matrix runs on:
- **Platforms:** Ubuntu, macOS, Windows
- **Python versions:** 3.10, 3.11, 3.12, 3.13
- **Environment:** Headless with `QT_QPA_PLATFORM=offscreen`

See `.github/workflows/tests.yml` for the full workflow configuration.

## Continuous Integration

The CI workflow includes:

1. **Lint and Type Check** (Python 3.11, Ubuntu)
   - Ruff linter and format checker
   - mypy type checker

2. **Tests** (3 platforms × 4 Python versions)
   - pytest with coverage report
   - Headless Qt rendering

All checks must pass before merging to main.
