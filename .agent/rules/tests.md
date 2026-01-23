---
trigger: glob
description: For writing or updating tests
globs: tests/*
---

# Running tests
1. Use `uv run pytest tests` for running tests. Don't run all tests, only ones you need to run.
2. Always run tests you just wrote. Fix code until tests pass.

# Writing tests
1. Don't write SQL inside tests. All queries should be written inside project repositories, and methods are called in tests.
2. When trying to send request to API use `client.request()` method instead of custom methods like `client.get()`, `client.delete()`, etc...
3. Do not use async mocks for 'getting data' from db. Use real data inside db. Create data in db with repositories (`infrastructure/db/`)

# Commenting rules
- For each test add comments for parts of test:
    1. setup
    2. action
    3. check
- Explain simply and short in each part what happens/edited/checked
- If comment is long, use multiple lines for comment, but try to keeps comments short.

# Structuring tests
Key structure:
- tests/integration - Integration tests
- tests/fixtures - Widely used fixtures, such as test database providers from `testcontainers` module.
- tests/mocks - Mock classes used for injecting into other classes
- tests/unit - Unit tests
- tests/e2e - E2E tests

## Domain-driven structuring
For each test we should determine it's domain and place it in directory accordingly. For example tests that test note-related interactors should be placed into `tests/integration/interactors/notes/` folder, not just `tests/integration/interactors/`.

## Integration tests
Integration tests fall into 2 directories: `tests/integration/api/` and `tests/integration/interactors/`. We should determine directory based on what is used for test ACTION step - either API call or interactor call.

# Integration tests
- Don't write mocks for every interactor dependency. We only mock API clients or other classes that do external connections.