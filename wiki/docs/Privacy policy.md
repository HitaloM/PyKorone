:information_source: Sophie respects your privacy; every part of Sophie is open source!

# What data we are saving
For the proper functionality of the bot, we are saving some data inconspicuously.
Here are all the non-obvious things we are saving:

### Settings and save-able content
Configurations and content such as notes, filters, etc.

### Users
- First and second names;
- User ID, Telegram username;
- Telegram language;
- Timestamp of the date when Sophie had seen the user for the first and the last time.
- Chat memeberships

### Chats
- Chat name;
- Chat ID;
- Username and Chat ID;
- Chat admins.

### Messages
- If the Antiflood is explicitly enabled - cached message send times and authors.
- If the AI Features are explicitly activates - cached message texts and authors (last 48h)

# How we use the data
We are processing, storing, managing all the data strictly only on the Sophie's virtual machines, with all the latest 
security updates automatically installed weekly.

# Rights to process

### Retrieve your data
Use '/export' command in your Private Message with Sophie to retrieve stored information.

### Remove your consent and delete data
You are able to remove your consent at any time. 
You can do that by stopping using Sophie (sending Telegram messages) and removing the previously saved content 
(such as notes, filters, etc).
The non-critical information would be automatically removed typically after 48 hours automatically.

We have legitimate interest to store the essential information (such as: Warnings, Federation Bans and User ID with Names.) indefinitely that are required to the functioning of 
Sophie. Sophie is using those data to protect chats/groups/channels.

# Third parties

### AI
When AI features are activated, you automatically agree with the OpenAI's privacy policy - https://openai.com/enterprise-privacy/
For some AI features, such as ChatBot feature, we would pass the context that could include cached chat's message 
history (typically less than 41 messages, including bot's responses)


### Crashlytics
Crashlytics significantly help Sophie to be stable. We are trying to log as few data as possible.
By using Sophie you agree to the Sentry's privacy policy as well - https://sentry.io/privacy.

We are collecting:
- Crash traceback with code variables states
- In some cases, code variables could contain the raw update data which caused the crash

This data is automatically purged after the issues are closed or/and stale or after 48 hours.
The crashlytics are not hidden. You will be clearly notified about it with the "crash" message Sophie would send.
In some cases, if it's not possible to send the message (the bot is blocked or another reason Telegram doesn't sends 
the message), this guarantee can be withdrawn.
