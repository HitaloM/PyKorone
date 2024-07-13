# Stickers

The stickers module provides commands to manage stickers and sticker sets in Telegram. You can use these commands to steal stickers from other sets, create new sticker sets, and add stickers to existing sets.

## Commands

- `/getsticker`: Fetches the sticker from the replied message and sends it to the chat as a file.
- `/kang (?emoji)`: Steals the sticker from the replied message and adds it to a new sticker set or an existing one. If you provide an emoji, the bot will use it as the sticker's emoji.

```{note}
Currently, the `/kang` command only supports adding stickers to sticker packs created by the bot. You can't add stickers to other people's sticker packs or to sticker packs you created manually.
```

```{hint}
the `/kang` command can be used in reply to images and videos as well.
```
