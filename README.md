# opensettlenet-common

## Installation
Using `pip`: `$ pip install git+https://github.com/OpenSettleNet/common.git`
Using `poetry`: `$ poetry add git+https://github.com/OpenSettleNet/common.git`

## Development
### Install [`pyenv`](https://github.com/pyenv/pyenv)
```commandline
brew update
brew install openssl readline sqlite3 xz zlib tcl-tk
brew install pyenv
```

#### [Postinstall steps](https://github.com/pyenv/pyenv#set-up-your-shell-environment-for-pyenv)
```commandline
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
```

### Install Python 3.10
```commandline
pyenv install 3.10
pyenv local 3.10
```

### Install [`pipx`](https://github.com/pypa/pipx)
```commandline
brew install pipx
pipx ensurepath
```

### Install [`poetry`](https://python-poetry.org)
```commandline
pipx install poetry
```

(Technically, you can skip `pipx` and run `pip install poetry`.)

Henceforth, you're going to run anything you want to have access to the Python environment via `poetry run` — e.g. `poetry run python`.

### Install [`black`](https://pypi.org/project/black/)

```commandline
pip install "black[d]"
```

(We install `black` with the `[d]` option so that the `blackd` daemon is available.)

### Set up `opensettlenet-common` development environment
```commandline
poetry install
```

### Install pre-commit hooks
```commandline
poetry run pre-commit install
```

(If you ever need to skip the pre-commit hooks, run `git commit` with `--no-verify`.)

### Running tests
`pytest` will have been installed via Poetry, so just run `poetry run pytest`.

### Running mypy
`poetry run mypy opensettlenet`

### Recommended post-install steps for PyCharm

Make sure that PyCharm is configured to use the project's Poetry environment.

Install the `Mypy` and `BlackConnect` PyCharm plugins, and configure `BlackConnect` to run on save.
