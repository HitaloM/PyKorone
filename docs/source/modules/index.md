# Modules

```{toctree}
---
hidden:
---

afk
disabling
filters
gsm_arena
languages
lastfm
medias
minecraft
piston
regex
stickers
translator
users
weather
web
```

_PyKorone_'s modules are a collection of commands grouped by functionality. Each module serves a specific purpose and can provides commands to interact with the bot. This section will introduce you to the available modules and how to use them.

## Understanding Command Arguments

When you see a command in the documentation, it may have one or more arguments that you need to provide. The arguments are enclosed in parentheses `()`, and some of them may be optional, indicated by a question mark `?` before the argument name. For example, the command `/command (user) (?text)` requires the `user` argument and has an optional `text` argument.

```{admonition} **Argument Types:**
:class: seealso

- `()`: Required argument.
- `(user)`: Required (user ID or username), but you can also reply to any user's message as an alternative.
- `(? )`: Optional argument.
```

## Available Modules

Below is a list of all available modules in _PyKorone_:

- [AFK (Away From Keyboard)](./afk): Sets you as away from keyboard and notifies users who mention you.
- [Disabling](./disabling): Allows you to disable specific commands to prevent spam and abuse.
- [Filters](./filters): Create custom commands to send predefined messages.
- [GSM Arena](./gsm_arena): Get smartphone specifications from GSM Arena.
- [Languages](./languages): Lets you change the bot's language.
- [LastFM](./lastfm): Get your LastFM scrobbles.
- [Medias](./medias): Downloads media from various websites automatically.
- [Minecraft](./minecraft): Get information about Minecraft servers and Modrinth projects.
- [Piston](./piston): Run code snippets using the [Piston API](https://github.com/engineer-man/piston)
- [Regex](./regex): Test regular expressions.
- [Stickers](./stickers): Steal stickers from sticker packs.
- [Translator](./translator): Translate text to different languages using DeepL.
- [Users](./users): Fetches information about Telegram and _PyKorone_ users.
- [Weather](./weather): Get weather information for a specific location.
- [Web Tools](./web): Get information about IP addresses and domains.
