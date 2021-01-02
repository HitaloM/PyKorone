from pyrogram import Client, idle

from config import API_ID, API_HASH, TOKEN


client = Client("bot", API_ID, API_HASH,
                bot_token=TOKEN,
                parse_mode="html",
                plugins=dict(root="handlers"))

if __name__ == "__main__":
    client.start()
    idle()
