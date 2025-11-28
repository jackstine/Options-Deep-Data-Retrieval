We use Alembic to do database migrations

***From project root***
Ensure that you append `export OPTIONS_DEEP_ENV=local` or you will get error when making calls to `alembic`.
Only apply `OPTIONS_DEEP_ENV=local` when generating new revisions.
`alembic -c src/database/equities/alembic.ini current`                        # Check status
`alembic -c src/database/equities/alembic.ini history`                        # View history
`alembic -c src/database/equities/alembic.ini upgrade head`                   # Apply migrations
`alembic -c src/database/equities/alembic.ini revision -m "<revision_name>"`  # creates a new revision for migration

### Setting up environment variables
If you get an error mentioning `OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD` 
it most likely means you are not setting `OPTIONS_DEEP_ENV` correctly.



