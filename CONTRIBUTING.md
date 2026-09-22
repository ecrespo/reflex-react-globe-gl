# Contributing

Thanks for wanting to improve `reflex-react-globe-gl`.

## Branching

- `main` — released code. Protected; changes land only through a pull request.
- `develop` — integration branch. Target your pull requests here.

## Setup

```bash
git clone git@github.com:ecrespo/reflex-react-globe-gl.git
cd reflex-react-globe-gl
uv sync --all-extras
```

That installs the package in editable mode, so edits under `custom_components/` are picked
up by the demo app without reinstalling.

## Running the demo

```bash
cd react_globe_gl_demo
uv run reflex run
```

## Before you push

```bash
uv run ruff check --fix custom_components tests react_globe_gl_demo
uv run ruff format custom_components tests react_globe_gl_demo
uv run pytest
uv run bandit -c pyproject.toml -r custom_components
```

The JS tests in `tests/test_wrapper_js.py` run `globe_wrapper.js` under Node and **skip
silently** if Node is not installed. CI installs Node, so a change that only breaks under
Node will be caught there — but install Node locally if you touch the wrapper.

## Type stubs

`custom_components/reflex_react_globe_gl/react_globe_gl.pyi` is generated, and CI fails if it
is stale. Regenerate it after changing any prop or event:

```bash
PYTHONPATH=. uv run reflex component build
```

`PYTHONPATH=.` is required. Without it the stub generator cannot import the modules by
dotted path, prints `Failed to import ...` for every file, and still exits successfully —
leaving the stub silently unchanged.

## Adding a prop

1. Add the `Var` field to `Globe` in `react_globe_gl.py` with a `doc=` string.
2. If the prop needs wrapper-side handling (accessor stability, sanitization, an imperative
   call), update `globe_wrapper.js`.
3. Add the upstream camelCase name to `UPSTREAM_PROPS` in `tests/test_component.py` so the
   coverage test keeps asserting parity with `react-globe.gl`.
4. Regenerate the stubs.

## Commits and releases

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/).

Releases are cut from `main`: bump `version` in `pyproject.toml`, add a `CHANGELOG.md`
section, then tag `vX.Y.Z`. The `Release` workflow verifies the tag matches the project
version, runs the full gate, publishes to PyPI via Trusted Publishing and creates the
GitHub Release.
