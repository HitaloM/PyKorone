# Privacy

_PyKorone_ is free and open-source software that does not collect any personal data from users. However, it may collect some data to improve the software. The data collected is anonymous and does not contain any personal information.

```{note}
As a fully open-source project, we encourage you to review our source code on [GitHub](https://github.com/HitaloM/PyKorone) to understand how we handle your data.
```

## What Data is Collected

For proper bot functionality, we store some data discreetly. Here's what we store:

```{important}
All collected data is made available by the Telegram API in a public way, note that if you use real data in your account, not only the bot will have access to it, but also other users if your account is public (has a username). Read more about [Telegram's Privacy Policy](https://telegram.org/privacy).
```

### User Data

- **ID**: The unique identifier of the user, used to identify the user.
- **Username**: The username of the user.
- **First Name**: The user's first name.
- **Last Name**: The user's last name.
- **Telegram Client Language**: The language used by the user in the Telegram client.
- **Registration Date**: The date when the _PyKorone_ bot saw the user for the first time.

### Group Data

- **ID**: The unique identifier of the group, used to identify the group.
- **Username**: The username of the group.
- **Title**: The title of the group.
- **Type**: The type of the group (`supergroup` or `group`).
- **Registration Date**: The date when the _PyKorone_ bot saw the group for the first time.

### Crashlytics

_PyKorone_ uses [Sentry](https://sentry.io/) to collect crash reports and improve the stability of the software. Crashlytics collects the same data as _PyKorone_, plus extra details of the crash itself. By using _PyKorone_ you agree to the [Sentry's privacy policy](https://sentry.io/privacy) as well.

#### Crash Data

The data displayed below is collected by crashlytics and is not stored permanently. It is used exclusively for debugging purposes.

- Crash [traceback](https://en.wikipedia.org/wiki/Stack_trace).
- [Telegram update](https://core.telegram.org/api/updates) that caused the crash.
