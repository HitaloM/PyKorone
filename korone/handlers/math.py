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

from urllib.parse import quote

from pyrogram import filters
from pyrogram.types import Message

from korone.handlers import COMMANDS_HELP
from korone.korone import Korone
from korone.utils import http

GROUP = "math"

COMMANDS_HELP[GROUP] = {
    "name": "Matemática",
    "text": "Esse é meu módulo de matemática, cuidado para não perder a cabeça.",
    "commands": {},
    "help": True,
}

done_text: str = "<b>Expressão:</b> <code>{}</code>\n<b>Resultado:</b> <code>{}</code>"
err_text: str = "Algo deu errado na requisição da API, tente novamente mais tarde..."

url: str = "https://newton.now.sh/api/v2/{}/{}"


def encoded(expression):
    return quote(expression, safe="")


@Korone.on_message(filters.cmd("simplify (?P<calc>.+)", group=GROUP))
async def simplify_math(c: Korone, m: Message):
    calc = m.matches[0]["calc"]
    req = await http.get(url.format("simplify", encoded(calc)))
    if req.status_code == 200:
        r = req.json()
    else:
        await m.reply_text(err_text)
        return
    await m.reply_text((done_text).format(calc, r["result"]))


@Korone.on_message(filters.cmd("factor (?P<calc>.+)", group=GROUP))
async def factor_math(c: Korone, m: Message):
    calc = m.matches[0]["calc"]
    req = await http.get(url.format("factor", encoded(calc)))
    if req.status_code == 200:
        r = req.json()
    else:
        await m.reply_text(err_text)
        return
    await m.reply_text((done_text).format(calc, r["result"]))


@Korone.on_message(filters.cmd("derive (?P<calc>.+)", group=GROUP))
async def derive_math(c: Korone, m: Message):
    calc = m.matches[0]["calc"]
    req = await http.get(url.format("derive", encoded(calc)))
    if req.status_code == 200:
        r = req.json()
    else:
        await m.reply_text(err_text)
        return
    await m.reply_text((done_text).format(calc, r["result"]))


@Korone.on_message(filters.cmd("integrate (?P<calc>.+)", group=GROUP))
async def integrate_math(c: Korone, m: Message):
    calc = m.matches[0]["calc"]
    req = await http.get(url.format("integrate", encoded(calc)))
    if req.status_code == 200:
        r = req.json()
    else:
        await m.reply_text(err_text)
        return
    await m.reply_text((done_text).format(calc, r["result"]))


@Korone.on_message(filters.cmd("zeroes (?P<calc>.+)", group=GROUP))
async def zeroes_math(c: Korone, m: Message):
    calc = m.matches[0]["calc"]
    req = await http.get(url.format("zeroes", encoded(calc)))
    if req.status_code == 200:
        r = req.json()
    else:
        await m.reply_text(err_text)
        return
    await m.reply_text((done_text).format(calc, r["result"]))


@Korone.on_message(filters.cmd("tangent (?P<calc>.+)", group=GROUP))
async def tangent_math(c: Korone, m: Message):
    calc = m.matches[0]["calc"]
    req = await http.get(url.format("tangent", encoded(calc)))
    if req.status_code == 200:
        r = req.json()
    else:
        await m.reply_text(err_text)
        return
    await m.reply_text((done_text).format(calc, r["result"]))


@Korone.on_message(filters.cmd("area (?P<calc>.+)", group=GROUP))
async def area_math(c: Korone, m: Message):
    calc = m.matches[0]["calc"]
    req = await http.get(url.format("area", encoded(calc)))
    if req.status_code == 200:
        r = req.json()
    else:
        await m.reply_text(err_text)
        return
    await m.reply_text((done_text).format(calc, r["result"]))


@Korone.on_message(filters.cmd("cos (?P<calc>.+)", group=GROUP))
async def xos_math(c: Korone, m: Message):
    calc = m.matches[0]["calc"]
    req = await http.get(url.format("cos", encoded(calc)))
    if req.status_code == 200:
        r = req.json()
    else:
        await m.reply_text(err_text)
        return
    await m.reply_text((done_text).format(calc, r["result"]))


@Korone.on_message(filters.cmd("sin (?P<calc>.+)", group=GROUP))
async def sin_math(c: Korone, m: Message):
    calc = m.matches[0]["calc"]
    req = await http.get(url.format("sin", encoded(calc)))
    if req.status_code == 200:
        r = req.json()
    else:
        await m.reply_text(err_text)
        return
    await m.reply_text((done_text).format(calc, r["result"]))


@Korone.on_message(filters.cmd("tan (?P<calc>.+)", group=GROUP))
async def tan_math(c: Korone, m: Message):
    calc = m.matches[0]["calc"]
    req = await http.get(url.format("tan", encoded(calc)))
    if req.status_code == 200:
        r = req.json()
    else:
        await m.reply_text(err_text)
        return
    await m.reply_text((done_text).format(calc, r["result"]))


@Korone.on_message(filters.cmd("accos (?P<calc>.+)", group=GROUP))
async def accos_math(c: Korone, m: Message):
    calc = m.matches[0]["calc"]
    req = await http.get(url.format("accos", encoded(calc)))
    if req.status_code == 200:
        r = req.json()
    else:
        await m.reply_text(err_text)
        return
    await m.reply_text((done_text).format(calc, r["result"]))


@Korone.on_message(filters.cmd("arcsin (?P<calc>.+)", group=GROUP))
async def arcsin_math(c: Korone, m: Message):
    calc = m.matches[0]["calc"]
    req = await http.get(url.format("arcsin", encoded(calc)))
    if req.status_code == 200:
        r = req.json()
    else:
        await m.reply_text(err_text)
        return
    await m.reply_text((done_text).format(calc, r["result"]))


@Korone.on_message(filters.cmd("arctan (?P<calc>.+)", group=GROUP))
async def arctan_math(c: Korone, m: Message):
    calc = m.matches[0]["calc"]
    req = await http.get(url.format("arctan", encoded(calc)))
    if req.status_code == 200:
        r = req.json()
    else:
        await m.reply_text(err_text)
        return
    await m.reply_text((done_text).format(calc, r["result"]))


@Korone.on_message(filters.cmd("abs (?P<calc>.+)", group=GROUP))
async def abs_math(c: Korone, m: Message):
    calc = m.matches[0]["calc"]
    req = await http.get(url.format("abs", encoded(calc)))
    if req.status_code == 200:
        r = req.json()
    else:
        await m.reply_text(err_text)
        return
    await m.reply_text((done_text).format(calc, r["result"]))


@Korone.on_message(filters.cmd("log (?P<calc>.+)", group=GROUP))
async def log_math(c: Korone, m: Message):
    calc = m.matches[0]["calc"]
    req = await http.get(url.format("log", encoded(calc)))
    if req.status_code == 200:
        r = req.json()
    else:
        await m.reply_text(err_text)
        return
    await m.reply_text((done_text).format(calc, r["result"]))


@Korone.on_message(
    filters.cmd(
        command="math",
        action="Manual de uso dos meus comandos matemáticos.",
        group=GROUP,
    )
)
async def math_help(c: Korone, m: Message):
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
