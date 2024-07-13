# Modules

```{toctree}
---
hidden:
---

afk
disabling
gsm_arena
languages
lastfm
medias
stickers
translator
users_groups
web
```

PyKorone's modules are a collection of commands grouped by functionality. Each module serves a specific purpose and provides commands to interact with the bot. These commands can take arguments to customize the output, with both mandatory and optional arguments detailed in each command's description.

## Understanding Command Arguments

When you see a command in the documentation, it may have one or more arguments that you need to provide. The arguments are enclosed in parentheses `()`, and some of them may be optional, indicated by a question mark `?` before the argument name. For example, the command `/command (user) (?text)` requires the `user` argument and has an optional `text` argument.

```{note}
**Argument Types:**

- `()`: Required argument.
- `(user)`: Required (user ID or username), but you can also reply to any user's message as an alternative.
- `(group)`: Required (group ID or username).
- `(? )`: Optional argument.
```

## Available Modules

Below is an overview of the modules available in PyKorone, along with a brief description of their functionalities:

- {doc}`AFK (Away From Keyboard) <afk>`: Enables you to set your status as AFK.
- {doc}`Disabling <disabling>`: Allows you to disable specific commands to prevent spam and abuse.
- {doc}`GSM Arena <gsm_arena>`: Fetches smartphone specifications from GSM Arena.
- {doc}`Languages <languages>`: Lets you change the bot's language.
- {doc}`LastFM <lastfm>`: Retrieves your LastFM scrobbles.
- {doc}`Medias <medias>`: Downloads media from various websites.
- {doc}`Stickers <stickers>`: Manipulates stickers and sticker sets.
- {doc}`Translator <translator>`: Translates text between languages using DeepL.
- {doc}`Users & Groups <users_groups>`: Fetches information about users and groups.
- {doc}`Web Tools <web>`: Retrieves information about IP addresses and domains.
