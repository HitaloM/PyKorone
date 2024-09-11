# Formatting

Here you will find all the information you need to format your filters. This includes adding buttons, fillings, and more!

## HTML

You can use HTML tags to format your messages. This includes bold, italic, underline, and more! You can see a full list of supported tags [here](https://core.telegram.org/api/entities#allowed-entities).

```{tip}
You can reply with `/filter` to a message already formatted to copy the formatting!
```

## Fillings

You can also customise the contents of your message with contextual data. For example, you could mention a user by name in the message!

### Supported fillings:

- `{first}`: The user's first name.
- `{last}`: The user's last name.
- `{fullname}`: The user's full name.
- `{username}`: The user's username. If they don't have one, mentions the user instead.
- `{mention}`: Mentions the user with their firstname.
- `{id}`: The user's ID.
- `{userid}`: The user's ID.
- `{chatid}`: The chat's ID.
- `{chatname}`: The chat's name.
- `{chatnick}`: The chat's nickname.

### Examples

- Set a filter which uses the user's name through fillings:
  > `/filter hello Hello there {first}! How are you?`

- Set a filter which mentions the user and the chat:
  > `/filter hello Hello there {mention}! You are in {chatname}.`

## Buttons

Telegram offers a popular feature that allows you to add buttons to your welcome messages, notes, or filters. This module will guide you through everything you need to know!

### Examples

- To create a button labeled "Google" that opens google.com, use the following syntax:
  > `[Google](buttonurl://google.com)`

- To create two buttons ("Google" and "Bing") that appear on the same line, use the `:same` tag on the second button:
  > `[Google](buttonurl://google.com)`
  > `[Bing](buttonurl://bing.com:same)`

```{note}
Remember, buttons need to be saved in _PyKorone_ to be used; you can't send them directly from your account!
```
