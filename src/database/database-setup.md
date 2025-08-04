# Database Setup Guide: Companies Table

This guide provides step-by-step instructions for setting up the first database table (companies) in the equities database using Alembic migrations.

## Prerequisites

### 1. Environment Variables
Set these environment variables before starting:

```bash
# Required for database connection
export ENVIRONMENT=local                                    # or dev, prod
export OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD=your_password  # Database password

# Verify variables are set
echo "Environment: $ENVIRONMENT"
echo "Password set: ${OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD:+Yes}"
```

### 2. Database User and Database Creation

#### Create Database User (if not exists)
The equities database uses specific users per environment:
- **Local**: `e_user`
- **Dev**: `dev_user` 
- **Prod**: `prod_user`

**For Local Environment (`e_user`):**
```bash
# Check if e_user exists
psql -U postgres -c "SELECT rolname FROM pg_roles WHERE rolname = 'e_user';"

# If user doesn't exist, create it:
psql -U postgres -c "
CREATE USER e_user WITH PASSWORD 'your_secure_password';
ALTER USER e_user CREATEDB;
GRANT CONNECT ON DATABASE postgres TO e_user;
"
```

#### Create Databases with Proper Ownership
```sql
-- Connect as postgres superuser
psql -U postgres

-- For local environment
CREATE DATABASE "equities-local" OWNER e_user;

-- For dev environment  
CREATE DATABASE "equities-dev" OWNER "dev_user";

-- For prod environment
CREATE DATABASE "equities-prod" OWNER "prod_user";
```

#### Grant Schema Permissions
```sql
-- For local environment
psql -U postgres -d "equities-local" -c "
GRANT ALL PRIVILEGES ON SCHEMA public TO e_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO e_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO e_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO e_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO e_user;
"
```

### 3. Dependencies
Install required packages:

```bash
pip install -r requirements.txt
# Includes: SQLAlchemy, psycopg2-binary, alembic
```

### 4. Working Directory
Navigate to the project root:

```bash
cd /path/to/Options-Deep
pwd  # Should show: /path/to/Options-Deep
```

## Initial Setup Verification

### 1. Check Alembic Configuration
Verify the equities database Alembic setup:

```bash
# Navigate to equities database directory
cd src/database/equities

# Check alembic configuration
cat alembic.ini | grep script_location
# Should show: script_location = %(here)s/migrations

# Verify migrations directory exists
ls -la migrations/
# Should show: env.py, script.py.mako, versions/
```

### 2. Test Database Connection
Verify database connectivity with the correct user:

```bash
# Test connection for local environment
psql -h localhost -U e_user -d equities-local -c "SELECT version();"

# Test connection for dev environment  
psql -h dev-db-server.example.com -U dev_user -d equities-dev -c "SELECT version();"

# Test connection for prod environment
psql -h prod-db-server.example.com -U prod_user -d equities-prod -c "SELECT version();"
```

**Note**: You'll be prompted for the password, which should match your `OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD` environment variable.

## Step-by-Step Migration Process

### Step 1: Verify Company Model
Check that the Company model includes the active field:

```bash
# View the company model
cat src/database/equities/tables/company.py | grep -A5 "active ="
# Should show: active = Column(Boolean, nullable=False, default=True, index=True)
```

### Step 2: Check Current Migration Status
From the equities database directory:

```bash
cd src/database/equities

# Check current migration status
alembic current
# Expected: No current revision (clean state)

# View migration history (should be empty initially)
alembic history --verbose
```

### Step 3: Generate Initial Migration
Create the migration for the companies table:

```bash
# Generate migration from Company model
alembic revision --autogenerate -m "Create companies table with active field"

# Expected output:
# INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
# INFO  [alembic.autogenerate.compare] Detected added table 'companies'
# Generating /path/to/migrations/versions/XXXXX_create_companies_table.py ... done
```

### Step 4: Review Generated Migration
Examine the generated migration file:

```bash
# Find the latest migration file
ls -la migrations/versions/
# Look for: XXXXX_create_companies_table.py

# Review the migration content
cat migrations/versions/*_create_companies_table.py
```
### Step 5: Apply Migration
Execute the migration to create the companies table:

