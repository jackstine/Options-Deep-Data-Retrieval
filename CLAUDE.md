# Development Guidelines

This document contains critical information about working with this codebase. Follow these guidelines precisely.


## Core Components 

- the following are in the @src folder
   - **repos** - this will contain database repos to tables or collections that are peristant data stores.
   - **data_sources** - this will contain data sources that are external to our application, where we fetch data from third parties.
   - **cmd** - this will contain single driven commands and programs that the system will run.
      - **cmd/examples** - this will contain examples of the data_sources retrival code, it should not connect the data_sources to database, but could be used for checking the contents of a data_source and placing it in a file.
   - **utils** - this is where you can find DRY code for a lot of common functionality.
   - **database** - this where database is constructed using alembic.
   - **config** - this is where setting up configurations, environment variables, and the like are stored.
   - **pipelines** - merging the repos and the data_sources together using dependency injection to abstract the use of the data sources.
   - **algorithms** - used to define the algorithms of the project. Each algorithm has it's own sub folder.
   
## Testing
- **unittests** - unittests are written side by side their respective code.made along side the actual code base, is used with mocks to generate fast running tests. 
- **integration tests** - the `/tests` folder, *outside of src folder* is used for non-unit tests this will be integration and e2e tests.

### Unit Test
To run unit tests please run `make unit-test`.
#### Test Specific
`PYTHONPATH=. python -m unittest <file>`
#### Specific test method
`PYTHONPATH=. python -m unittest src.path.to.test_file.TestClassName.test_m`

## Environment Variables
- when adding environment variables you ***MUST*** ensure that you do the following
   - that you add them to `src/config/models/environment_variables.py`
   - that access to the environment variables goes through `src/config/configuration.py`
   - you update the `src/config/ENVIRONMENT.md` with a summary of the variable


## Static Type Checking
**Ensuyre you apply policy**. Please do not use type checking, unless you have been asked.

Run `python -m mypy <python_file>` to get the static type checking information.
Use this after writing to files to fix common missing behaviours please.

Run `uv run pyright <python_file>` to get more static typing checking information, and fix those issues as well.

## Common Packages
if you need information on SqlAlchemy please conduct context7 resource `https://context7.com/sqlalchemy/sqlalchemy`


## unit testing
to test a file in this repo,  you will need to set the `OPTIONS_DEEP_ENV=unittest`
ensure that it is always set to `unittest` this is a ***MUST***.
`export OPTIONS_DEEP_ENV=unittest && python -m unittest <file> -v`
