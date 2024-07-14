## Available commands

**Admins only**
- `/antiflood`: Gives you the current configuration of antiflood in the chat
- `/antiflood off`: Disables Antiflood
- `/setflood (limit)`: Sets flood limit
Replace (limit) with any integer; should be less than 200. When setting it up, Sophie will ask you to send an expiration time. If you don't understand what this expiration time is for? The user who sends the specified limit of messages consecutively within this specified time, would be kicked, banned, or whatever the action is. If you don't want this time and want to take action against those who exceeds specified limit without the time interval between the messages mattering, you can reply to the question with 0.

### Configuring the time:
- 2m = 2 minutes
- 2h = 2 hours
- 2d = 2 days`

/setfloodaction (action): `Sets the action to taken when user exceeds flood limit`

##### Currently supported actions:
- ban
- mute
- kick
