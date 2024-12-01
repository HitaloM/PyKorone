from sophie_bot.modules.legacy_modules.modules.language import select_lang_keyboard


async def set_lang_cb(event):
    await select_lang_keyboard(event.message, edit=True)
