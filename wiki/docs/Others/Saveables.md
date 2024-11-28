Saveables are an internal name for the backend note engine format.
They are used in many places other than notes, for example in Rules, Greetings and Filters modules.

Saveables support many additional features.

## Formatting
Saveables DOES NOT support HTML / Markdown directly, but instead they extract pre-formatted messages.
Simply format your content using inbuilt Telegram's tools.

## Saving files, photos, stickers, media, voice messages
Commonly, the easiest way to do that is to reply to the media message. Sophie would try to save the both message (The sent and replied message's contents).
But if the media type does not support the text (for example the sticker or the video circle), it will be ignored.
However, those types support buttons, so you can simply attach them.

## Buttons
There's support for some button types.

The most common is the URL button, if you want to add a URL button to your saveable use following syntax at the end of the message:
`[Button name](btnurl:https://google.com)`.

If you keep adding buttons, they would stack in a horizontal stack.
You can change that by adding `:same` to the end of the button's content. For example:
`[Same-row button](btnurl:https://google.com:same)`.
That would make button render in the same row with previous button.

### Other button types

| Example syntax                        | Description                                                                                                  |
|---------------------------------------|--------------------------------------------------------------------------------------------------------------|
| `[Note button](btnnote:note_name)`    | Redirects users to the DM with Sophie, where she sends the required note.                                    |
| `[Rules button](btnrules)`            | Redirects users to the DM with Sophie, where she shows the rules of the chat.                                |
| `[Delete message button](delmsg)`     | Deletes the message of the button after clicking                                                             |
| `[Connect button](btnconnect)`        | Connects the DM with Group, see [Connection help](/docs/modules/connection) for more information.            |
| `[Captcha button](btnwelcomesecurity` | Redirects users to the DM to start the captcha prcoess, use only when the captcha is activated for the chat. |

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
