---
title: Greetings
icon: 🙋‍♂️
---> This module helps you to welcome new users automatically, while keeping the chat clean. \
> If you want to enforce captcha / rules verification, please see 'Welcome Security' module instead.

## Available commands


### Commands

| Commands | Arguments | Description | Remarks |
| --- | --- | --- | --- |
| `/welcome` | - | Shows welcome settings | *Disable-able* |

### Only admins

| Commands | Arguments | Description | Remarks |
| --- | --- | --- | --- |
| `/enablewelcome` | `<?New status>` | Shows / changes the state of sending greetings |  |
| `/setwelcome` | `<Content>` | Sets welcome message. |  |
| `/setjoinrequest` | `<Content>` | Sets join request message. |  |
| `/deljoinrequest` | - | Deletes the join request message |  |
| `/cleanservice` | `<?New status>` | Shows / changes the state of automatic service messages cleanup. |  |
| `/cleanwelcome` | `<?New status>` | Shows / changes the state of automatic welcome messages cleanup. |  |