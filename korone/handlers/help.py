# This file is part of Korone (Telegram Bot)
# Copyright (C) 2022 AmanoTeam

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
from contextlib import suppress
from typing import Union

from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.errors import MessageNotModified
from pyrogram.types import CallbackQuery, Message

import korone
from korone.handlers import COMMANDS_HELP
from korone.korone import Korone

help_text = "Por favor, selecione uma categoria para obter ajuda!"

start_text = """
Oi <b>{}</b>!

Eu sou o <b>{}</b>, um bot interativo que adora participar de grupos! ^^
<b>Versão:</b> <code>{} ({})</code>
"""

about_text = """
🚮 <b>{}</b> é um bot criado por diversão para o grupo <b>Spam-Therapy</b>.
Seu foco é trazer funções legais e um design funcional com tecnologia e criatividade.

📦 Powered by <a href='https://docs.pyrogram.org/'>Pyrogram</a> with <a href='https://github.com/usernein/pyromod'>Pyromod</a>.

🗂 <b>Links:</b> <a href='{}'>GitHub</a> | <a href='{}'>Chat</a>
"""


@Korone.on_message(
    filters.cmd(command=r"start", action="Envia a mensagem de inicialização do bot.")
)
@Korone.on_callback_query(filters.regex(r"^start_back$"))
async def start(c: Korone, m: Union[Message, CallbackQuery]):
    if isinstance(m, Message):
        query = m.text.split()
        if len(query) > 1:
            field = query[1]
            query = field.split("_")
            if query[0] == "help":
                module = query[1]
                await help_module(c, m, module)
        else:
            keyboard = []
            text = (start_text).format(
                m.from_user.first_name,
                c.me.first_name,
                korone.__version__,
                c.version_code,
            )
            if m.chat.type == ChatType.PRIVATE:
                keyboard.append([("📚 Ajuda", "help_cb"), ("ℹ️ Sobre", "about")])
                keyboard.append(
                    [("👥 Grupo Off-Topic", "https://t.me/SpamTherapy", "url")]
                )
            else:
                keyboard.append(
                    [
                        (
                            "Clique aqui para obter ajuda!",
                            f"http://t.me/{c.me.username}?start",
                            "url",
                        )
                    ]
                )
                text += "\nVocê pode ver tudo que eu posso fazer clicando no botão abaixo..."
            await m.reply_text(
                text,
                reply_markup=c.ikb(keyboard),
            )
    if isinstance(m, CallbackQuery):
        text = (start_text).format(
            m.from_user.first_name,
            c.me.first_name,
            korone.__version__,
            c.version_code,
        )
        keyboard = [
            [("📚 Ajuda", "help_cb"), ("ℹ️ Sobre", "about")],
            [("👥 Grupo Off-Topic", "https://t.me/SpamTherapy", "url")],
        ]
        with suppress(MessageNotModified):
            await m.message.edit_text(text, reply_markup=c.ikb(keyboard))


@Korone.on_message(filters.cmd(r"help (?P<module>.+)"))
async def help_m(c: Korone, m: Message):
    module = m.matches[0]["module"]
    if m.chat.type == "private":
        if module in COMMANDS_HELP.keys() or module in [
            "commands",
            "filters",
            "start",
        ]:
            await help_module(c, m, module)
        else:
            await m.reply_text(
                f"Desculpe! Não encontrei o módulo <code>{module}</code>, "
                "verifique sua pesquisa e tente novamente."
            )
    elif module in COMMANDS_HELP.keys():
        keyboard = [
            [
                (
                    "Ir ao PV",
                    f"https://t.me/{c.me.username}/?start=help_{module}",
                    "url",
                )
            ]
        ]
        await m.reply_text(
            text="Para ver isso, vá ao meu PV.", reply_markup=c.ikb(keyboard)
        )
    else:
        keyboard = [[("Ir ao PV", f"https://t.me/{c.me.username}/?start", "url")]]
        await m.reply_text(
            "Este módulo não existe, vá ao meu PV para ver os módulos que possuo!",
            reply_markup=c.ikb(keyboard),
        )


