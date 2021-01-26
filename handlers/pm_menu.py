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

from config import prefix
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from pyromod.helpers import ikb

help_text = "Por favor, selecione uma categoria para obter ajuda!"


@Client.on_message(filters.command("start", prefix) & filters.group)
async def start_group(c: Client, m: Message):
    keyboard = ikb([
        [("Clique aqui para obter ajuda!", "http://t.me/PyKoroneBot?start", "url")]
    ])
    await m.reply_text(
        "Oi, eu sou o <b>Korone</b>, um bot interativo "
        "que adora participar de grupos!\n"
        "Você pode ver tudo que eu posso fazer clicando no botão abaixo...",
        reply_markup=keyboard,
    )


@Client.on_message(filters.command("start", prefix) & filters.private)
async def start(c: Client, m: Message):
    keyboard = ikb([
        [("Ajuda", "help"),
         ("Sobre", "about")],
        [("Grupo Off-Topic", "https://t.me/SpamTherapy", "url")]
    ])
    await m.reply_text(
        "Oi, eu sou o <b>Korone</b>, um bot interativo "
        "que adora participar de grupos!",
        reply_markup=keyboard,
    )


@Client.on_message(filters.command("help", prefix) & filters.private)
async def help_command(c: Client, m: Message):
    keyboard = ikb([
        [("Comandos", "help_cmds"),
         ("Filtros", "help_regex")],
        [("<- Voltar", "start_back")]
    ])
    await m.reply_text(help_text,
                       reply_markup=keyboard,
                       )


@Client.on_callback_query(filters.regex("^help$"))
async def help(c: Client, m: CallbackQuery):
    keyboard = ikb([
        [("Comandos", "help_cmds"),
         ("Filtros", "help_regex")],
        [("<- Voltar", "start_back")]
    ])
    await m.message.edit_text(help_text,
                              reply_markup=keyboard,
                              )


@Client.on_callback_query(filters.regex("^help_regex$"))
async def help_regex(c: Client, m: CallbackQuery):
    keyboard = ikb([[("<- Voltar", "help")]])
    await m.message.edit_text(
        "<b>O PyKorone também possui alguns filtros com respostas pré-definidas:</b>\n\n"
        "<b>types:</b>\n"
        " - <code>messages</code>\n"
        " - <code>assistant</code>\n"
        " - <code>interactions</code>\n\n"
        "Você pode obter ajuda para um tipo de filtro específico usando <code>/help {type}</code>",
        reply_markup=keyboard,
    )


@Client.on_callback_query(filters.regex("^help_cmds$"))
async def help_cmds(c: Client, m: CallbackQuery):
    keyboard = ikb([[("<- Voltar", "help")]])
    await m.message.edit_text(
        "<b>Aqui estão alguns dos meus comandos:</b>\n"
        "• <code>/start</code>: Envia a mensagem inicial do bot.\n"
        "• <code>/help</code>: Envia a mensagem de ajuda do bot.\n"
        "• <code>/ping</code>: Envia o ping do bot.\n"
        "• <code>/echo</code>: Faz um eco com o que você escrever na frente do comando.\n"
        "• <code>/cat</code>: Envia uma imagem de um gatinho aleatório.\n"
        "• <code>/py</code>: Envia algumas informações técnicas do bot.\n"
        "• <code>/copy</code>: O bot copia a mensagem que você responder com este comando.\n"
        "• <code>/user</code>: Obtêm informações básicas de um usuário.",
        reply_markup=keyboard,
    )


@Client.on_callback_query(filters.regex("^about$"))
async def about(c: Client, m: CallbackQuery):
    keyboard = ikb([[("<- Voltar", "start_back")]])
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
        "Oi, eu sou o <b>Korone</b>, um bot interativo "
        "que adora participar de grupos!",
        reply_markup=keyboard,
    )
