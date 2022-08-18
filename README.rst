==================================
Korone - Telegram Bot |beta badge|
==================================

.. danger::
    This version is still in development!

.. image:: https://app.codacy.com/project/badge/Grade/4c935499b3d74d89935ae4460db05537
    :target: https://www.codacy.com/gh/AmanoTeam/PyKorone/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=AmanoTeam/PyKorone&amp;utm_campaign=Badge_Grade

.. image:: https://badges.crowdin.net/pykorone/localized.svg
    :target: https://crowdin.com/project/pykorone
    :alt: Crowdin

.. image:: https://img.shields.io/badge/telegram-korone-blue.svg
    :target: https://t.me/PyKoroneBot
    :alt: PyKorone on Telegram

.. image:: https://img.shields.io/badge/License-BSD_3--Clause-orange.svg
    :target: https://opensource.org/licenses/BSD-3-Clause
    :alt: BSD 3-Clause License

**PyKorone** is a modern and fully asynchronous Telegram bot to
improve you Telegram experience, written in Python3 using
`Pyrogram <https://gihub.com/Pyrogram/Pyrogram>`_.

How to contribute
=================
Every open source project lives from the generous help by contributors that sacrifices their time and PyKorone is no different.

Translations
------------
Translations should be done in our `Crowdin Project <https://crowdin.com/project/pykorone>`_,
as Crowdin checks for grammatical issues, provides improved context about the string to be translated and so on,
thus possibly providing better quality translations. But you can also submit a pull request if you prefer to translate that way.

Bot setup
---------
Below you can learn how to set up the PyKorone project.

Requirements
~~~~~~~~~~~~
- Python 3.9+.
- An Unix-like operating system (Windows isn't supported).

Instructions
~~~~~~~~~~~~
1. Create a virtualenv (This step is optional, but **highly** recommended to avoid dependency conflicts)

   - ``python3 -m venv .venv`` (You don't need to run it again)
   - ``. .venv/bin/activate`` (You must run this every time you open the project in a new shell)

2. Install dependencies from the pyproject.toml with ``python3 -m pip install . -U``.

   - Use ``python3 -m pip install .[fast] -U`` to install optional dependencies.

3. Go to https://my.telegram.org/apps and create a new app.
4. Create a new ``config.toml`` file from the ``config.toml.sample`` file (``cp config.toml.sample config.toml``).
5. Place your token, IDs and api keys to your ``config.toml`` file.

Tools and tips
~~~~~~~~~~~~~~

- Use `black <https://github.com/psf/black>`_ and `isort <https://github.com/PyCQA/isort>`_
- Use `flake8 <https://pypi.org/project/flake8/>`_ to lint your code.
- Use `mypy <https://pypi.org/project/mypy/>`_ to type-check your code.
- Don't forget to add the `SPDX-License-Identifier <https://spdx.dev/ids/>`_ header.
- Try to resolve any problems identified by our CI.

.. |beta badge| image:: https://img.shields.io/badge/-beta-red
  :alt: Beta badge
