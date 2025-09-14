# RomShelf

A ROM management application for organizing retro game collections.

## Requirements

- Python 3.13+

## Installation

```bash
uv sync
```

## Usage

```bash
uv run python run.py
```

## Features

- Multi-platform ROM support (N64, Game Boy, GBA, PS1)
- Archive support (ZIP, 7Z, RAR)
- Clean Qt interface
- Platform filtering and search

## Development

```bash
# Lint
uv run ruff check src/

# Type check
uv run mypy src/
```