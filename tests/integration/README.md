# Test Verification Suite

This directory contains test infrastructure verification tests that demonstrate and validate the parallel testing capabilities of the Options Deep integration test framework.

## Purpose

These tests verify that:
1. **Container Isolation** - Each test can create its own independent PostgreSQL container
2. **Parallel Execution** - Multiple tests can run simultaneously without interference
3. **Dynamic Port Assignment** - testcontainers correctly assigns unique ports to each container
4. **Pre-Applied Migrations** - The `options-deep-test:latest` Docker image works correctly
5. **Repository Independence** - Each test can instantiate repositories that connect to different containers

## Tests in This Suite

### test_simple_setup.py
Original setup verification test that validates:
- Container starts successfully
- Pre-applied migrations created all tables
- Repository can insert and retrieve companies
- Basic end-to-end workflow functions

**Run time:** ~3-5 seconds

### test_parallel_container_a.py
Parallel execution test A that:
- Creates its own PostgreSQL container (independent from other tests)
- Inserts "Parallel Test Company A" (Technology/Software sector)
- Logs timestamps to demonstrate parallel execution
- Verifies complete isolation from other tests

**Run time:** ~3-5 seconds

### test_parallel_container_b.py
Parallel execution test B that:
- Creates its own PostgreSQL container (independent from other tests)
- Inserts "Parallel Test Company B" (Finance/Banking sector)
- Logs timestamps to demonstrate parallel execution
- Verifies complete isolation from other tests

**Run time:** ~3-5 seconds

## Prerequisites

### 1. Install pytest-xdist

The parallel execution capability requires pytest-xdist:

```bash
# Install test dependencies (includes pytest-xdist)
uv sync --group test

# Or install all dependencies
uv sync --all-groups
```

### 2. Build Test Docker Image

The tests require the pre-migrated Docker image:

```bash
# Build the test image
make build-test-image

# Or use the script directly
./scripts/build_test_image.sh
```

### 3. Verify Docker is Running

Ensure Docker Desktop is running before executing tests.

## Running the Tests

### Sequential Execution (Default)

Run tests one at a time in sequence:

```bash
# Run all verification tests sequentially
pytest tests/integration/test_verification/ -v

# Run a specific test
pytest tests/integration/test_verification/test_simple_setup.py -v
```

**Expected duration:** ~10-15 seconds (sum of all test durations)

### Parallel Execution (pytest-xdist)

Run tests simultaneously using multiple worker processes:

```bash
# Run with 2 workers (recommended for these 3 tests)
pytest tests/integration/test_verification/ -n 2 -v

# Run with 3 workers (one per test)
pytest tests/integration/test_verification/ -n 3 -v

# Run with auto worker detection (uses all CPU cores)
pytest tests/integration/test_verification/ -n auto -v
```

**Expected duration:** ~3-5 seconds (same as longest single test)

### Verifying Parallel Execution

To confirm tests are running in parallel, look for:

1. **Interleaved output** - TEST A and TEST B logs will be mixed together
2. **Similar timestamps** - Both tests start around the same time
3. **Total duration** - Should be ~same as single test, not 2x

Example output showing parallel execution:
```
TEST A: Started at 14:23:45.123
TEST B: Started at 14:23:45.156
✓ TEST A: Container started at 14:23:47.234
✓ TEST B: Container started at 14:23:47.298
...
✅ TEST A: COMPLETED at 14:23:50.445
   Total duration: 5.322s
✅ TEST B: COMPLETED at 14:23:50.512
   Total duration: 5.356s
```

## How Parallel Execution Works

### Container Isolation

Each test creates its own PostgreSQL container using testcontainers:

```python
with PostgresContainer("options-deep-test:latest", ...) as postgres:
    # This container is completely isolated
    # - Separate Docker container
    # - Different port (e.g., 55432 vs 55433)
    # - Independent database
```

### pytest-xdist Workers

When you run `pytest -n 2`:
1. pytest-xdist spawns 2 worker processes
2. Each worker gets its own Python interpreter
3. Tests are distributed across workers (e.g., Test A → Worker 1, Test B → Worker 2)
4. Workers run independently and in parallel
5. Results are collected and displayed together

### Dynamic Port Assignment

testcontainers automatically assigns unique ports:
- Test A container might use `localhost:55432`
- Test B container might use `localhost:55433`
- No manual port configuration needed
- No port conflicts possible