```bash
# Apply the migration
alembic upgrade head

# Expected output:
# INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
# INFO  [alembic.runtime.migration] Will assume transactional DDL.
# INFO  [alembic.runtime.migration] Running upgrade  -> XXXXX, Create companies table with active field
```

### Step 6: Verify Migration Success
Confirm the migration was applied:

```bash
# Check current migration status
alembic current
# Should show: XXXXX (head)

# Verify migration history
alembic history
# Should show: <base> -> XXXXX (head), Create companies table with active field
```

## Database Verification

### 1. Verify Table Creation
Connect to database and check table structure:

```sql
-- Connect to database with correct user
psql -h localhost -U e_user -d equities-local

-- List all tables
\dt

-- Describe companies table structure
\d companies

-- Check indexes
\di companies*

-- Verify alembic tracking table
SELECT * FROM alembic_version;
```

Expected table structure:
```
Column      |           Type           | Nullable |      Default
-----------+--------------------------+----------+-------------------
id          | integer                  | not null | nextval('companies_id_seq'::regclass)
ticker      | character varying(20)    | not null |
company_name| character varying(500)   | not null |
exchange    | character varying(20)    | not null |
sector      | character varying(100)   | yes      |
industry    | character varying(200)   | yes      |
country     | character varying(100)   | yes      |
market_cap  | integer                  | yes      |
description | text                     | yes      |
active      | boolean                  | not null | true
source      | character varying(50)    | not null |
created_at  | timestamp with time zone | not null | now()
updated_at  | timestamp with time zone | not null | now()
```

### 2. Test Table Operations
Verify table functionality:

```sql
-- Insert test company
INSERT INTO companies (ticker, company_name, exchange, source) 
VALUES ('TEST', 'Test Company Inc.', 'NASDAQ', 'manual');

-- Verify insert and default values
SELECT id, ticker, company_name, active, created_at FROM companies WHERE ticker = 'TEST';

-- Clean up test data
DELETE FROM companies WHERE ticker = 'TEST';
```

## Modifying and Updating Migrations

### When You Need to Change a Migration

There are several scenarios where you might need to modify or update an Alembic migration:

1. **Before applying**: You generated a migration but want to change it
2. **After applying**: You applied a migration but need to make corrections
3. **Message only**: You want to change the migration message/description
4. **Structural changes**: You need to modify the actual database changes

### Scenario 1: Migration Not Yet Applied (Safe to Modify)

#### Option A: Delete and Regenerate (Recommended)
```bash
cd src/database/equities

# Check if migration has been applied
alembic current
# If output shows "No current revision", migration hasn't been applied

# Find and delete the unwanted migration file
ls migrations/versions/
rm migrations/versions/abc123_unwanted_migration.py

# Make your model changes in src/database/equities/tables/company.py
# Then regenerate the migration
alembic revision --autogenerate -m "Create companies table with correct structure"
```

#### Option B: Edit Migration File Directly
```bash
# Find the migration file
ls migrations/versions/
vim migrations/versions/abc123_migration_name.py

# Edit the upgrade() and downgrade() functions
# Example: Add/remove columns, change column types, modify indexes
```

**Example of editing a migration file:**
```python
def upgrade() -> None:
    # Original generated code
    op.create_table('companies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('ticker', sa.String(length=20), nullable=False),
        # ... other columns
        
        # Add your custom changes here
        sa.Column('custom_field', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add custom indexes
    op.create_index('ix_companies_custom_field', 'companies', ['custom_field'])

def downgrade() -> None:
    # Always mirror the upgrade changes in reverse
    op.drop_index('ix_companies_custom_field', table_name='companies')
    op.drop_table('companies')
```

### Scenario 2: Migration Already Applied (Requires New Migration)

#### Option A: Create Corrective Migration (Recommended)
```bash
# Make changes to your model first
# Edit src/database/equities/tables/company.py

# Generate new migration for the changes
alembic revision --autogenerate -m "Update companies table - remove unused columns"

# Apply the new migration
alembic upgrade head
```

