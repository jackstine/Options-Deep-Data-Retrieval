# Environment Variables Configuration

This document describes all environment variables used in the Options Deep stock analysis application.

## Environment Variables

- `OPTIONS_DEEP_ENV` - **[REQUIRED]** Selects which .env file to load. Must be set to one of: local, dev, qa, prod
- `ENVIRONMENT` - Specifies which environment configuration to load (local, dev, qa, prod)
- `OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD` - Database password for PostgreSQL connection
- `NASDAQ_API_KEY` - API key for accessing NASDAQ company data
- `EODHD_API_KEY` - API key for accessing EODHD market data
- `OPTIONS_DEEP_TEST_DB_PORT` - (Optional) Overrides the database port for integration tests using testcontainers. Set automatically by testcontainer fixtures to use dynamically assigned Docker ports. Should not be set manually in normal usage

## Environment File Selection

The application uses `OPTIONS_DEEP_ENV` to determine which environment file to load. This variable is **required** and must be set.

| OPTIONS_DEEP_ENV | File Loaded | Use Case |
|------------------|-------------|----------|
| `local` | `.local.env` | Local development |
| `dev` | `.dev.env` | Development server |
| `qa` | `.qa.env` | QA/Testing environment |
| `prod` | `.prod.env` | Production environment |

### Example Usage
```bash
# Use local environment file (REQUIRED - must set OPTIONS_DEEP_ENV)
export OPTIONS_DEEP_ENV=local
python src/cmd/my_script.py

# Use production environment file
export OPTIONS_DEEP_ENV=prod
python src/cmd/my_script.py
```

## Configuration Architecture

Configuration is split into two parts for security and flexibility:

### 1. Environment Variables (.env files) - Secrets
Contains sensitive information that should NEVER be committed to version control:
- Database passwords
- API keys
- Sensitive credentials

Located in project root: `.local.env`, `.dev.env`, `.qa.env`, `.prod.env`

### 2. JSON Configuration Files - Settings
Contains non-sensitive configuration stored in version control:
- Database hostnames, ports, database names
- Application settings
- Feature flags

Located in: `src/config/environment_configs/local.json`, `dev.json`, `qa.json`, `prod.json`

## Environment Configuration Files Structure

Example JSON structure (`src/config/environment_configs/local.json`):
```json
{
  "databases": {
    "equities": {
      "host": "localhost",
      "port": 5432,
      "database": "equities-local",
      "username": "e_user"
    },
    "algorithm": {
      "host": "localhost",
      "port": 5432,
      "database": "algorithms-local",
      "username": "postgres"
    }
  }
}
```

## Setting Up Environment Variables

### Local Development

1. Copy the example file:
   ```bash
   cp env.example .local.env
   ```

2. Edit `.local.env` and fill in your values:
   ```bash
   ENVIRONMENT=local
   OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD=your_local_password
   NASDAQ_API_KEY=your_nasdaq_api_key
   ```

3. Set the environment selector:
   ```bash
   export OPTIONS_DEEP_ENV=local
   ```

4. Run your application:
   ```bash
   python src/cmd/your_script.py
   ```

### Development/QA/Production Environments

1. Copy the example file and customize for your environment:
   ```bash
   # For dev
   cp env.example .dev.env

   # For qa
   cp env.example .qa.env

   # For prod
   cp env.example .prod.env
   ```

2. Edit the file and fill in environment-specific values

3. Set the environment selector in your deployment configuration:
   ```bash
   export OPTIONS_DEEP_ENV=prod
   ```

## Accessing Environment Variables in Code

The application provides type-safe access to environment variables through the `CONFIG` singleton:

```python
from src.config.configuration import CONFIG

# Get environment name
env = CONFIG.get_environment()  # Returns: "local", "dev", "qa", or "prod"

# Get database password
password = CONFIG.get_database_password()

# Get NASDAQ API key
api_key = CONFIG.get_nasdaq_api_key()

# Get database config (combines env vars + JSON config)
db_config = CONFIG.get_equities_config()
```

