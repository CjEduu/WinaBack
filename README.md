# Poker tournament replayer:

Poker tournament replayer done for personal use. It lets you traverse through hands with a VIM like motion.

This project is not by any means a feat of engineering but a test of the [Ralp Workflow](https://github.com/snarktank/ralph?), its fully developed by Claude Opus 4.5 and not revised by myself.


## How to use

Clone the repository:
```bash
git clone https://github.com/CjEduu/WinaBack.git
```

Use your favourite package manager to install the dependencies (we use [uv](https://docs.astral.sh/uv/)), on project root:
```bash
# Remove --no-dev if you want to develop this project
uv sync --no-dev
```

To run, simply run main.py:
```bash
uv run main.py
```

### Developing

We use tools like ruff, pyright and pytest for testing and format/typecheking:
- **Type Checking**: Run `uv run pyright src/ tests/`
- **Linting**: Run `uv run ruff check src/ tests/`
- **Testing**: Run `uv run pytest tests/ -v`

## Currently supported houses
- Winamax

