# This file is part of Korone (Telegram Bot)

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import html

from config import prefix
from pyromod.helpers import ikb
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery

from . import COMMANDS_HELP

help_text = "Por favor, selecione uma categoria para obter ajuda!"

about_text = """
🚮 <b>PyKorone</b> é um bot criado por diversão para o grupo <b>Spam-Therapy</b>. Seu foco é trazer funções legais e um design funcional com tecnologia e criatividade.

📦 Powered by <a href='https://docs.pyrogram.org/'>Pyrogram</a> with <a href='https://github.com/usernein/pyromod'>Pyromod</a>.

🗂 <b>Links:</b> <a href='https://github.com/HitaloSama/PyKorone'>GitHub</a> | <a href='https://t.me/SpamTherapy'>Chat</a>
"""


@Client.on_message(
    filters.cmd(command="start", action="Envia a mensagem de inicialização do Bot.")
)
async def start(c: Client, m: Message):
    keyboard = []
    text = (
        "Oi, eu sou o <b>Korone</b>, um bot interativo "
        "que adora participar de grupos!\n"
    )
    if m.chat.type == "private":
        keyboard.append([("📚 Ajuda", "help_cb"), ("ℹ️ Sobre", "about")])
        keyboard.append([("👥 Grupo Off-Topic", "https://t.me/SpamTherapy", "url")])
    else:
        keyboard.append(
            [
                (
                    "Clique aqui para obter ajuda!",
                    f"http://t.me/{(await c.get_me()).username}?start",
                    "url",
                )
            ]
        )
        text += "Você pode ver tudo que eu posso fazer clicando no botão abaixo..."
    await m.reply_text(
        text,
        reply_markup=ikb(keyboard),
    )


@Client.on_message(filters.cmd("help (?P<module>.+)"))
async def help_m(c: Client, m: Message):
    module = m.matches[0]["module"]
    if m.chat.type == "private":
        await help_module(m, module)
        return


@Client.on_message(
    filters.cmd(command="help", action="Envia o menu de ajuda do Bot.")
    & filters.private
)
async def help(c: Client, m: Message):
    await help_module(m)


@Client.on_callback_query(filters.regex("^help_cb$"))
async def help_cb(c: Client, m: CallbackQuery):
    await help_module(m)


@Client.on_message(filters.command("help", prefix) & filters.private)
async def help_command(c: Client, m: Message):
    keyboard = ikb(
        [
            [("Comandos", "help_cmds"), ("Filtros", "help_regex")],
            [("⬅️ Voltar", "start_back")],
        ]
    )
    await m.reply_text(
        help_text,
        reply_markup=keyboard,
    )


async def help_module(m: Message, module: str = None):
    is_query = isinstance(m, CallbackQuery)
    text = ""
    keyboard = []
    success = False
    if not module or module == "start":
        keyboard.append([("Comandos", "help_cmds"), ("Filtros", "help_filters")])
        keyboard.append([("⬅️ Voltar", "start_back")])
        text = "Por favor, selecione uma categoria para obter ajuda!"
        success = True
    else:
        if module == "cmds":
            modules = []
            for key, value in COMMANDS_HELP.items():
                if "commands" in value:
                    modules.append(key)
            text = f"Eu tenho atualmente <code>{len(modules)}</code> módulo(s) com comandos, verifique-os usando <code>/help &lt;módulo&gt;</code>.\n"
            if len(modules) > 0:
                text += "\n<b>Módulo(s)</b>:"
                for module_name in modules:
                    text += f"\n  - <code>{module_name}</code>"
            success = True
            keyboard.append([("⬅️ Voltar", "help_start")])
        elif module == "filters":
            modules = []
            for key, value in COMMANDS_HELP.items():
                if "filters" in value:
                    modules.append(key)
            text = f"Eu tenho atualmente <code>{len(modules)}</code> módulo(s) com filtros, verifique-os usando <code>/help &lt;módulo&gt;</code>.\n"
            if len(modules) > 0:
                text += "\n<b>Módulo(s)</b>:"
                for module_name in modules:
                    text += f"\n  - <code>{module_name}</code>"
            success = True
            keyboard.append([("⬅️ Voltar", "help_start")])
        elif module in COMMANDS_HELP.keys():
            text = f"<b>Módulo</b>: <code>{module}</code>\n"
            module = COMMANDS_HELP[module]
            text += f'\n{module["text"]}\n'

            type = "commands" if "commands" in module else "filters"
            if len(module[type]) > 0:
                text += f'\n<b>{"Comandos" if type == "commands" else "Filtros"}</b>:'
                for key, value in module[type].items():
                    action = value["action"]
                    if len(action) > 0:
                        regex = ""
                        if type == "commands":
                            regex = key.split()[0]
                            if "<" in key and ">" in key:
                                left = key[len(regex) :].split("<")[1:]
                                for field in left:
                                    regex += " <" + field.split(">")[0] + ">"
                        else:
                            regex = key
                        if action == " " and type == "filters":
                            text += f"\n  - <code>{html.escape(regex)}</code>"
                        elif action not in [" ", ""] and type == "filters":
                            text += f"\n  - <code>{html.escape(regex)}</code>: {action}"
                        else:
                            text += f'\n  - <b>{"/" if type == "commands" else ""}{html.escape(regex)}</b>: <i>{action}</i>'
            success = True

    kwargs = {}
    if len(keyboard) > 0:
        kwargs["reply_markup"] = ikb(keyboard)

    if success:
        await (m.edit_message_text if is_query else m.reply)(text, **kwargs)


@Client.on_callback_query(filters.regex("help_(?P<module>.+)"))
async def on_help_callback(c: Client, cq: CallbackQuery):
    module = cq.matches[0]["module"]
    await help_module(cq, module)


@Client.on_callback_query(filters.regex("^about$"))
async def about(c: Client, m: CallbackQuery):
    keyboard = ikb([[("⬅️ Voltar", "start_back")]])
    await m.message.edit_text(
        about_text,
        reply_markup=keyboard,
        disable_web_page_preview=True,
    )


@Client.on_callback_query(filters.regex("^start_back$"))
async def start_back(c: Client, m: CallbackQuery):
    keyboard = ikb(
        [
            [("📚 Ajuda", "help_cb"), ("ℹ️ Sobre", "about")],
            [("👥 Grupo Off-Topic", "https://t.me/SpamTherapy", "url")],
        ]
    )
    await m.message.edit_text(
        "Oi, eu sou o <b>Korone</b>, um bot interativo "
        "que adora participar de grupos!",
        reply_markup=keyboard,
    )