## Type Safety

Environment variables are defined with TypedDict for type safety:

```python
from src.config.models.environment_variables import EnvironmentVariables, ENV_VARS

# ENV_VARS provides constants for IDE autocomplete
ENV_VARS.OP_ENVIRONMENT
ENV_VARS.DB_PASSWORD
ENV_VARS.NASDAQ_API_KEY
```

## Security Best Practices

1. **Never commit sensitive data**: API keys and passwords should never be in version control
2. **Use different passwords**: Each environment should have unique, strong passwords
3. **Rotate keys regularly**: Change API keys and passwords periodically
4. **Restrict access**: Limit who has access to production environment variables
5. **Use secrets management**: In production, consider using AWS Secrets Manager, Azure Key Vault, or similar services

## Configuration Structure

```
src/config/
├── environment_configs/            # Static configuration files (in git)
│   ├── local.json                 # Local development settings
│   ├── dev.json                   # Development environment settings
│   ├── qa.json                    # QA environment settings
│   └── prod.json                  # Production environment settings
├── models/                        # Configuration models
│   ├── database.py                # Database configuration model
│   ├── equities.py                # Equities configuration model
│   ├── algorithm.py               # Algorithm configuration model
│   └── environment_variables.py   # TypedDict for env vars (NEW)
├── configuration.py               # Main configuration manager
└── ENVIRONMENT.md                 # This documentation file

Project root:
├── .local.env                     # Local env file (gitignored)
├── .dev.env                       # Dev env file (gitignored)
├── .qa.env                        # QA env file (gitignored)
├── .prod.env                      # Prod env file (gitignored)
└── env.example                    # Example env file (in git)
```

## Adding New Environment Variables

When adding new environment variables:

1. **Add to TypedDict**: Update `src/config/models/environment_variables.py`
2. **Add to ENV_VARS constants**: For IDE autocomplete
3. **Update ConfigurationManager**: Add getter method in `configuration.py`
4. **Add to validation**: Update `_load_and_validate_env_vars()` if required
5. **Document here**: Add the variable to this file
6. **Update example file**: Add to `env.example` file
7. **Update deployment**: Ensure the variable is set in all environments
8. **Security review**: Determine if the variable contains sensitive data

## Troubleshooting

### Common Issues

1. **OPTIONS_DEEP_ENV not set**
   - Error: `ERROR: OPTIONS_DEEP_ENV environment variable is not set.`
   - Solution: Set OPTIONS_DEEP_ENV to one of: local, dev, qa, prod
   - Example: `export OPTIONS_DEEP_ENV=local`

2. **Missing environment variable**
   - Error: `ValueError: Missing required environment variables: ...`
   - Solution: Ensure all required variables are set in your `.{environment}.env` file

3. **Wrong environment file**
   - Error: `FileNotFoundError: Environment file not found: ...`
   - Solution: Check that `OPTIONS_DEEP_ENV` matches an existing `.{environment}.env` file

4. **Invalid OPTIONS_DEEP_ENV value**
   - Error: `ValueError: Invalid OPTIONS_DEEP_ENV value: ...`
   - Solution: Use one of: local, dev, qa, prod

5. **Config file not found**
   - Error: `Config file not found: src/config/environment_configs/...`
   - Solution: Ensure the corresponding JSON config file exists

6. **Database connection fails**
   - Verify database credentials in `.{environment}.env` file
   - Check database host/port in `environment_configs/*.json`
   - Verify network connectivity

### Debugging

Check which environment file is being loaded:
```python
import os
print(f"OPTIONS_DEEP_ENV: {os.getenv('OPTIONS_DEEP_ENV', 'not set')}")
print(f"ENVIRONMENT: {os.getenv('ENVIRONMENT', 'not set')}")
```

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Validation

The application validates all required environment variables on startup (fail-fast approach) and provides clear error messages for missing or invalid configurations. This ensures problems are caught immediately rather than during runtime.
