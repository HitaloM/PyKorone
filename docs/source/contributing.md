# Contributing

Every open source project thrives thanks to the generous help of contributors who sacrifice their time, and _PyKorone_ is no different. To ensure a pleasant experience for all participants, this project adheres to the [Code of Conduct](https://policies.python.org/python.org/code-of-conduct/) by the Python Software Foundation.

## Developing

Before making any changes to the code, you need to fork the project and clone it to your device. Additionally, familiarize yourself with creating a pull request. You can read more about pull requests in the [GitHub docs](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request).

Since this project is written in Python, ensure that you have Python installed (preferably the latest version) and a code editor like Visual Studio Code, PyCharm, or another editor of your choice.

### Setting Up the Project

_PyKorone_ uses Rye, which simplifies the setup process. Run the following command to install all dependencies in a virtual environment:

```bash
rye sync
```

Also, _PyKorone_ uses pre-commit hooks to run some checks automatically before committing. To install the pre-commit hooks, run:

```bash
rye run pre-commit install
```

### Finding Something to Do

If you already know what you'd like to work on, you can skip this section.

Otherwise, check the [issue tracker](https://github.com/HitaloM/PyKorone/issues) or the [pull requests](https://github.com/HitaloM/PyKorone/pulls) section to see if your idea has already been filed or is being worked on.

### Formatting the Code (Code Style)

To keep the code clean and organized, we use the Ruff formatter/linter. Run the following commands to format the code and fix any issues:

```bash
ruff format .
ruff check . --fix
```

Always run the linter before committing to ensure the code is clean and follows the [PEP 8](https://pep8.org/) guidelines. Aim to follow the best Python development practices.

### Documentation

If you are making changes to the documentation, preview the changes by running:

```bash
rye run live-docs
```

This starts a local server where you can preview your documentation changes in real-time.

### Describing Your Changes

Once you finish your changes, describe them clearly. This helps maintainers understand what you did and why. Refer to the [commit message guidelines](https://www.conventionalcommits.org/en/v1.0.0/) for writing good commit messages.

### Completing the Process

After making your changes, publish them to your repository, create a pull request, and wait for a review.

## Star on GitHub

If you enjoy the project, please star the [GitHub Repository](https://github.com/HitaloM/PyKorone). This helps increase the project's visibility and attract more contributors.
