
# Notes 📗


## Available commands


### Commands

| Commands | Arguments | Description | Remarks |
| --- | --- | --- | --- |
| `/pmnotes` `/privatenotes` | - | Show current state of Private Notes | *Only in groups* |
| `/notes` `/saved` `/notelist` | `<?Search notes>` | Lists available notes. | *Disable-able* |
| `/get` | `<Note name>` `<?raw>` | Retrieve the note. |  |
| `/search` | `<Text to search>` | Searches for note contents | *Disable-able* |

### Only admins

| Commands | Arguments | Description | Remarks |
| --- | --- | --- | --- |
| `/pmnotes` `/privatenotes` | `<New state>` | Control Private Notes | *Only in groups* |
| `/delnote` `/clear` | `<Note name>` | Deletes notes. |  |
| `/save` `/addnote` | `<Note names>` `<?Description>` `<Content>` | Save the note. |  |
| `/clearall` | - | Deletes notes. |  |

### Aliased commands from [✨ Sophie AI](ai)

| Commands | Arguments | Description | Remarks |
| --- | --- | --- | --- |
| `/aisave` | `<Prompt>` | Generate a new note using AI |  |
---
# Features


## AI notes generation
Please refer to the [AI help page](ai).

## Saving photos / stickers, adding buttons and fillings
Please refer to the [Saveables help page](/docs/Others/Saveables) of Sophie, as this information is global and work in many other places.

## Note searching
Sophie implements 2 ways to search notes.
The simplest way is to filer by the note names using `/notes <filter>`.

Additionally, you can search by the content using `/search <content>`.

## PM Notes / Private Notes
By default, the notes are being shown in the group, but if you want to redirect users to the private messages of Sophie, you can enable private notes mode.
This would redirect users with a button to the PM, every time they request `/notes` or `/search`,

> Please note, that admins still can still access the `/notes` and other commands in the group directly.
> Additionally, users would still be able to `/get` the note.

# Advanced usage

### Multiple note names
Sophie supports setting many note names for the note, this helps users to retrieve the note by the expected note name.

For example
`/save pie | pierecipe | pie_recipes To cook the Pie you would need...`.
This would save the note with 3 different note names, and you can retrieve it by using any of them.

### Note Descriptions
Notes could have description that could help users indentify the note's content.
To add a description use following syntax:
`/saave pie "Tasty pie recipe"`. Of course, you can also add multiple note names, by just splitting them with `|`. See above for more information.
