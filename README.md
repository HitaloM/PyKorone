# PyKorone

[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/AmanoTeam/PyKorone.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/AmanoTeam/PyKorone/context:python)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/75894dccef324798b452791297624e0a)](https://app.codacy.com/gh/AmanoTeam/PyKorone?utm_source=github.com&utm_medium=referral&utm_content=AmanoTeam/PyKorone&utm_campaign=Badge_Grade_Settings)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![GitHub contributors](https://img.shields.io/github/contributors/AmanoTeam/PyKorone.svg)](https://GitHub.com/AmanoTeam/PyKorone/graphs/contributors/)

> An interaction and fun bot for Telegram groups, having some useful and other useless commands.
> Created as an experiment and learning bot but being expanded and improved over time.

This repository contains the source code of [@PyKoroneBot](https://t.me/PyKoroneBot) Telegram bot, along with instructions for hosting your own instance.

## Requirements

- Python 3.6 or higher.
- A [Telegram API Key and API Hash](https://docs.pyrogram.org/intro/setup#api-keys).
- A [Telegram Bot Token](https://t.me/botfather).
- A Linux distribution (should also work on Windows but has not been tested).

## Installation

### Setup

First, clone this Git repository locally:
`git clone https://github.com/AmanoTeam/PyKorone`

After that, you can run `python3 -m pip install .` to install the bot along with the dependencies.

#### Error: `Directory '.' is not installable. File 'setup.py' not found.`

This common error is caused by an outdated version of pip. We use the Poetry
package manager to make things easier to maintain, which works with pip through
PEP-517. This is a relatively new standard, so a newer version of pip is necessary
to make it work.

Upgrade to pip 19 or later to fix this issue: `python3 -m pip install pip -U`

## Usage

To start the bot, type `python3 -m korone`.

## Special thanks

- [@usernein](https://github.com/usernein) - teachings, ideas and allowed me to use some of his codes.
- [@AndrielFR](https://github.com/AndrielFR) - helped me in great things.
- [@RianFC](https://github.com/RianFC) - granted permission for the port of [ytdl.py](https://t.me/UserLixoPlugins/78) to the Korone.

_If there is anyone I have forgotten to mention please let me know on Telegram: [@Hitalo](https://t.me/Hitalo)_

## License

[GPLv3](https://github.com/AmanoTeam/PyKorone/blob/main/LICENSE) © 2021 [AmanoTeam](https//github.com/AmanoTeam)
