# Contributing

Thanks for helping improve `geo-audit-flow`.

## Local Setup

```bash
git clone https://github.com/your-org/geo-audit-flow.git
cd geo-audit-flow
pip install -e ".[dev]"
python scripts/make_sample_data.py
```

## Development Checks

Run these before opening a pull request:

```bash
ruff check .
mypy src
pytest
```

## Pull Request Guidelines

- Keep changes focused and explain the user-facing impact.
- Add or update tests for behavior changes.
- Update docs when configuration, CLI behavior, checks, or outputs change.
- Avoid large external datasets; use small synthetic fixtures.

## Code Style

The project uses Ruff for linting and import sorting, mypy for static checks, and pytest for tests. Prefer small, typed functions and clear error messages over clever abstractions.
