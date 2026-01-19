# 🤖 Sophie Telegram Bot

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Sophie is a modern, fast, and feature-rich Telegram chat manager bot built with [aiogram 3](https://github.com/aiogram/aiogram). It's designed to be modular, scalable, and easy to extend.

## ✨ Features

- **🛡️ Advanced Moderation:** Ban, mute, warn, and report systems.
- **🌍 Internationalization:** Multi-language support via Gettext and Crowdin.
- **⚙️ Microservices Architecture:** Separate modes for Bot, REST API, and Scheduler.
- **🗄️ Database:** Uses MongoDB with Beanie ODM for persistence.
- **🚀 High Performance:** Powered by `uv`, `ujson`, and `redis`.
- **🛠️ In-house Libraries:**
    - [ASS](https://gitlab.com/SophieBot/ass) — Argument Searcher of Sophie.
    - [STFU](https://gitlab.com/SophieBot/stf) — Sophie Text Formatting Utility.

## 📋 Requirements

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** (modern package manager)
- **MongoDB** (data storage)
- **Redis / Valkey** (caching and FSM)

### OS-specific Dependencies (e.g., openSUSE)

To build some dependencies, you might need:
`libicu-devel`, `gcc-c++`, `python313-devel`, `gcc13`

## 🚀 Quick Start

### 1. Installation

Clone the repository and install dependencies using `uv`:

```bash
git clone https://gitlab.com/SophieBot/sophie.git
cd sophie
make pull_libs
uv sync
```

### 2. Configuration

Copy the example environment file and edit it:

```bash
cp data/config.example.env data/config.env
# Edit data/config.env with your credentials (TOKEN, USERNAME, etc.)
```

### 3. Running Sophie

Sophie can be started in different modes depending on your needs.

#### 🤖 Bot Mode (Main)
```bash
# Standard
uv run python -m sophie_bot
# Development with hot-reload
make dev_bot
```

#### 🌐 REST API Mode
```bash
# Standard
MODE=rest uv run python -m sophie_bot
# Development with hot-reload
make dev_rest
```

#### 📅 Scheduler Mode
```bash
# Standard
MODE=scheduler uv run python -m sophie_bot
# Development with hot-reload
make dev_scheduler
```

## 🛠️ Development

We use `make` for common development tasks.

- **Check everything:** `make commit` (runs formatters, linters, tests, and generates docs)
- **Format code:** `make fix_code_style`
- **Sync libraries:** `make sync_libs` (reinstalls ASS/STFU)
- **Run tests:** `make run_tests`
- **Type checking:** `make test_codeanalysis`
- **Translations:** `make locale`

## 📖 Documentation

- **Wiki:** [https://sophie-wiki.orangefox.tech/](https://sophie-wiki.orangefox.tech/)
- **Self-hosting Guide:** See [wiki_docs/Self-hosting.md](wiki_docs/Self-hosting.md)

## ⚖️ License

Sophie is licensed under the **GNU AGPLv3**. See [LICENSE](LICENSE) for more details.
