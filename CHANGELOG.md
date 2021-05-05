# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),

## [1.3.0] - 2021-04-17

### Added

- `rt` filter (Reply to someone's message with "rt").

### Removed

- `/tuxsay` command.
- `/cowsay` command.
- `/daemonsay` command.
- `/f` command.
- `Cowpy` dependency.
-  Korone pypi package support (not available anymore).

### Changed

- `/echo` command available for sudo only.
- Using a fork of `wikipedia` dependency (maybe faster).
- Replaced the `/bing` and `/search` commands with `/duckgo`. (less problematic and faster).
- Improved `interaction.py` to decrease duplicate code.
- Using two decorators for `help_c` in `help.py`

## [1.2.0] - 2021-04-07

### Added

- Anime character search with `/character` command.
- sed/regex command `s/`.

### Removed

- Removed the check of SpamWatch banneds in welcome.

### Changed

- Added button to do new search in anime/manga message from inline.
- Added "type" in the inline anime search title.
- Pass errors in a better way in `/google` and `/bing` commands.

## [1.1.5] - 2021-04-05

### Added

- Added the /mcserver command to view information about a Minecraft server.
- Added `/spacex` command

### Changed

- Airing time in the `/airing` command will now show the remaining time to display.

### Removed

- Removed HTML tags in the anime/manga search in the inline.

## [1.1.0] - 2021-03-27

### Added

- Defined useful information in init and importing to the text of the `/about` command.
- Added license, copyright, Pyrogram version and Korone version in bot startup header.
- Implemented the `/ytdl` command to download videos and audios from YouTube using youtube-dl.
- Added the wheel package as a requirement.
- Added the `/tr` command for text translation using `gpytranslate`.
- Added command to encode a text with base64 and a command to decode base64.
- Added a command for sending an empty message.
- Added a command to generate fake play Store style codes.
- Added inline commands.
- New filters have been added. 

### Changed

- Now using a single httpx session for better performance. (the session closes whenever the bot is shut down)
- Performance improvements to the `/stickers` command (more noticeable on low-end devices).
- Returning to the old wikipedia command.
- Texts of the `/pypi` command translated into the language of the bot.

### Fixed

- Fixed bug that resulted in duplicate results in the `/stickers` command.

## [1.0.0] - 2021-03-24

### Added

- First release
