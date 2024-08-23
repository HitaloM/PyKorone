.. note

    You should *NOT* be adding new change log entries to this file, this
    file is managed by towncrier. You *may* edit previous change logs to
    fix problems like typo corrections or such.
    To add a new change log entry, please see
    https://towncrier.readthedocs.io/en/stable/tutorial.html#creating-news-fragments
    we named the news folder "news".
    WARNING: Don't drop the next directive!

.. towncrier release notes start

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
