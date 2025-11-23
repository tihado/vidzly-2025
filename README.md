# Vidzly

If you're a micro-influencer with zero skills or gear, Vidzly is your free pass.

Just drop us your raw clip and your vibe. We handle the rest, transforming it into a scroll-stopping 30-second hit. Zero effort for you, guaranteed.

Release date: 30/11.

## Setup

This project uses [Poetry](https://python-poetry.org/) for dependency management.

### Installing Poetry

If you don't have Poetry installed, you can install it using:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Or on macOS with Homebrew:

```bash
brew install poetry
```

### Installing Dependencies

Once Poetry is installed, install the project dependencies:

```bash
poetry install
```

This will create a virtual environment and install all dependencies specified in `pyproject.toml`.

### Activating the Virtual Environment

To activate the Poetry virtual environment:

```bash
poetry shell
```

Alternatively, you can run commands within the virtual environment without activating it:

```bash
poetry run <command>
```

### Adding Dependencies

To add a new dependency:

```bash
poetry add <package-name>
```

To add a development dependency:

```bash
poetry add --group dev <package-name>
```

### Removing Dependencies

To remove a dependency:

```bash
poetry remove <package-name>
```

### Updating Dependencies

To update all dependencies to their latest compatible versions:

```bash
poetry update
```

### Contributors
- 🐱 [honghanhh](https://github.com/honghanhh)🐱
- 🦊 [nvti](https://github.com/nvti)🦊 
- 🐻 [Nlag](https://github.com/NLag)🐻
- 🐰 [DaphneeCh](https://github.com/DaphneeCh)🐰