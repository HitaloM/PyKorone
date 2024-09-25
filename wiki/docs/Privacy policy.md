:information_source: Sophie respects your privacy; every part of Sophie is open source!

# What data we are saving
For the proper functionality of the bot, we are saving some data inconspicuously.
Here are all the non-obvious things we are saving:

## Users
- First and second names;
- User ID, Telegram username;
- Telegram language;
- Timestamp of the date when Sophie had seen the user for the first and the last time.

## Chats
- Chat name;
- Chat ID;
- Username and Chat ID;
- Chat admins.

## Messages
- Temporary cached message time history, authors and count (only when antiflood feature is activated).
- Temporary cached temporary message text, author and count (only when AI is activated) 

## Crashlytics
Crashlytics significantly help Sophie to be stable. We are trying to log as few data as possible.
By using Sophie you agree to the Sentry's privacy policy as well - https://sentry.io/privacy.

We are collecting:
- Crash traceback with code variables states
- In some cases, a raw update data which caused the crash

This data is automatically purged after the issues are closed or stale.
The crashlytics are not hidden. You will be clearly notified about it with the "crash" message Sophie would send.
In some cases, if it's not possible to send the message (the bot is blocked or another reason Telegram doesn't sends 
the message), this guarantee can be withdrawn.

# How we use the data
We are processing, storing, managing all the data strictly only on the Sophie's virtual machines, with all the latest 
security updates automatically installed weekly.

We are not sharing any kinds of the data with third-parties except the anonymous statistics (such as total count of 
the chats/users or/and percentage and total amount of data that being used for overall number of chats) and crashlytics.

# Deleting the data
Currently, removing Sophie from the chat she's in would trigger an automatic data purge task. For users, it is not 
yet possible to automatically purge the data.

# AI
When AI features are activated, you automatically agree with the OpenAI's privacy policy - https://openai.com/enterprise-privacy/
For some AI features, such as ChatBot feature, we would pass the context that could include cached chat's message 
history (typically less than 20 messages)
