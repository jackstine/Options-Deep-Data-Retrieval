We use Alembic to do database migrations

***From project root***
`alembic -c src/database/equities/alembic.ini current`    # Check status
`alembic -c src/database/equities/alembic.ini history`    # View history
`alembic -c src/database/equities/alembic.ini upgrade head`  # Apply migrations

