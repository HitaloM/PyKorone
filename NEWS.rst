.. note

    You should *NOT* be adding new change log entries to this file, this
    file is managed by towncrier. You *may* edit previous change logs to
    fix problems like typo corrections or such.
    To add a new change log entry, please see
    https://towncrier.readthedocs.io/en/stable/tutorial.html#creating-news-fragments
    we named the news folder "news".
    WARNING: Don't drop the next directive!

.. towncrier release notes start

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
