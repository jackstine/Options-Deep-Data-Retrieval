# Dockerfile for Options Deep Test Image
# Creates a PostgreSQL container with pre-applied Alembic migrations
# This eliminates the ~5-10 second migration overhead from integration tests

# =============================================================================
# Stage 1: Base Image with Dependencies (Rarely Rebuilt)
# =============================================================================
FROM postgres:latest AS base

# Install Python 3 and pip for running Alembic migrations
RUN apt-get update && \
    apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment for Python dependencies
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies required for Alembic migrations
# These rarely change - cache this layer!
RUN pip install --no-cache-dir \
    alembic>=1.13.0 \
    sqlalchemy>=2.0.43 \
    psycopg2-binary>=2.9.11 \
    python-dotenv>=1.0.0 \
    pydantic>=2.11.7

# Set working directory
WORKDIR /opt/options-deep

# =============================================================================
# Stage 2: Migration Image with Code (Frequently Rebuilt)
# =============================================================================
FROM base AS migrations

# Copy only src directories needed for migrations (env.py imports from src)
# Only database/ is required - it now contains its own configuration
# This selective copy reduces rebuilds - changes to cmd, config, data_sources,
# models, pipelines, repos, services, and utils won't trigger a rebuild
COPY src/__init__.py /opt/options-deep/src/__init__.py
COPY src/database/ /opt/options-deep/src/database/

# Fix permissions for postgres user to read config files
RUN chmod -R 755 /opt/options-deep/src/

# Create .local-test.env file for ConfigurationManager
# This prevents FileNotFoundError when CONFIG tries to load the env file
RUN echo "ENVIRONMENT=local-test" > /opt/options-deep/.local-test.env && \
    echo "OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD=test" >> /opt/options-deep/.local-test.env && \
    echo "NASDAQ_API_KEY=test_key" >> /opt/options-deep/.local-test.env && \
    echo "EODHD_API_KEY=test_key" >> /opt/options-deep/.local-test.env

# Set environment variables required for migrations
ENV OPTIONS_DEEP_ENV=local-test \
    OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD=test \
    ENVIRONMENT=local-test \
    NASDAQ_API_KEY=test_key \
    EODHD_API_KEY=test_key \
    PGUSER=test \
    PGPASSWORD=test \
    PGDATABASE=test

# Copy entrypoint script that will run Alembic migrations
# Scripts in /docker-entrypoint-initdb.d/ are automatically executed
# after PostgreSQL initializes the database
# Use --chmod to set executable permissions during copy
COPY --chmod=0755 dockerfiles/test/docker-entrypoint-init.sh /docker-entrypoint-initdb.d/10-run-migrations.sh

# The postgres image's default entrypoint will:
# 1. Initialize the PostgreSQL database
# 2. Run scripts in /docker-entrypoint-initdb.d/ (our migrations)
# 3. Start PostgreSQL server
