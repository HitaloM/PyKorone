You can keep your members from getting out of control using this feature!

## Available commands
For all user-specific commands on this page, you can either supply a @username, a user ID, or reply to the message of said user.

## General (Admins)
- `/warn (?user) (?reason)` – Warns a user
Use this command to warn the user! you can mention or reply to the offended user and add reason if needed.

**Example: `/warn @JeePee Learn how to use Markdown`**

- `/delwarns` or `/resetwarns`: This command is used to delete all the warns user got so far in the chat
**Example: /delwarns @username**

## Warn limt (Admins)
- `/warnlimit (new limit)`: Sets a warn limit
Not all chats want to give same maximum warns to the user, right? This command will help you to modify default maximum warns. Default is 3.

**Example: `/warnlimit 6`**

The new warnlimit should be greater than 1 and less than 10,000.

## Warn action (Admins)
- `/warnaction (mode) (?time)`
Well again, not all chats want to ban (default) users when exceed maximum warns so this command will able to modify that.

The currently supported actions are:
- `ban` (default) – Bans the user
- `mute` – Mutes the user
- `tmute` – Temporarily mutes the user
The tmute mode requires a time argument, as you guessed (see below).

**Example:**
- `/warnaction tmute 20m` this will mute user for 20 minutes.
- `/warnaction` ban bans the user.

## Available for all users
- `/warns (?user)` – Lists warns of a user
Use this command to see number of warns and information about warns, which a user received in the chat.

For the (user) argument, you can either specify a @username, a user ID, or you can reply to a message from another user.
To see your own warns, don't specify the user argument.

**Example: `/warns @username` or just `/warns` (for yourself)**
