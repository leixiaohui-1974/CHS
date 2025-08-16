# Contributing to CHS-SDK

> **Note for Repository Maintainers:** This file should be moved to the root directory of the `chs-sdk` main code repository. It is included here in the knowledge hub for visibility and completeness.

---

Firstly, thank you for considering contributing to CHS-SDK! We welcome all forms of contribution, from fixing typos to implementing complex new features.

To maintain the quality and consistency of the codebase, we've established the following contribution guidelines.

## Table of Contents

- [Code Style](#code-style)
- [Submitting an Issue](#submitting-an-issue)
- [Pull Request (PR) Process](#pull-request-pr-process)
- [Contributing to the Documentation](#contributing-to-the-documentation)

## Code Style

To keep the code clean and consistent, we adhere to the following standards:

- **Python**: We follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide.
  - Use `black` for code formatting.
  - Use `isort` for sorting imports.
  - Use clear English for comments and docstrings.
- **Naming Conventions**:
  - Class names use `CamelCase`.
  - Function, method, and variable names use `snake_case`.
  - Private members are prefixed with a single underscore `_`.

Before submitting your code, please ensure you run the formatters.

```bash
pip install black isort
black .
isort .
```

## Submitting an Issue

If you find a bug, have a feature suggestion, or any other issue, please submit it via GitHub Issues.

Before submitting an issue, please:
1.  Search existing issues to ensure your problem hasn't been reported already.
2.  If it's a bug, provide as much detail as possible:
    -   Your OS and Python version.
    -   The version of CHS-SDK.
    -   A minimal, reproducible code example that triggers the bug.
    -   What you expected to happen, and what actually happened (including the full error traceback).

## Pull Request (PR) Process

We warmly welcome code and documentation improvements via Pull Requests (PRs).

1.  **Fork & Clone**: Fork the repository to your GitHub account and then clone it locally.
    ```bash
    git clone https://github.com/YOUR_USERNAME/chs-sdk.git
    ```
2.  **Create a Branch**: Create a new feature branch from the `main` branch. Please use a descriptive name for your branch (e.g., `feature/new-agent-type` or `fix/mpc-optim-bug`).
    ```bash
    git checkout -b feature/my-awesome-feature
    ```
3.  **Code**:
    -   Make your code changes.
    -   Add unit tests for your new features. Ensure all existing and new tests pass.
    -   Add clear docstrings to your code.
4.  **Format & Test**: Ensure your code conforms to our style guide and passes all tests.
    ```bash
    black .
    isort .
    pytest
    ```
5.  **Commit**: Write clear, concise commit messages. We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification.
    -   Example: `feat: Add ReinforcementLearningAgent with basic Q-learning`
    -   Or `fix: Correct state update logic in BodyAgent`
6.  **Push**: Push your branch to your fork.
    ```bash
    git push origin feature/my-awesome-feature
    ```
7.  **Create PR**: On GitHub, create a Pull Request from your feature branch to the `chs-sdk/main` branch.
    -   In the PR description, clearly explain what you did and why. If it resolves an issue, please link to it (e.g., `Closes #123`).
    -   Our team will review your PR and may suggest changes.

## Contributing to the Documentation

Our documentation (the CHS-Knowledge-Hub) is hosted in [its own repository](https://github.com/your-org/chs-knowledge-hub). If you wish to add new content or make corrections:
1.  Please follow a similar PR process in that repository.
2.  The documentation is written in Markdown.
3.  If you add a new tutorial or case study, please be sure to update the navigation links in the `mkdocs.yml` file.

Thank you for your contribution!
