---
title: Antiflood
icon: 🚫
---> Antiflood protection automatically detects and punishes users who send too many messages in a short time period. Configure the message threshold (default: 5 messages in 30 seconds) and action to take (ban, kick, mute, temporary mute, or temporary ban).

## Available commands


### Only admins

| Commands | Arguments | Description | Remarks |
| --- | --- | --- | --- |
| `/setflood` | `<Number of messages>` | Set the antiflood limit for this chat. |  |
| `/antiflood` `/flood` | `<New state>` | Controls the antiflood state. |  |
| `/setfloodaction` | `<New action>` | Sets the antiflood action. |  |
| `/setflood` | `<Number of messages allowed in 30 seconds>` | Set the antiflood message threshold | *Disable-able* |
| `/antiflood` | - | Show antiflood settings | *Disable-able* |
| `/setfloodaction` | - | - |  |