#### Option B: Rollback and Regenerate (Use with Caution)
```bash
# DANGER: This will lose data if the migration created/modified data
# Only use in development environments

# Rollback the migration
alembic downgrade -1

# Delete the old migration file
rm migrations/versions/abc123_old_migration.py

# Make your model changes
# Generate new migration
alembic revision --autogenerate -m "Create companies table - corrected version"

# Apply the migration
alembic upgrade head
```

### Scenario 3: Change Migration Message Only

#### Rename Migration File
```bash
cd src/database/equities/migrations/versions

# Find current migration file
ls -la

# Rename file (keep the revision ID prefix)
mv abc123_old_message.py abc123_create_companies_table_with_active_field.py

# Edit the docstring in the file
vim abc123_create_companies_table_with_active_field.py
```

**Edit the migration file header:**
```python
"""Create companies table with active field

Revision ID: abc123
Revises: def456
Create Date: 2024-01-15 10:30:45.123456

"""
```

#### If You Haven't Created Migration Yet:
```bash
cd src/database/equities
alembic revision --autogenerate -m "Create companies table with active field"
```

#### If You Have an Existing Migration with Old Fields:
```bash
# Check current status
alembic current

# If not applied, delete and regenerate:
rm migrations/versions/old_migration_file.py
alembic revision --autogenerate -m "Create companies table - updated structure"

# If already applied, create corrective migration:
alembic revision --autogenerate -m "Remove currency, employees, website from companies"
alembic upgrade head
```

### Migration Safety Procedures

#### 1. Always Backup Before Changes
```bash
# For local development
pg_dump equities-local > backup_before_migration_$(date +%Y%m%d_%H%M%S).sql

# For production (CRITICAL)
pg_dump equities-prod > prod_backup_before_migration_$(date +%Y%m%d_%H%M%S).sql
```

#### 2. Test Migration Path
```bash
# Test the complete migration path
alembic upgrade head     # Apply migration
alembic downgrade -1     # Test rollback
alembic upgrade head     # Re-apply migration

# Verify data integrity after each step
```

#### 3. Environment-Specific Testing
```bash
# Test on local first
ENVIRONMENT=local alembic upgrade head

# Then development
ENVIRONMENT=dev alembic upgrade head

# Finally production (with backup)
ENVIRONMENT=prod alembic upgrade head
```

### Troubleshooting Migration Modifications

#### 1. "Revision abc123 not found"
```bash
# Check if migration file exists
ls migrations/versions/

# Check alembic history
alembic history

# If file missing, regenerate migration
alembic revision --autogenerate -m "Recreate missing migration"
```

#### 2. "Migration generates no changes"
```bash
# Ensure model changes are saved
cat src/database/equities/tables/company.py | grep -A5 "class Company"

# Check if models are imported in env.py
grep -r "Company" migrations/env.py

# Force revision creation
alembic revision -m "Manual migration" --autogenerate
```

#### 3. "Cannot rollback migration - data loss"
```bash
# Check what the rollback would do
alembic downgrade -1 --sql

# If data loss is expected, backup first
pg_dump equities-local > backup_before_rollback.sql

# Then proceed with rollback
alembic downgrade -1
```

#### 4. "Duplicate column/table errors"
```bash
# Check current database schema
psql -d equities-local -c "\d companies"

# Compare with expected model
# Manually create corrective migration if needed
alembic revision -m "Fix schema inconsistencies"
```

### Best Practices for Migration Modifications

1. **Never edit applied migrations** - Always create new ones
2. **Use descriptive messages** - Include what changed and why
3. **Test rollbacks** - Ensure downgrade() functions work correctly
4. **Document changes** - Add comments explaining complex migrations
5. **Review generated SQL** - Use `--sql` flag to see what will execute
6. **Backup before production** - Always backup before applying migrations

### Quick Commands for Migration Management

```bash
# Check current migration status
alembic current

# See pending migrations
alembic history --verbose

# Generate SQL without applying
alembic upgrade head --sql

# Apply specific migration
alembic upgrade abc123

# Rollback specific number of migrations
alembic downgrade -2

# Mark database as up-to-date without running migrations
alembic stamp head

# Create empty migration for manual changes
alembic revision -m "Manual schema changes"
```