## Troubleshooting

### Tests Still Run Sequentially

**Symptom:** When running with `-n 2`, tests still execute one at a time

**Possible Causes:**
1. pytest-xdist not installed
2. Using session-scoped fixtures that force serialization
3. Not enough tests to parallelize

**Solution:**
```bash
# Verify pytest-xdist is installed
pytest --version
# Should show: pytest 8.x.x
# plugins: xdist-3.x.x, ...

# Reinstall if needed
uv sync --group test
```

### Container Startup Failures

**Symptom:** Tests fail with Docker connection errors

**Solutions:**
- Ensure Docker Desktop is running
- Verify image exists: `docker images | grep options-deep-test`
- Rebuild image: `make build-test-image`
- Check Docker logs: `docker logs <container-id>`

### Port Conflicts

**Symptom:** Tests fail with "address already in use" errors

**This should NOT happen** - testcontainers uses random ports. If you see this:
1. Check for manual port assignments in test code (there shouldn't be any)
2. Verify no containers are running: `docker ps`
3. Clean up stale containers: `docker rm -f $(docker ps -aq)`

### Slow Parallel Execution

**Symptom:** Parallel tests take as long as sequential tests

**Possible Causes:**
1. Not enough CPU cores (tests might be waiting for CPU)
2. Docker resource constraints
3. Disk I/O bottleneck

**Solutions:**
- Check Docker Desktop resource settings (increase CPU/Memory if needed)
- Reduce number of workers: `-n 2` instead of `-n auto`
- Run fewer tests in parallel

## Integration with Main Test Suite

These verification tests are standalone and don't interfere with the main integration test suite:

```
tests/integration/
├── test_verification/         # This directory (verification tests)
│   ├── README.md
│   ├── test_simple_setup.py
│   ├── test_parallel_container_a.py
│   └── test_parallel_container_b.py
│
└── company_ingestion/         # Main integration tests
    ├── nasdaq/
    └── eodhd/
```

### Running All Tests in Parallel

You can run the entire integration suite in parallel:

```bash
# Run all integration tests with parallel execution
pytest tests/integration/ -n auto -v

# This will parallelize:
# - Verification tests
# - Company ingestion tests
# - Any other integration tests
```

## Best Practices

### When to Use Parallel Execution

**Use parallel execution (`-n 2` or `-n auto`) when:**
- Running the full integration test suite
- Running multiple independent test files
- CI/CD pipelines (faster feedback)
- You have multiple CPU cores available

**Don't use parallel execution when:**
- Debugging a specific test failure
- Analyzing test output in detail
- Running a single test file
- System resources are limited

### Writing Parallel-Safe Tests

When creating new integration tests that should support parallel execution:

1. **Avoid shared fixtures** - Each test creates its own container
2. **Use function scope** - Don't rely on session/module-scoped database state
3. **Independent data** - Don't assume data from other tests exists
4. **Unique identifiers** - Use unique company names, symbols, etc.
5. **Clean state** - Each test starts with a fresh database

Example:
```python
def test_my_feature():
    # Good: Creates own container
    with PostgresContainer(...) as postgres:
        # Test code here
        pass

    # Container auto-cleaned up
```

## Performance Benchmarks

Based on current test infrastructure:

| Execution Mode | Duration | Speedup |
|----------------|----------|---------|
| Sequential     | ~10-15s  | 1x      |
| Parallel (-n 2)| ~5-7s    | ~2x     |
| Parallel (-n 3)| ~4-6s    | ~2.5x   |

**Notes:**
- Speedup is limited by container startup time (~2-3s)
- Diminishing returns beyond number of tests
- Actual performance depends on system resources

## Future Enhancements

Potential improvements to this verification suite:

1. **Stress test** - Run 10+ parallel containers to test resource limits
2. **Conflict detection** - Verify no resource conflicts under load
3. **Performance metrics** - Automated benchmark tracking
4. **Resource monitoring** - Track Docker CPU/memory usage during parallel tests
5. **Cleanup verification** - Ensure all containers are properly removed

## References

- [pytest-xdist Documentation](https://pytest-xdist.readthedocs.io/)
- [testcontainers-python Documentation](https://testcontainers-python.readthedocs.io/)
- [Main Integration Test README](../README.md)
