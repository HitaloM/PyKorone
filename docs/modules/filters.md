## Exact-match filters

By default, Sophie normalizes message texts by removing special characters, Unicode symbols, and extra spacing.
This normalization ensures your handlers will trigger even when users write messages with Unicode characters or
irregular spacing.

However, sometimes you may need to match exact text, such as when looking for `t.me/+` links (rather than just `t.me`).
For these cases, you can add the `exact:` prefix before your handler to perform strict text matching.

## Regex handlers

Sophie's filters implementation supports handling regex patterns.
To achieve this, you would need to add `re:` before the regex pattern.
For example: `/addfilter re:@\w+` will match if there's a username in the message.

Some regex could be very slow to handle,
the [DoS practice](https://en.wikipedia.org/wiki/ReDoS) of invoking slow regex patterns exists,
therefore, Sophie will test the entered regex against the speed of execution.
In the case the pattern is too slow, it'll be rejected from adding to filters.

## AI Filter handlers

Sophie introduces powerful AI-powered filter handlers that intelligently determine whether to trigger filter actions
based on message content. Powered by Mistral AI, an industry-leading AI provider known for its commitment to data
privacy, this feature allows you to create intelligent filters that understand context and meaning rather than just
matching text patterns.

### How to Use AI Filters

Simply use the `ai:` prefix followed by your prompt when adding filters:

```
/addfilter ai:Your prompt describing when to trigger
```

### Examples

```
/addfilter ai:Has anything regarding money or cryptocurrency
/addfilter ai:Message contains scam or phishing attempt
/addfilter ai:Promotion or advertisement content
/addfilter ai:Spam or unsolicited messages
/addfilter ai:Political content
```

### Supported Content Types

AI filters work with various message types:

- **Text messages**: Analyzes the message text or caption
- **Photos**: Analyzes both the caption and the image content
- **Videos**: Analyzes the caption and video thumbnail
- **GIFs/Animations**: Analyzes the caption and animation thumbnail
- **Stickers**: Analyzes sticker images (static, animated, or video)

## Multiple filter actions and multiple filters

Sophie supports having many filter actions for one filter handler.
This means you can trigger complicated actions like warning users and deleting the user's message.
Or triggering the AI Respond with a prompt that will try to describe users why is it bad to tag admins in chats, while
in the same time deleting the trigger message and muting the user.

However, limits exist.
The maximum number of actions per filter is currently three, and Sophie will only trigger the first two of matching
filters.

# How the Filters Engine Works for Admins vs. Non-Admins

To enable admins to manage the bot's settings, Sophie ignores filters for known commands (listed in /help) when they're
used by admins.
For regular users, filters apply to all messages, even overriding known commands.
If a filter is triggered, Sophie skips executing any part of the command.

For example, if the command is `/notes`, a regular user will trigger a filter action (like message deletion) instead of
getting the notes list.
But admins? They get the list of notes instead.
Also, filters don't apply in PMs, regardless of user status, even if using chat connections.

## Remarks about AI Response filter action

The AI Response action does not require AI features to be enabled. Since only admins can add filters and filter actions,
adding the AI Response filter implies consent for AI features (see the AI help page).

AI Responses enhance interactions in situations where standard responses may seem "too dry".
Sophie will use the message content as context to generate more suitable responses.
Admins can provide additional information in the prompt to help Sophie's AI module better assist users with their
specific needs.

Once the AI Response is generated, users can interact with it by simply replying to the message, which can be invaluable
for addressing follow-up questions.