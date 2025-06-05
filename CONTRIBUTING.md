# Contributing to LangGraphBook

Thank you for considering contributing to this project!

## Issues and Pull Requests

- Use the GitHub [issue tracker](https://github.com/yourorg/langgraphbook/issues) to report bugs or request features.
- Fork the repository and create a feature branch for your changes.
- Submit a pull request with a clear description of the change.

## Code Style

We use the configuration in [pyproject.toml](BookLLM/pyproject.toml) along with `flake8` and `mypy` rules. Please run these linters before submitting your pull request.

## Running Tests

Install the dependencies and run:

```bash
pytest
```

## Updating Documentation

Documentation lives in the `docs/` directory. Build it locally with:

```bash
make docs
```

or directly with `sphinx-build`:

```bash
sphinx-build docs docs/_build
```

