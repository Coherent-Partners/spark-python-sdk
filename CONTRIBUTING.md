# How to Contribute

These are a few guidelines that contributors need to follow to keep things easy.

## Getting Started

- Create a branch or fork the repository
- Check out the [Developer Guide](#developer-guide) below for setup instructions
- Add your functionality or fix a bug
- Ensure that your changes pass the tests
- Only refactoring and documentation changes require no new tests.
- Only pull requests with passing tests will be accepted.

## Submitting Changes

- Push your changes to your branch/fork.
- Submit a pull request.

## Additional Resources

- [General GitHub documentation](http://help.github.com/)
- [GitHub pull request documentation](http://help.github.com/send-pull-requests/)

---

## Developer Guide

As a developer, you should be aware of the following:

- Linting and formatting with `ruff` and `pyright`
- Testing with `pytest`
- CI/CD with [GitHub Actions](https://docs.github.com/en/actions/quickstart)

### Code Quality

[Ruff](https://docs.astral.sh/ruff/linter/) is used to lint and format the codebase.

### Rye

[Rye](https://rye-up.com/) is used for virtual environments, dependency management
and packaging. The `rye` setup is located in the `rye` field of `pyproject.toml`.

### Unit Testing

[Pytest](https://docs.pytest.org/en/stable/) is used for unit testing. The tests are
located in the `test` directory.

### Installation and Devtools

Using `rye` as the package manager, you may run the following commands:

```bash
# build virtual environment and install dependencies
rye sync

# lint code
rye run lint

# test code
rye test

# build code
rye build --clean
```

To run an example, you will need to follow the instructions in the
[examples/README.md](./examples/README.md) file, then run the following command:

```bash
yarn demo
```

> **Disclaimer:** This project is inspired by many open source SDKs and libraries.
> Among them are [openai-python] and [box-python-sdk]. So, big kudos to the developers
> behind these projects.

[openai-python]: https://github.com/openai/openai-python
[box-python-sdk]: https://github.com/box/box-python-sdk
