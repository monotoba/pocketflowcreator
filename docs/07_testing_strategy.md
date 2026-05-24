# Testing Strategy

## Test Layers

1. Model tests for graph and node metadata.
2. Validation tests for structural errors.
3. Code generation tests for generated Python text.
4. Provider tests using mock providers.
5. GUI smoke tests after PySide6 test infrastructure is added.
6. Exported project smoke tests.

## Required Test Rule

Every new behavior should include a test. For refactoring, preserve existing behavior and keep tests passing.

## LLM Testing Rule

Tests should not require real LLM calls by default. Use mock providers for deterministic results.
