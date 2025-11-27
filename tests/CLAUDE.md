
## Integration tests
please ensure that when we run tests that we use `TESTCONTAINERS_RYUK_DISABLED=true`
this is because we use the `pytest-xdist` package to run containers in parallel.

here is an example `TESTCONTAINERS_RYUK_DISABLED=true uv run pytest tests/integration/test_verification/ -n 2 -v`



