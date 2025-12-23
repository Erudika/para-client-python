![Logo](https://s3-eu-west-1.amazonaws.com/org.paraio/para.png)

# Python Client for Para

[![NuGet version](https://badge.fury.io/py/paralient.svg)](https://badge.fury.io/py/paraclient)
[![Join the chat at https://gitter.im/Erudika/para](https://badges.gitter.im/Erudika/para.svg)](https://gitter.im/Erudika/para)

## What is this?

**Para** was designed as a simple and modular backend framework for object persistence and retrieval.
It helps you build applications faster by taking care of the backend. It works on three levels -
objects are stored in a NoSQL data store or any old relational database, then automatically indexed
by a search engine and finally, cached.

This is the Python client for Para.

### Quick start

1. Use the [PyPI](https://pypi.python.org/pypi) package manager to install the Python client for Para:
```sh
$ pip3 install paraclient
```

2. Initialize the client with your access and secret API keys.
```python
from paraclient import ParaClient

paraclient = ParaClient('ACCESS_KEY', 'SECRET_KEY');
```

## Documentation

### [Read the Docs](https://paraio.org/docs)

## Development

This repository now relies on [uv](https://github.com/astral-sh/uv) for dependency management, builds, and publishing, and targets Python 3.9+.

1. Install uv by following the [official instructions](https://docs.astral.sh/uv/getting-started/installation/).
2. Create and update the local virtual environment with `uv sync`. This installs every dependency declared in `pyproject.toml` and pinned in `uv.lock` into `.venv/`. Add the `--extra test` flag if you need the Testcontainers-powered test suite dependencies.
3. Run the test suite or any other tooling via `uv run`, for example `uv run pytest`.
4. Build distributable artifacts with `uv build`; the command produces both the sdist and wheel in `dist/`.

When dependencies change, update the `[project]` section of `pyproject.toml`, then regenerate the lock file with `uv lock --upgrade`.

The test suite uses [Testcontainers](https://testcontainers.com/) to spin up the `erudikaltd/para:latest_stable` Docker image automatically, so ensure Docker is installed and the daemon is running before invoking `uv run python -m unittest`. You can override some environment variables (see `tests/test_paraclient.py`).

## Contributing

1. Fork this repository and clone the fork to your machine
2. Create a branch (`git checkout -b my-new-feature`)
3. Implement a new feature or fix a bug and add some tests
4. Commit your changes (`git commit -am 'Added a new feature'`)
5. Push the branch to **your fork** on GitHub (`git push origin my-new-feature`)
6. Create new Pull Request from your fork

For more information see [CONTRIBUTING.md](https://github.com/Erudika/para/blob/master/CONTRIBUTING.md)

## License
[Apache 2.0](LICENSE)
