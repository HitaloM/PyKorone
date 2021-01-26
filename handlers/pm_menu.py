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

import pyrogram
import pyromod
from config import prefix
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from pyromod.helpers import ikb


@Client.on_message(filters.command("start", prefix) & filters.group )
async def start_group(c: Client, m: Message):
    keyboard = ikb([
        [("Clique aqui para obter ajuda!", "http://t.me/PyKoroneBot?start", "url")]
    ])
    await m.reply_text(
        f"Oi, eu sou o <b>Korone</b>, um bot interativo "
        "que adora participar de grupos!\n"
        "Você pode ver tudo que eu posso fazer clicando no botão abaixo...",
        reply_markup=keyboard,
    )


@Client.on_message(filters.command("start", prefix) & filters.private )
async def start(c: Client, m: Message):
    keyboard = ikb([
        [("Ajuda", "help"),
        ("Sobre", "about")],
        [("Grupo Off-Topic", "https://t.me/SpamTherapy", "url")]
    ])
    await m.reply_text(
        f"Oi, eu sou o <b>Korone</b>, um bot interativo "
        "que adora participar de grupos!",
        reply_markup=keyboard,
    )


@Client.on_callback_query(filters.regex("^help$"))
async def help(c: Client, m: CallbackQuery):
    keyboard = ikb([[("<- Voltar", "start_back", "callback_data")]])
    await m.message.edit_text(
        "<b>Aqui estão alguns dos meus comandos:</b>\n"
        "• <code>/start</code>: Envi a mensagem inicial do bot.\n"
        "• <code>/ping</code>: Envia o ping do bot.\n"
        "• <code>/py</code>: Envia algumas informações técnicas do bot.\n"
        "• <code>/copy</code>: O bot copia a mensagem que você responder com este comando.\n"
        "• <code>/user</code>: Obtêm informações básicas de um usuário.",
        reply_markup=keyboard,
    )


@Client.on_callback_query(filters.regex("^about$"))
async def about(c: Client, m: CallbackQuery):
    keyboard = ikb([[("<- Voltar", "start_back", "callback_data")]])
    await m.message.edit_text(
        """
🚮 <b>PyKorone</b> é um bot criado por diversão para o grupo <b>Spam-Therapy</b>. Seu foco é trazer funções legais e um design funcional com tecnologia e criatividade.

📦 Powered by <a href='https://docs.pyrogram.org/'>Pyrogram</a> with <a href='https://github.com/usernein/pyromod'>Pyromod</a>.

🗂 <b>Links:</b> <a href='https://github.com/HitaloSama/PyKorone'>GitHub</a> | <a href='https://t.me/SpamTherapy'>Chat</a>
        """,
        reply_markup=keyboard,
        disable_web_page_preview=True,
    )


@Client.on_callback_query(filters.regex("^start_back$"))
async def start_back(c: Client, m: CallbackQuery):
    keyboard = ikb([
        [("Ajuda", "help"),
        ("Sobre", "about")],
        [("Grupo Off-Topic", "https://t.me/SpamTherapy", "url")]
    ])
    await m.message.edit_text(
        f"Oi, eu sou o <b>Korone</b>, um bot interativo "
        "que adora participar de grupos!",
        reply_markup=keyboard,
    )