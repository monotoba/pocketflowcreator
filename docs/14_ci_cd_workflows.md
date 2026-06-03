# GitHub Actions CI/CD Workflows

PocketFlow Creator uses comprehensive GitHub Actions workflows to ensure code quality, security, and reliable releases.

## Overview

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| **Tests** | Push/PR to main/develop | Unit tests, linting, type checking across multiple OS/Python versions |
| **Build** | Push/PR to main/develop | Verify package builds, check distribution with twine |
| **Security** | Push/PR + daily schedule | Security scanning with Bandit, dependency checks |
| **Docs** | Changes to docs/** | Markdown linting, link checking, documentation validation |
| **Release** | GitHub release published | Build and publish package to PyPI |
| **Release Notes** | Release created/edited | Validate release, verify changelog and version consistency |

---

## Tests Workflow

**File**: `.github/workflows/tests.yml`

### What it does

- **Linting**: Validates code style with `ruff check` and `ruff format`
- **Type Checking**: Verifies type hints with `mypy`
- **Unit Tests**: Runs pytest suite with coverage reporting
- **Multi-OS Testing**: Runs on Ubuntu, macOS, and Windows
- **Multi-Python Testing**: Tests Python 3.10, 3.11, 3.12, 3.13
- **Coverage Upload**: Sends coverage reports to Codecov

### Jobs

#### `lint`
- Runs on: Ubuntu (single job)
- Checks: ruff lint, ruff format, mypy types
- Python: 3.11

#### `test`
- Runs on: Ubuntu, macOS, Windows
- Tests: All Python 3.10-3.13
- Metrics: Line coverage, branch coverage
- Reports: Codecov integration

### How to use

Coverage badge in README:
```markdown
[![codecov](https://codecov.io/gh/Monotoba/PocketFlowCreator/branch/main/graph/badge.svg)](https://codecov.io/gh/Monotoba/PocketFlowCreator)
```

View coverage: https://codecov.io/gh/Monotoba/PocketFlowCreator

---

## Build Workflow

**File**: `.github/workflows/build.yml`

### What it does

Verifies that the package can be built and distributed correctly on every PR/push.

### Jobs

- **build**
  - Installs build dependencies
  - Builds wheel and sdist distributions
  - Validates distributions with `twine check`
  - Uploads artifacts (retained for 30 days)

### Artifacts

Build artifacts are uploaded to GitHub Actions and can be downloaded for testing:
1. Go to the workflow run
2. Click "Artifacts" section
3. Download `python-package-distributions`

---

## Security Workflow

**File**: `.github/workflows/security.yml`

### What it does

Automated security scanning to identify potential vulnerabilities.

### Jobs

#### `bandit`
- Scans Python code for security issues
- Generates JSON report
- Continues on errors (doesn't fail the workflow)

#### `dependabot`
- Checks for outdated packages
- Runs full dependency installation
- Lists all outdated packages

### Running locally

```bash
# Install and run Bandit
pip install bandit
bandit -r src

# Check outdated packages
pip list --outdated
```

---

## Documentation Workflow

**File**: `.github/workflows/docs.yml`

### What it does

Validates documentation quality and integrity.

### Jobs

#### `markdown-lint`
- Lints all Markdown files
- Uses `.markdownlint.json` config
- Continues on errors (advisory only)

#### `links-check`
- Checks all links in Markdown files
- Verifies internal and external URLs
- Continues on errors (advisory only)

#### `docs-exists`
- Verifies key documentation files exist
- Checks README, CHANGELOG, user guide, provider setup guide
- Verifies help system directory structure

### Creating `.markdownlint.json`

Optional configuration file for markdown linting:

```json
{
  "MD003": { "style": "consistent" },
  "MD004": { "style": "consistent" },
  "MD024": false,
  "MD033": false,
  "MD034": false,
  "no-hard-tabs": false
}
```

---

## Release Workflow

**File**: `.github/workflows/release.yml`

### What it does

Automates package building and publishing to PyPI when a release is created.

### Jobs

#### `build`
- Builds distribution packages (wheel + sdist)
- Validates with twine
- Uploads artifacts

#### `publish`
- Depends on: `build` job
- Uses PyPI trusted publisher (no API key needed)
- Publishes to production PyPI

### Environment

Uses GitHub environment `pypi` with:
- Trusted Publisher configured in PyPI project settings
- No credentials stored in repository

### How to publish a release

1. **Update version**: Edit `pyproject.toml`
   ```toml
   version = "0.3.0"
   ```

2. **Update changelog**: Add entry to `CHANGELOG.md`
   ```markdown
   ## [0.3.0] - 2026-06-03

   ### Added
   - New feature description

   ### Fixed
   - Bug fix description
   ```

3. **Create GitHub Release**:
   - Go to Releases → Draft a new release
   - Tag: `v0.3.0`
   - Release title: `Release v0.3.0`
   - Description: Copy from CHANGELOG.md
   - Click "Publish release"

4. **Workflow runs automatically**:
   - Build job builds packages
   - Publish job publishes to PyPI
   - Release is available at `pip install pocketflow-creator==0.3.0`

---

## Release Notes Workflow

**File**: `.github/workflows/release-notes.yml`

### What it does

Validates releases and ensures consistency before publishing.

### Jobs

#### `validate-release`
- Verifies tag matches version in `pyproject.toml`
- Ensures changelog entry exists
- Prevents mismatched versions

#### `generate-release-notes`
- Extracts release notes from CHANGELOG.md
- Creates release summary comment
- Validates installation instructions

### Version consistency example

**Tag**: `v0.3.0`
**pyproject.toml**: `version = "0.3.0"`
**CHANGELOG.md**: `## [0.3.0] - 2026-06-03`

All three must match, or the release workflow will fail validation.

---

## Local Development

### Running checks locally

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest -v

# Run with coverage
pytest -v --cov=src --cov-report=html

# Lint code
ruff check src tests

# Check formatting
ruff format --check src tests

# Type checking
mypy src

# Security scanning
bandit -r src

# Check distributions
python -m build
twine check dist/*
```

### Pre-commit hooks

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
set -e

echo "Running linting..."
ruff check src tests
ruff format --check src tests

echo "Running type checks..."
mypy src

echo "Running tests..."
pytest -q

echo "✓ All checks passed"
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

---

## Troubleshooting

### Tests failing locally but passing in CI

- Check Python version: `python --version`
- Ensure you're in the venv: `source .venv/bin/activate`
- Reinstall dependencies: `pip install -e ".[dev]"`
- Clear cache: `rm -rf .pytest_cache __pycache__`

### Build failing with "module not found"

- Ensure all files are committed: `git status`
- Check MANIFEST.in is correct
- Verify package structure: `python -m build -w && tar -tzf dist/*.tar.gz | head -20`

### PyPI publish failing

- Verify tag format: `v0.3.0` (with 'v' prefix)
- Verify version in `pyproject.toml` matches tag
- Check PyPI project settings for trusted publisher
- View publish logs in GitHub Actions

### Coverage not uploading

- Ensure `coverage.xml` is generated: `pytest --cov-report=xml`
- Check Codecov token in GitHub repository settings
- View Codecov upload logs in GitHub Actions

---

## Status Badges

Add to README.md:

```markdown
[![Tests](https://github.com/Monotoba/PocketFlowCreator/actions/workflows/tests.yml/badge.svg)](https://github.com/Monotoba/PocketFlowCreator/actions/workflows/tests.yml)
[![Build](https://github.com/Monotoba/PocketFlowCreator/actions/workflows/build.yml/badge.svg)](https://github.com/Monotoba/PocketFlowCreator/actions/workflows/build.yml)
[![codecov](https://codecov.io/gh/Monotoba/PocketFlowCreator/branch/main/graph/badge.svg)](https://codecov.io/gh/Monotoba/PocketFlowCreator)
[![PyPI version](https://badge.fury.io/py/pocketflow-creator.svg)](https://pypi.org/project/pocketflow-creator/)
```

---

## Release Checklist

Before publishing a release:

- [ ] All tests pass locally and in CI
- [ ] Version updated in `pyproject.toml`
- [ ] CHANGELOG.md updated with release notes
- [ ] All commits are on main/develop
- [ ] Tag format is `v0.3.0` (with 'v' prefix)
- [ ] No uncommitted changes
- [ ] Documentation builds without errors

To check CI status before releasing:
1. Go to Actions tab
2. Verify latest commit passed all workflows
3. Check all jobs show ✓ (passed) status

---

## Further Reading

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [PyPA Build Documentation](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [PyPI Trusted Publishers](https://docs.pypi.org/pypi/publishing/)
