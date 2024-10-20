.. note

    You should *NOT* be adding new change log entries to this file, this
    file is managed by towncrier. You *may* edit previous change logs to
    fix problems like typo corrections or such.
    To add a new change log entry, please see
    https://towncrier.readthedocs.io/en/stable/tutorial.html#creating-news-fragments
    we named the news folder "news".
    WARNING: Don't drop the next directive!

.. towncrier release notes start

1.1.5 (2024-10-20)
==================

Features
--------

- Added support for TikTok URLs with the `vt` subdomain in the automatic media download feature.
- Enhanced support for Threads and BlueSky thumbnails: PyKorone now automatically resizes images to meet Telegram's requirements.

Bug Fixes
---------

- Fix a validation error in the Twitter automatic media download that was causing the process to fail.
- Fixed an issue where the automatic media download was downloading the incorrect TikTok video. Now, the bot will not download the video.

1.1.4 (2024-10-12)
==================

Features
--------

- Ensure the bot checks for admin privileges before executing `/cleanup` command.
- Prevent caching of `/piston` command results to avoid returning incorrect outputs.
- Rewritten the Instagram download feature to utilize a new API, enhancing the reliability of the download process.

Bug Fixes
---------

- Fixed `/ytdl` command, which was broken due to a recent change in the YouTube API.

1.1.3 (2024-09-13)
==================

Bug Fixes
---------

- Fixed a bug where the bot did not respond to the `/lfmcollage` command if one of the albums in the collage lacked a cover.
- Fixed an error that occurred when the result of `/piston` evaluation exceeded the 4096-character limit for Telegram messages.
- Resolved an issue where some Instagram reels were not being downloaded by the automatic media downloader.

1.1.2 (2024-09-12)
==================

Features
--------

- Added support for automatic video downloads from BlueSky, allowing PyKorone to seamlessly download videos from the platform.

Bug Fixes
---------

- Fixed incorrect HTML escaping that caused formatting issues in the captions of media sent by the automatic media downloader.

1.1.1 (2024-09-10)
==================

Bug Fixes
---------

- Fixed an issue where `/piston` would raise error when processing code containing blank lines at the start. Also fixed an error when only the language of the code snippet was provided.
- Fixed an issue where the `/filtersinfo` command would raise error when fetching information about filters.
- Fixed an issue where the filters module would raise error when processing messages containing emojis.

Improved Documentation
----------------------

- Added a better documentation of how to format Filters messages with HTML tags, buttons and filings, take a look :doc:`here <modules/formatting>`.

1.1.1 (2024-09-10)
==================

Bug Fixes
---------

- Fixed an issue where `/piston` would raise error when processing code containing blank lines at the start. Also fixed an error when only the language of the code snippet was provided.
- Fixed an issue where the `/filtersinfo` command would raise error when fetching information about filters.
- Fixed an issue where the filters module would raise error when processing messages containing emojis.

Improved Documentation
----------------------

- Added a better documentation of how to format Filters messages with HTML tags, buttons and filings, take a look :doc:`here <modules/formatting>`.

1.1.0 (2024-09-10)
==================

Features
--------

- Added support to Threads and BlueSky at automatic media download.
- Added the :doc:`Filters Module <modules/filters>`, allowing the creation, management and application of text and media filters. (`#261 <https://github.com/HitaloM/PyKorone/issues/261>`_)
- Added the :doc:`Piston Module <modules/piston>` with commands to run code snippets through the bot. (`#263 <https://github.com/HitaloM/PyKorone/issues/263>`_)
- Added the :doc:`Minecraft Module <modules/minecraft>` with commands to get information about Minecraft servers and Modrinth projects. (`#264 <https://github.com/HitaloM/PyKorone/issues/264>`_)

Bug Fixes
---------

- Fixed a bug that displayed the LastFM artist's name incorrectly when the bot warned that the user mentioned is AFK.
- Some improvements have been made to the Instagram medias download, reels that weren't downloading before should now download.
- fixed the list of commands in Telegram menu not appearing for english users.

1.0.6 (2024-08-23)
==================

Bug Fixes
---------

- Dealing with cases where the text to be translated by `/tr` was empty, which caused the bot to crash.
- Fixed an error encountered during the TikTok media data search, causing the bot to just not respond to the request.
- Fixed problems with migrating groups to supergroups in the database, where the bot would crash if the group was not in the database and was converted to a supergroup.

1.0.5 (2024-08-21)
==================

Removals
--------

- If the bot crashes, it will no longer display the detailed error message. This change has been made for security reasons to prevent leaking sensitive content.

Features
--------

- Enhanced the `/device` command to optimize the processing of GSM Arena data, resulting in improved performance and increased stability. (`#258 <https://github.com/HitaloM/PyKorone/issues/258>`_)

Bug Fixes
---------

- Fixed a crash issue that occurred when the bot encountered invalid TikTok URLs or experienced HTTP request timeouts.
- Fixed an issue where downloading TikTok slideshows would result in an error if the slideshow did not have a music.
- Update the `/start` command text for group chats. Previously, the bot used the same text as in private chats, which caused confusion due to references to buttons that are not available in group chats.

1.0.4 (2024-08-16)
==================

Features
--------

- Added validation to the `/kang` command to ensure videos comply with Telegram's sticker requirements. Videos must meet specific duration and size constraints before further processing.

Bug Fixes
---------

- Fixed a crash when the bot attempted to download TikTok media from messages containing text in addition to the URL. The bot now correctly identifies and processes the TikTok URL even with extra text.
- Fixed an error in LastFM when a track, album, or artist did not have an image.
- Fixed an issue that prevented the bot from downloading media from tweets of profiles without a banner image.
- Fixed an issue where the `/device` command failed for some devices, particularly older non-smart ones, resulting in an error message.
- Fixed an issue where the bot attempted to send more than 10 Instagram media items, causing an error due to Telegram's limit of 10 media items per message. The bot now ensures no more than 10 media items are sent per message, even if the Instagram post contains more than 10 items.

1.0.3 (2024-08-14)
==================

Bug Fixes
---------

- Updated the username validation regex to allow underscores (_) in LastFM usernames, ensuring users can set their usernames without issues.
- Fixed a ValidationError caused by tweets without view counts, allowing such tweets to be processed correctly without causing crash.

Improved Documentation
----------------------

- Enhanced the changelog structure and language for better clarity and user understanding of recent updates.

1.0.2 (2024-08-13)
==================

Features
--------

- If the bot is restricted to send messages in certain chats, it will now automatically leave those chats to avoid any problems.

Bug Fixes
---------

- We've made sure that if the bot runs into certain technical issues, it will handle them quietly without crashing.
- We fixed a connection issue that sometimes happened when interacting with Instagram, so the bot should connect more reliably now.
- We also corrected a problem where the bot might have crashed if it didn’t receive a message as expected. Now, it will keep running smoothly.

1.0.1 (2024-08-12)
==================

Bug Fixes
---------

- Fixed a bug where the bot would try to add a user to the database even if they already existed. This caused some random crashes in group chats.

1.0.0 (2024-08-12)
===================

- Initial project release.