@Korone.on_message(filters.cmd(command=r"help", action="Envia o menu de ajuda do Bot."))
@Korone.on_callback_query(filters.regex(r"^help_cb$"))
async def help_c(c: Korone, m: Union[Message, CallbackQuery]):
    if isinstance(m, Message) and m.chat.type in ["supergroup", "group"]:
        keyboard = [[("Ir ao PV", f"https://t.me/{c.me.username}/?start", "url")]]
        await m.reply_text(
            "Para obter ajuda vá ao meu PV!", reply_markup=c.ikb(keyboard)
        )
    elif isinstance(m, (Message, CallbackQuery)):
        await help_module(c, m)


async def help_module(c: Korone, m: Message, module: str = None):
    is_query = isinstance(m, CallbackQuery)
    text = ""
    keyboard = []
    success = False
    if not module or module == "start":
        keyboard.append([("Comandos", "help_commands"), ("Filtros", "help_filters")])
        keyboard.append([("⬅️ Voltar", "start_back")])
        text = "Por favor, selecione uma categoria para obter ajuda!"
        success = True
    elif module in {"commands", "filters"}:
        text = "Escolha um módulo ou use <code>/help &lt;módulo&gt;</code>.\n"
        keyboard = [[]]
        index = 0
        for key, value in COMMANDS_HELP.items():
            if module in value and "help" in value and value["help"]:
                if len(keyboard[index]) == 3:
                    index += 1
                    keyboard.append([])
                keyboard[index].append(
                    (
                        value["name"] if "name" in value else key.capitalize(),
                        f"help_{key}",
                    )
                )
        success = True
        keyboard.append([("⬅️ Voltar", "help_start")])
    elif module in COMMANDS_HELP.keys():
        text = f"<b>Módulo</b>: <code>{module}</code>\n"
        module = COMMANDS_HELP[module]
        text += f'\n{module["text"]}\n'

        m_type = "commands" if "commands" in module else "filters"
        if len(module[m_type]) > 0:
            text += f'\n<b>{"Comandos" if m_type == "commands" else "Filtros"}</b>:'
            for key, value in module[m_type].items():
                action = value["action"]
                if len(action) > 0:
                    regex = ""
                    if m_type == "commands":
                        key = key.replace("$", "")
                        regex = key.split()[0]
                        if "<" in key and ">" in key:
                            left = key[len(regex) :].split("<")[1:]
                            for field in left:
                                regex += " <" + field.split(">")[0] + ">"
                        else:
                            regex = key
                    else:
                        regex = key
                    if action == " " and m_type == "filters":
                        text += f"\n  - <code>{html.escape(regex)}</code>"
                    elif action not in [" ", ""] and m_type == "filters":
                        text += f"\n  - <code>{html.escape(regex)}</code>: {action}"
                    else:
                        text += f'\n  - <b>{"/" if m_type == "commands" else ""}{html.escape(regex)}</b>: <i>{action}</i>'
        success = True
        keyboard.append([("⬅️ Voltar", f"help_{m_type}")])

    kwargs = {}
    if keyboard:
        kwargs["reply_markup"] = c.ikb(keyboard)

    if success:
        with suppress(MessageNotModified):
            await (m.edit_message_text if is_query else m.reply_text)(text, **kwargs)


@Korone.on_callback_query(filters.regex(r"help_(?P<module>.+)"))
async def on_help_callback(c: Korone, cq: CallbackQuery):
    module = cq.matches[0]["module"]
    await help_module(c, cq, module)


@Korone.on_message(
    filters.cmd(
        command=r"about",
        action="Veja algumas informações sobre o bot.",
    )
)
@Korone.on_callback_query(filters.regex(r"^about$"))
async def about_c(c: Korone, m: Union[Message, CallbackQuery]):
    is_callback = isinstance(m, CallbackQuery)
    about = about_text.format(
        c.me.first_name,
        korone.__source__,
        korone.__community__,
    )
    keyboard = c.ikb([[("⬅️ Voltar", "start_back")]])
    with suppress(MessageNotModified):
        await (m.message.edit_text if is_callback else m.reply_text)(
            about,
            reply_markup=(keyboard if is_callback else None),
            disable_web_page_preview=True,
        )
