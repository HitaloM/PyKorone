# Filters

The Filters module is great for everything! Filters are used to filter words or sentences in your chat – send notes, warn, or ban the sender!

## Commands

- `/filter (trigger) (reply)`: Every time someone says "trigger", the bot will reply with "sentence". For multiple word filters, quote the trigger.
- `/filterinfo (trigger)`: Get information about a filter.
- `/filters`: List all active filters in the chat.
- `/delfilter (trigger)`: Stop the bot from replying to "trigger".
- `/delallfilters`: Stop *ALL* filters in the current chat. This cannot be undone.

### Examples

- Set a filter:
  > `/filter hello Hello there! How are you?`

- Set a filter which uses the user's name through fillings:
  > `/filter hello Hello there {first}! How are you?`

- Set a filter on a sentence:
  > `/filter "hello friend" Hello back! Long time no see!`

- Set multiple filters at once by separating wrapping in brackets, and separating with commas:
  > `/filter (hi, hey, hello, "hi there") Hello back! Long time no see!`

- To get the unformatted version of a filter, to copy and edit it, simply say the trigger followed by the keyword "noformat":
  > `trigger noformat`

- To save a "protected" filter, which cant be forwarded:
  > `/filter "example" This filter cant be forwarded {protect}`

- If you want the filter to reply to the person you replied to, instead of you:
  > `/filter "magic" Watch out for wizards! {replytag}`

- To save a file, image, gif, or any other attachment, simply reply to file with:
  > `/filter trigger`

### Fillings

You can also customise the contents of your message with contextual data. For example, you could mention a user by name in the message!

#### Supported fillings:

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


#### Examples

- Set a filter which uses the user's name through fillings:
  > `/filter hello Hello there {first}! How are you?`

- Set a filter which mentions the user and the chat:
  > `/filter hello Hello there {mention}! You are in {chatname}.`