## Troubleshooting

### Common Issues

#### 1. "Target database is not up to date"
```bash
# Check current status
alembic current

# Check if migrations exist
ls migrations/versions/

# Apply pending migrations
alembic upgrade head
```

#### 2. "Can't locate revision"
```bash
# Verify you're in the correct directory
pwd  # Should be: /path/to/Options-Deep/src/database/equities

# Check migration files exist
ls migrations/versions/

# Verify alembic.ini configuration
cat alembic.ini | grep script_location
```

#### 3. "Database connection failed"
```bash
# Check environment variables
echo $ENVIRONMENT
echo ${OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD:+Password is set}

# Test database connection manually for local environment
psql -h localhost -U e_user -d equities-local -c "SELECT 1;"

# For other environments, use appropriate usernames:
# psql -h dev-db-server.example.com -U dev_user -d equities-dev -c "SELECT 1;"
# psql -h prod-db-server.example.com -U prod_user -d equities-prod -c "SELECT 1;"
```

#### 4. "No module named 'src.config.database'"
```bash
# Ensure you're in project root for Python imports
cd /path/to/Options-Deep

# Set Python path if needed
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run from equities directory
cd src/database/equities
alembic upgrade head
```

#### 5. "Permission denied on database"
```bash
# Check database user permissions for e_user
psql -h localhost -U postgres -d postgres -c "SELECT rolname, rolsuper, rolcreatedb FROM pg_roles WHERE rolname = 'e_user';"

# Grant necessary permissions if needed
psql -h localhost -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE \"equities-local\" TO e_user;"

# Ensure schema permissions are set
psql -h localhost -U postgres -d "equities-local" -c "
GRANT ALL PRIVILEGES ON SCHEMA public TO e_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO e_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO e_user;
"
```

### Migration Issues

#### Generated migration is empty
- Verify Company model is properly defined in `src/database/equities/tables/company.py`
- Check that the model inherits from the correct Base class
- Ensure the model is imported in `migrations/env.py`

#### Migration fails during upgrade
- Review the generated migration file for syntax errors
- Check that the database user has CREATE TABLE permissions
- Verify no conflicting table names exist

#### Rollback issues
```bash
# Test rollback capability
alembic downgrade -1
alembic upgrade head

# If rollback fails, check the downgrade() function in migration file
```

## Next Steps

After successfully creating the companies table:

### 1. Test Model Integration
```python
# Test the Company model in Python
from src.database.equities.tables.company import Company
from src.data_sources.models.company import Company as CompanyDataModel

# Create test data model
test_company = CompanyDataModel(
    ticker="AAPL",
    company_name="Apple Inc.",
    exchange="NASDAQ",
    source="test"
)

# Convert to database model
db_company = Company.from_data_model(test_company)
print(f"Database model: {db_company}")
```

### 2. Add Data Population
- Set up data providers to populate the companies table
- Create scripts to import company data from NASDAQ or other sources
- Implement data validation and deduplication logic

### 3. Create Additional Tables
- Stock quotes table
- Historical price data table
- Company financials table

### 4. Environment Deployment
```bash
# Deploy to development environment
ENVIRONMENT=dev alembic upgrade head

# Deploy to production environment
ENVIRONMENT=prod alembic upgrade head
```

### 5. Monitoring and Maintenance
- Set up database monitoring
- Create backup procedures
- Plan for index maintenance and optimization

## Quick Reference

```bash
# Essential commands for companies table setup
cd src/database/equities
alembic current                                    # Check status
alembic revision --autogenerate -m "message"      # Create migration
alembic upgrade head                               # Apply migration
alembic history                                    # View history
alembic downgrade -1                               # Rollback one migration

# Environment variables
export ENVIRONMENT=local
export OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD=your_password

# Database connection test
psql -h localhost -U e_user -d equities-local -c "SELECT version();"
```

This completes the setup of the companies table in the equities database. The table is now ready for data population and integration with the Options Deep application.