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
   - **algorithms** - used to define the algorithms of the project.
   
- test information
   - **unittests** - unittests are written side by side their respective code.made along side the actual code base, is used with mocks to generate fast running tests. 
   - **integration tests** - the `/tests` folder, *outside of src folder* is used for non-unit tests this will be integration and e2e tests.

## Testing
### Unit Test
To run unit tests please run `make unit-test`.
#### Test Specific
`PYTHONPATH=. python -m unittest <file>`
#### Specific test method
`PYTHONPATH=. python -m unittest src.path.to.test_file.TestClassName.test_m`

### Integration Tests
for integration tests,  please read the `