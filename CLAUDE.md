# Development Guidelines

This document contains critical information about working with this codebase. Follow these guidelines precisely.

## Core Development Rules

1. Code Quality
   - Type hints required for all code
   - Functions must be focused and small
   - Follow existing patterns exactly

2. Testing Requirements
   - Framework: `uv run pytest`
   - Async testing: use anyio, not asyncio
   - Coverage: test edge cases and errors
   - New features require tests
   - Bug fixes require regression tests

3. Code Style
    - PEP 8 naming (snake_case for functions/variables)
    - Class names in PascalCase
    - Constants in UPPER_SNAKE_CASE
    - Document with docstrings
    - Use f-strings for formatting

## Development Philosophy

- **Simplicity**: Write simple, straightforward code
- **Readability**: Make code easy to understand
- **Performance**: Consider performance without sacrificing readability
- **Maintainability**: Write code that's easy to update
- **Testability**: Ensure code is testable
- **Reusability**: Create reusable components and functions
- **Less Code = Less Debt**: Minimize code footprint

## Coding Best Practices

- **Early Returns**: Use to avoid nested conditions
- **Descriptive Names**: Use clear variable/function names
- **Constants Over Functions**: Use constants where possible
- **DRY Code**: Don't repeat yourself
- **Functional Style**: Prefer functional, immutable approaches when not verbose
- **Minimal Changes**: Only modify code related to the task at hand
- **Function Ordering**: Define composing functions before their components
- **TODO Comments**: Mark issues in existing code with "TODO:" prefix
- **Simplicity**: Prioritize simplicity and readability over clever solutions
- **Build Iteratively** Start with minimal functionality and verify it works before adding complexity
- **Run Tests**: Test your code frequently with realistic inputs and validate outputs
- **Build Test Environments**: Create testing environments for components that are difficult to validate directly
- **Functional Code**: Use functional and stateless approaches where they improve clarity
- **Clean logic**: Keep core logic clean and push implementation details to the edges
- **File Organsiation**: Balance file organization with simplicity - use an appropriate number of files for the project scale

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

## Testing
- tests are created in the same sub-directories as the code
- test data is created in the @tests folder
- tests utilize `*_mock.py` files to mock out the data from `repos` and `data_sources`

