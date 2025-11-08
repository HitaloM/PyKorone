Saveables are an internal name for the backend note engine format.
They are used in many places other than notes, for example in Rules, Greetings and Filters modules.

Saveables support many additional features.

## Formatting

Saveables DOES NOT support HTML / Markdown directly, but instead they extract pre-formatted messages.
Simply format your content using inbuilt Telegram's tools.

## Saving files, photos, stickers, media, voice messages

Commonly, the easiest way to do that is to reply to the media message. Sophie would try to save the both message (The
sent and replied message's contents).
But if the media type does not support the text (for example the sticker or the video circle), it will be ignored.
However, those types support buttons, so you can simply attach them.

## Buttons

There's support for some button types.

The most common is the URL button, if you want to add a URL button to your saveable use following syntax at the end of
the message:
`[Button name](btnurl:https://google.com)`.

If you keep adding buttons, they would stack in a horizontal stack.
You can change that by adding `:same` to the end of the button's content. For example:
`[Same-row button](btnurl:https://google.com:same)`.
That would make button render in the same row with previous button.

### Other button types

| Example syntax                         | Description                                                                                                  |
|----------------------------------------|--------------------------------------------------------------------------------------------------------------|
| `[Note button](btnnote:note_name)`     | Redirects users to the DM with Sophie, where she sends the required note.                                    |
| `[Rules button](btnrules)`             | Redirects users to the DM with Sophie, where she shows the rules of the chat.                                |
| `[Delete message button](delmsg)`      | Deletes the message of the button after clicking                                                             |
| `[Connect button](btnconnect)`         | Connects the DM with Group, see [Connection help](/docs/modules/connection) for more information.            |
| `[Captcha button](btnwelcomesecurity)` | Redirects users to the DM to start the captcha process, use only when the captcha is activated for the chat. |
| `[Sophie DM button](btnsophieurl)`     | Redirects users to the DM of Sophie, can be used for `/setjoinrequest`.                                      |

## Fillings

Fillings are special keyword that would be replaced with the actual information later.

| Filling      | Replace value                                                         |
|--------------|-----------------------------------------------------------------------|
| `{first}`    | User's first name                                                     |
| `{last}`     | User's last name                                                      |
| `{fullname}` | The full name of users                                                |
| `{id}`       | User's ID                                                             |
| `{username}` | Username of the user                                                  |
| `{mention}`  | Mentions the user, or the users that were added (for welcome message) |
| `{chatid}`   | ID of the Chat                                                        |
| `{chatname}` | The name of the chat                                                  |
| `{chatnick}` | Username of the chat                                                  |

## Random

Random lets you embed one or more alternative text options inside your saveable and have Sophie pick one at the time of
sending.

Important: Random choices are resolved only when the saveable is rendered/sent. The saved content in the database is NOT
modified or overwritten.

### Syntax

Wrap a choice section with `%%%` delimiters. Each option is separated by another `%%%`.

- Single-line example:
    - Input: `Hello %%%world%%%universe%%% today!`
    - Output (one of): `Hello world today!` or `Hello universe today!`

- Multiple sections in one message:
    - Input: `Have a %%%good%%%bad%%% %%%day%%%night%%%!`
    - Output (one of): `Have a good day!`, `Have a bad day!`, etc.

- Empty option (allowed):
    - Input: `Start %%%%%%middle%%% end`  (options are "" and "middle")
    - Output (one of): `Start  end` or `Start middle end`

- Multiline options (leading/trailing single newlines inside options are normalized):
    - Input:

```
Hello
%%%
world
planet
%%%
universe
galaxy
%%%
```

- Output (one of):

```
Hello
world
planet
```

or

```
Hello
universe
galaxy
```
