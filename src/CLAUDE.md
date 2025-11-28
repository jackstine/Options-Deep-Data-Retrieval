## Development
### Core Development Rules

1. Code Quality
   - Type hints required for all code
   - Functions must be focused and small
   - Follow existing patterns exactly

2. Code Style
    - PEP 8 naming (snake_case for functions/variables)
    - Class names in PascalCase
    - Constants in UPPER_SNAKE_CASE
    - Document with docstrings
    - Use f-strings for formatting



### Coding Best Practices
Using TypeDicts and Dataclass are prefered.

#### TypeDicts
Do not return `dict[str, int]`  but instead return TypeDict classes that define the attributes please.

#### Dataclasses
using the `@dataclass`


## Environment Variables
- when adding environment variables you ***MUST*** ensure that you do the following
   - that you add them to `src/config/models/environment_variables.py`
   - that access to the environment variables goes through `src/config/configuration.py`
   - you update the `src/config/ENVIRONMENT.md` with a summary of the variable


## Useful resources
### testcontainers-python
use the context7 https://context7.com/testcontainers/testcontainers-python for more information, when working with `testcontainers-python`.
### pytest
use the context7 https://context7.com/pytest-dev/pytest for more information, when working with `pytest`.

