# Environment Variables Configuration

This document describes all environment variables used in the Options Deep stock analysis application.

## Environment Variables

- `ENVIRONMENT` - Specifies which environment configuration to load (local, dev, prod)
- `OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD` - Database password for PostgreSQL connection
- `NASDAQ_API_KEY` - API key for accessing NASDAQ company data

## Environment Configuration Files

Static configuration (non-sensitive data) is stored in JSON files located in `src/config/environment_configs/`. The configuration supports multiple databases with the following structure:

```json
{
  "databases": {
    "equities": {
      "host": "localhost",
      "port": 5432,
      "database": "equities-local",
      "username": "postgres"
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
Create a `.env` file in the project root:
```bash
ENVIRONMENT=local
OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD=postgres
NASDAQ_API_KEY=your_nasdaq_api_key_here
```

### Development/Production
Set environment variables in your deployment environment:
```bash
export ENVIRONMENT=dev
export OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD=your_secure_dev_password
export NASDAQ_API_KEY=your_nasdaq_api_key_here
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
├── environment_configs/     # Static configuration files
│   ├── local.json          # Local development settings
│   ├── dev.json            # Development environment settings
│   └── prod.json           # Production environment settings
├── models/                 # Configuration models
│   ├── database.py         # Database configuration model
│   ├── equities.py         # Equities configuration model
│   └── algorithm.py        # Algorithm configuration model
├── configuration.py        # Main configuration manager
├── environment.py          # Environment variables management
└── ENVIRONMENT.md          # This documentation file
```

## Adding New Environment Variables

When adding new environment variables:

1. **Document here**: Add the variable to this file using the format `- VARIABLE_NAME - description`
2. **Update configuration.py**: Add loading logic if needed
3. **Add to .env.example**: Provide example values
4. **Update deployment**: Ensure the variable is set in all environments
5. **Security review**: Determine if the variable contains sensitive data

## Troubleshooting

### Common Issues

1. **Missing environment variable**: Check that all required variables are set
2. **Wrong environment**: Verify `ENVIRONMENT` variable matches your intended environment
3. **Config file not found**: Ensure the environment config JSON file exists
4. **Database connection fails**: Verify database credentials and network connectivity

### Debugging

Enable debug logging to see which configuration is being loaded:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Validation

The application will validate environment variables on startup and provide clear error messages for missing or invalid configurations.