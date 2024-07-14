The Filters module is great for everything! Filters are used to filter words or sentences in your chat – send notes, warn, or ban the sender!

## Available commands
**Admin commands**
- `/addfilter` (word/sentence)
This is the command used to add a filter. To avoid hassle when setting up the the filter, Sophie will take you through an interactive setup!

As of now, there is 6 actions that you can use:

- Delete the message
- Reply to message
- Send a note
- Warn the user
- Mute the user
- tMute the user
- Kick the user
- Ban the user
- tBan the user
A filter can support multiple actions!

Ah, if you don't understand what this actions are for? – The action determines what the bot will do when the given word/sentence is triggered.

- Examples of setting up filters
Step for setting each actions differs – most of them are identical!
Here we are setting up filter for word foo:
filter_setup.png
Actions like Delete the message are directly saved. The other actions, like Send a note, require the note that should to be sent. Similarly, tMute the user and tBan the user requires time, etc. Sophie will ask you for the required properties once you select an action.

- Example: Saving filter with action Send a note
Here, I will create a foo filter with action Send a note. My note name is note and it contains the text bar, after clicking Send a note button - This is how I setup foo filter
saving_note_filter.png
It was that easy, right? Now look how to set up tBan the user or tMute the user - Both follow same procedure

- Example: Saving filter with action tBan the user
Now, I will setup a foo filter with the action tBan the user or tMute the user for 10m (10 minutes). The following shows after pressing the according button:
saving_time_filter.png
Again that was so easy too 😉

## Deleting filters
- `/delfilter (filter)`
So, you don't like your filter? Use this command to delete the filter.

**Example**

Here I gonna delete my foo filter. It just needs /delfilter foo!

If there's more than one action for a word / sentence, Sophie will give you options and you can select filter you want to delete.

## Available for all users
- `/filters` or `/listfilters`
You want to know all filter of your chat / chat you joined? Use this command. It will list all filters along with specified actions!
