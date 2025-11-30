# Running Tests in Parallel

## Prerequisites

Install pytest-xdist:
```bash
uv sync --group test
```

## Running Parallel Tests

Set `TESTCONTAINERS_RYUK_DISABLED=true` to avoid container cleanup conflicts:

```bash
# Run with 2 workers
TESTCONTAINERS_RYUK_DISABLED=true pytest tests/integration/test_verification/ -n 2 -v

# Run with auto worker detection (uses all CPU cores)
TESTCONTAINERS_RYUK_DISABLED=true pytest tests/integration/test_verification/ -n auto -v
```

## Cleanup Test Containers

When Reaper is disabled, containers may remain after tests. Clean them up:

```bash
# Remove all containers based on the test image
docker ps -a --filter "ancestor=options-deep-test:latest" --format "{{.ID}}" | xargs -r docker rm -f
```
