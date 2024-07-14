## Available commands

## General
- `/setwelcome or /savewelcome`: Set welcome
- `/setwelcome (on/off)`: Disable/enabled welcomes in your chat
- `/welcome`: Shows current welcomes settings and welcome text
- `/resetwelcome`: Reset welcomes settings

## Welcome security
- `/welcomesecurity (level)`
Turns on welcome security with specified level, either button or captcha (learn more about levels). Setting up welcome security will give you a choice to customize join expiration time aka minimum time given to user to verify themselves not a bot, users who do not verify within this time would be kicked!

- `/welcomesecurity (off/no/0)`: Disable welcome security
- `/setsecuritynote`: Customise the "Please press button below to verify themself as human!" text
- `/delsecuritynote`: Reset security text to defaults

## Welcome mutes
- `/welcomemute (time)`: Set welcome mute (no media) for X time
- `/welcomemute (off/no)`: Disable welcome mute

## Purges
- `/cleanwelcome (on/off)`: Deletes old welcome messages and last one after 45 mintes
- `/cleanservice (on/off)`: Cleans service messages (user X joined)

## Customizing
Settings images, gifs, videos or stickers as welcome
Saving attachments on welcome is same as saving notes with it, read the notes help about it. But keep in mind what you have to replace /save to /setwelcome

Addings buttons and variables to welcomes or security text
Buttons and variables syntax is same as notes buttons and variables

## Welcome security
Available levels

- `button`: Ask user to press "I'm not a bot" button
- `math`: Asking to solve simple math query, few buttons with answers will be provided, only one will have right answer
- `captcha`: Ask user to enter captcha
If welcome security is enabled, user will be welcomed with security text, if user successfully verify self as user, he/she will be welcomed also with welcome text in his PM (to prevent spamming in chat).

If user didn't verify themself for 24 hours, they will be kicked from chat.
