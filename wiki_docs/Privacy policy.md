:information_source: Sophie respects your privacy; every part of Sophie is open source!

For privacy inquiries, please contact sophie@orangefox.tech

# What data we are saving / caching

For the proper functionality of the bot, we are saving some data inconspicuously.
Here are all the non-obvious things we are saving:

### Settings and save-able content

Configurations and content such as notes, filters, etc.

### Users

- First and second names;
- User ID, Telegram username;
- Telegram language;
- Timestamp of the date when Sophie had seen the user for the first and the last time.
- Chat memberships

### Chats

- Chat name;
- Chat ID;
- Username and Chat ID;
- Chat admins.

### Messages

- If Antiflood is explicitly enabled, the bot caches* the timestamps of sent messages and their author IDs.
- If AI Features are explicitly activated, the bot caches* the text of messages and their author IDs (for the past 48
  hours).

*Caching refers to storing data for a limited time, which in Sophie's case, does not exceed 7 days.

# How we use the data

We are processing, storing, managing all the data strictly only on the Sophie's virtual machines, with all the latest
security updates automatically installed weekly.

For some AI Features, with the direct user consent of enabling AI Features,
Sophie could provide some of the saved data to OpenAI
(see the OpenAI's privacy policy - https://openai.com/enterprise-privacy/)

# Rights to process

### Retrieve your data

Use '/export' command in your Private Message with Sophie to retrieve stored information.

### Data deletion and consent withdrawal

You can withdraw your consent and request deletion of your data at any time.

* To withdraw consent for data collection and processing:** Stop using Sophie (i.e., stop sending Telegram messages).
* To delete saved content: Remove any previously saved content within Sophie, such as notes and filters.
* Automatic deletion: Non-essential information is automatically deleted after 7 days of inactivity.

We have legitimate interest to store the essential information (Warnings, Federation Bans, User ID, and Names)
indefinitely to maintain platform security and protect our users.
This is necessary for the proper functioning of Sophie and its ability to protect chats/groups/channels.

For special cases, you can request deletion of this essential information by contacting us at sophie@orangefox.tech,
and we will review such requests on a case-by-case basis.

However, deleting this information may prevent you from using Sophie.

# Third parties

### AI

AI features are disabled by default and can only be activated with the user's explicit consent.
When these features are activated,
you agree to:

* [OpenAI Privacy Policy](https://openai.com/enterprise-privacy/)
* [Google Privacy Policy](https://ai.google.dev/gemini-api/terms)
* [Tavily Privacy Policy](https://www.tavily.com/privacy)

While using some AI-enabled features such as AI Chatbot, AI Translator or AI Moderator,
we may share the context of the conversation, which can
include up to 40 of the most recent messages (including bot responses).

Additionally, user-saved data like notes, filters, settings, etc.,
may be shared with OpenAI and Google, but only while using some AI-assisted features.

### Crashlytics (Sentry):

Crashlytics helps us improve Sophie's stability.
We collect crash tracebacks and, in some cases, code variable states,
which may include raw update data that caused the crash.
This data is automatically purged after the issues are resolved or after 48 hours.
You will be notified of crashes via a "crash" message from Sophie (unless technical limitations prevent delivery).
By using Sophie, you agree to Sentry's privacy policy: https://sentry.io/privacy.

This data is automatically purged after the issues are closed or/and stale or after 48 hours.
The crashlytics are not hidden. You will be clearly notified about it with the "crash" message Sophie would send.
In some cases, if it's not possible to send the message (the bot is blocked or another reason Telegram doesn't sends
the message), this guarantee can be withdrawn.

# Changes to This Policy

We may update this Privacy Policy from time to time.
We will notify you of any significant changes by sending a message in the Sophie's NEWS Telegram channel
(https://t.me/SophieNEWS).
