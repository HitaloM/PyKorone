# Privacy

```{note}
**Privacy is a priority for PyKorone!**

As a fully open-source project, we encourage you to review our source code on [GitHub](https://github.com/HitaloM/PyKorone) to understand how we handle your data.
```

```{important}
**Your personal data is safe with us!**

PyKorone does not store any personal information about you. We only collect data that is necessary for the bot to function properly.
```

PyKorone is free and open-source software that does not collect any personal data from users. However, it may collect some data to improve the software. The data collected is anonymous and does not contain any personal information.

## What Data is Collected

PyKorone may collect the following data:

### User Data

- **ID**: The unique identifier of the user, used to identify the user.
- **Username**: The username of the user, if it has one.
- **First Name**: The user's first name.
- **Last Name**: The user's last name.
- **Telegram Client Language**: The language used by the user in the Telegram client.
- **Registration Date**: The date when the PyKorone bot saw the user for the first time.

### Group Data

- **ID**: The unique identifier of the group, used to identify the group.
- **Username**: The username of the group, if it has one.
- **Title**: The title of the group.
- **Type**: The type of the group (`supergroup` or `group`).
- **Registration Date**: The date when the PyKorone bot saw the group for the first time.

```{note}
All collected data is public and can be accessed by anyone through the [Telegram API](https://core.telegram.org/bots/api).
```

### Crashlytics

PyKorone uses [Sentry](https://sentry.io/) to collect crash reports and improve the stability of the software. Crashlytics collects the same data as PyKorone, plus extra details of the crash itself.

#### Currently, we only log:

- Crash [traceback](https://en.wikipedia.org/wiki/Stack_trace).
- [Telegram update](https://core.telegram.org/api/updates) that caused the crash. (We don't store the data; it's just for debugging purposes)
