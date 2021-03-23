# This file is part of Korone (Telegram Bot)
# Copyright (C) 2021 AmanoTeam

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

import aionewton

from pyrogram import Client, filters
from pyrogram.types import Message

from bot.handlers import COMMANDS_HELP

GROUP = "math"

COMMANDS_HELP[GROUP] = {
    "name": "Matemática",
    "text": "Esse é meu módulo de matemática, cuidado para não perder a cabeça.",
    "commands": {},
    "help": True,
}

done_text = "<b>Expressão:</b> <code>{}</code>\n<b>Resultado:</b> <code>{}</code>"


@Client.on_message(filters.cmd("simplify (?P<calc>.+)", group=GROUP))
async def simplify(c: Client, m: Message):
    calc = m.matches[0]["calc"]
    result = await aionewton.simplify(calc)
    await m.reply_text((done_text).format(calc, result))


@Client.on_message(filters.cmd("factor (?P<calc>.+)", group=GROUP))
async def factor(c: Client, m: Message):
    calc = m.matches[0]["calc"]
    result = await aionewton.factor(calc)
    await m.reply_text((done_text).format(calc, result))


@Client.on_message(filters.cmd("derive (?P<calc>.+)", group=GROUP))
async def derive(c: Client, m: Message):
    calc = m.matches[0]["calc"]
    result = await aionewton.derive(calc)
    await m.reply_text((done_text).format(calc, result))


@Client.on_message(filters.cmd("integrate (?P<calc>.+)", group=GROUP))
async def integrate(c: Client, m: Message):
    calc = m.matches[0]["calc"]
    result = await aionewton.integrate(calc)
    await m.reply_text((done_text).format(calc, result))


@Client.on_message(filters.cmd("zeroes (?P<calc>.+)", group=GROUP))
async def zeroes(c: Client, m: Message):
    calc = m.matches[0]["calc"]
    result = await aionewton.zeroes(calc)
    await m.reply_text((done_text).format(calc, result))


@Client.on_message(filters.cmd("tangent (?P<calc>.+)", group=GROUP))
async def tangent(c: Client, m: Message):
    calc = m.matches[0]["calc"]
    result = await aionewton.tangent(calc)
    await m.reply_text((done_text).format(calc, result))


@Client.on_message(filters.cmd("area (?P<calc>.+)", group=GROUP))
async def area(c: Client, m: Message):
    calc = m.matches[0]["calc"]
    result = await aionewton.area(calc)
    await m.reply_text((done_text).format(calc, result))


@Client.on_message(filters.cmd("cos (?P<calc>.+)", group=GROUP))
async def xos(c: Client, m: Message):
    calc = m.matches[0]["calc"]
    result = await aionewton.cos(calc)
    await m.reply_text((done_text).format(calc, result))


@Client.on_message(filters.cmd("sin (?P<calc>.+)", group=GROUP))
async def sin(c: Client, m: Message):
    calc = m.matches[0]["calc"]
    result = await aionewton.sin(calc)
    await m.reply_text((done_text).format(calc, result))


@Client.on_message(filters.cmd("tan (?P<calc>.+)", group=GROUP))
async def tan(c: Client, m: Message):
    calc = m.matches[0]["calc"]
    result = await aionewton.tan(calc)
    await m.reply_text((done_text).format(calc, result))


@Client.on_message(filters.cmd("accos (?P<calc>.+)", group=GROUP))
async def accos(c: Client, m: Message):
    calc = m.matches[0]["calc"]
    result = await aionewton.accos(calc)
    await m.reply_text((done_text).format(calc, result))


@Client.on_message(filters.cmd("arcsin (?P<calc>.+)", group=GROUP))
async def arcsin(c: Client, m: Message):
    calc = m.matches[0]["calc"]
    result = await aionewton.arcsin(calc)
    await m.reply_text((done_text).format(calc, result))


@Client.on_message(filters.cmd("arctan (?P<calc>.+)", group=GROUP))
async def arctan(c: Client, m: Message):
    calc = m.matches[0]["calc"]
    result = await aionewton.arctan(calc)
    await m.reply_text((done_text).format(calc, result))


@Client.on_message(filters.cmd("abs (?P<calc>.+)", group=GROUP))
async def abs(c: Client, m: Message):
    calc = m.matches[0]["calc"]
    result = await aionewton.abs(calc)
    await m.reply_text((done_text).format(calc, result))


@Client.on_message(filters.cmd("log (?P<calc>.+)", group=GROUP))
async def log(c: Client, m: Message):
    calc = m.matches[0]["calc"]
    result = await aionewton.log(calc)
    await m.reply_text((done_text).format(calc, result))


@Client.on_message(
    filters.cmd(
        command="math",
        action="Manual de uso dos meus comandos matemáticos.",
        group=GROUP,
    )
)
async def math_help(c: Client, m: Message):
    await m.reply_text(
        """
<b>Resolva problemas matemáticos complexos usando https://newton.now.sh</b>

 - /simplify: simplificar <code>/simplify 2^2+2(2)</code>
 - /factor: Fator <code>/factor x^2+2x</code>
 - /derive: derivar <code>/derive x^2+2x</code>
 - /integrate: integrar <code>/integrate x^2+2x</code>
 - /zeroes: Encontre 0s <code>/zeroes x^2+2x</code>
 - /tangent: Encontre Tangente <code>/tangent 2lx^3</code>
 - /area: Área sob a curva <code>/area 2:4lx^3</code>
 - /cos: Cosseno <code>/cos pi</code>
 - /sin: Seno <code>/sin 0</code>
 - /tan: Tangente <code>/tan 0</code>
 - /arccos: Cosseno inverso <code>/arccos 1</code>
 - /arcsin: Seno inverso <code>/arcsin 0</code>
 - /arctan: Tangente inversa <code>/arctan 0</code>
 - /abs: Valor absoluto <code>/abs -1</code>
 - /log: Logaritmo <code>/log 2l8</code>

<i>Lembre-se:</i> para encontrar a linha tangente de uma função em um determinado valor x, envie a solicitação como c|f(x), onde c é o valor x fornecido e f(x) é a expressão da função, o separador é uma barra vertical '|'. Consulte a tabela acima para obter um exemplo de solicitação.

Para encontrar a área sob uma função, envie a solicitação como c:d|f(x) onde c é o valor inicial de x, d é o valor final de x e f(x) é a função sob a qual você deseja a curva entre os dois valores de x.

Para calcular frações, insira expressões como numerador(sobre)denominador. Por exemplo, para processar 2/4, você deve enviar sua expressão como 2(sobre)4. A expressão do resultado será em notação matemática padrão (1/2, 3/4).
    """
    )
