# Change Log

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

- Airing time in the `/airing` command will now show the remaining time to display.
- Removed HTML tags in the anime/manga search in the inline.
- Added the /mcserver command to view information about a Minecraft server.
- Added `/spacex` command
- Minor improvements and fixes

## [1.1.0] - 2021-03-27

- Defined useful information in init and importing to the text of the `/about` command.
- Added license, copyright, Pyrogram version and Korone version in bot startup header.
- Now using a single httpx session for better performance. (the session closes whenever the bot is shut down)
- Implemented the `/ytdl` command to download videos and audios from YouTube using youtube-dl.
- Performance improvements to the `/stickers` command (more noticeable on low-end devices).
- Fixed bug that resulted in duplicate results in the `/stickers` command.
- Added the wheel package as a requirement.
- Added the `/tr` command for text translation using `gpytranslate`.
- Added command to encode a text with base64 and a command to decode base64.
- Added a command for sending an empty message.
- Added a command to generate fake play Store style codes.
- Returning to the old wikipedia command.
- Texts of the `/pypi` command translated into the language of the bot.
- Added inline commands.
- New filters have been added.
- Code improvements
- Other fixes

## [1.0.0] - 2021-03-24

- First release
