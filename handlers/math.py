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

import re
import aionewton

from pyrogram import Client, filters
from pyrogram.types import Message

from config import prefix

done_text = "<b>Expressão:</b> <code>{}</code>\n<b>Resultado:</b> <code>{}</code>"


@Client.on_message(filters.command("simplify", prefix))
async def simplify(c: Client, m: Message):
    calc = re.sub('^/simplify ', '', m.text.html)
    result = await aionewton.simplify(calc)
    await m.reply_text((done_text).format(calc, result))


@Client.on_message(filters.command("factor", prefix))
async def factor(c: Client, m: Message):
    calc = re.sub('^/factor ', '', m.text.html)
    result = await aionewton.factor(calc)
    await m.reply_text((done_text).format(calc, result))


@Client.on_message(filters.command("derive", prefix))
async def derive(c: Client, m: Message):
    calc = re.sub('^/derive ', '', m.text.html)
    result = await aionewton.derive(calc)
    await m.reply_text((done_text).format(calc, result))


@Client.on_message(filters.command("integrate", prefix))
async def integrate(c: Client, m: Message):
    calc = re.sub('^/integrate ', '', m.text.html)
    result = await aionewton.integrate(calc)
    await m.reply_text((done_text).format(calc, result))


@Client.on_message(filters.command("zeroes", prefix))
async def zeroes(c: Client, m: Message):
    calc = re.sub('^/zeroes ', '', m.text.html)
    result = await aionewton.zeroes(calc)
    await m.reply_text((done_text).format(calc, result))


@Client.on_message(filters.command("tangent", prefix))
async def tangent(c: Client, m: Message):
    calc = re.sub('^/tangent ', '', m.text.html)
    result = await aionewton.tangent(calc)
    await m.reply_text((done_text).format(calc, result))


@Client.on_message(filters.command("area", prefix))
async def area(c: Client, m: Message):
    calc = re.sub('^/area ', '', m.text.html)
    result = await aionewton.area(calc)
    await m.reply_text((done_text).format(calc, result))


@Client.on_message(filters.command("cos", prefix))
async def xos(c: Client, m: Message):
    calc = re.sub('^/cos ', '', m.text.html)
    result = await aionewton.cos(calc)
    await m.reply_text((done_text).format(calc, result))


@Client.on_message(filters.command("sin", prefix))
async def sin(c: Client, m: Message):
    calc = re.sub('^/sin ', '', m.text.html)
    result = await aionewton.sin(calc)
    await m.reply_text((done_text).format(calc, result))


@Client.on_message(filters.command("tan", prefix))
async def tan(c: Client, m: Message):
    calc = re.sub('^/tan ', '', m.text.html)
    result = await aionewton.tan(calc)
    await m.reply_text((done_text).format(calc, result))


@Client.on_message(filters.command("accos", prefix))
async def accos(c: Client, m: Message):
    calc = re.sub('^/accos ', '', m.text.html)
    result = await aionewton.accos(calc)
    await m.reply_text((done_text).format(calc, result))


@Client.on_message(filters.command("arcsin", prefix))
async def arcsin(c: Client, m: Message):
    calc = re.sub('^/arcsin ', '', m.text.html)
    result = await aionewton.arcsin(calc)
    await m.reply_text((done_text).format(calc, result))


@Client.on_message(filters.command("arctan", prefix))
async def arctan(c: Client, m: Message):
    calc = re.sub('^/arctan ', '', m.text.html)
    result = await aionewton.arctan(calc)
    await m.reply_text((done_text).format(calc, result))


@Client.on_message(filters.command("abs", prefix))
async def abs(c: Client, m: Message):
    calc = re.sub('^/abs ', '', m.text.html)
    result = await aionewton.abs(calc)
    await m.reply_text((done_text).format(calc, result))


@Client.on_message(filters.command("log", prefix))
async def log(c: Client, m: Message):
    calc = re.sub('^/log ', '', m.text.html)
    result = await aionewton.log(calc)
    await m.reply_text((done_text).format(calc, result))


@Client.on_message(filters.command("math", prefix))
async def math_help(c: Client, m: Message):
    await m.reply_text(
    """
<b>Resolva problemas matemáticos complexos usando https://newton.now.sh</b>

 - /simplify: simplificar <code>/simplify 2^2+2(2)</code>
 - /factor: Fator <code>/factor x^2+2x</code>
 - /derive: derivar <code>/derive x^2+2x</code>
 - /integrate: integrar <code>/integrate x^2+2x</code>
 - /zeros: Encontre 0s <code>/zeroes x^2+2x</code>
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
