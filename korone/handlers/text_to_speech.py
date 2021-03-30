from pyrogram.types import Message
from pyrogram import Client, filters
from pydub import AudioSegment
from speech_recognition import AudioFile, Recognizer, UnknownValueError, RequestError
from os import remove
from korone.handlers import COMMANDS_HELP

GROUP = "text_to_speech"
TEMP_DL_DIR = "./temp/"

COMMANDS_HELP[GROUP] = {
    "name": "Audio",
    "text": "Meus comandos relacionados com audio",
    "filters": {},
    "help": True,
}

@Client.on_message(filters.int(filter=r"Korone, que disse ele", group=GROUP))
async def read_him(c: Client, msg: Message):
    filename, file_format = (None,) * 2

    if msg.voice:
        voice_note = True
        if not voice_note:
            await msg.reply(":c Não sei, não parece que seja uma mensagem de voz")
            return
        filename = TEMP_DL_DIR + "audio." + file_format
        await msg.reply("Deixa eu escutar ^_^")
        try:
            await c.download_media(message=msg, file_name=filename)
        except Exception as e:
            await msg.reply("Algo correu mal. Esse audio não tem algo que eu entenda >_<")
            return
    else:
        await msg.reply(":c Não sei, não parece que seja uma mensagem de voz")
        return

    try:
        audio_file = AudioSegment.from_file(filename, file_format)
        audio_wav = TEMP_DL_DIR + "audio.wav"
        audio_file.export(audio_wav, "wav")

        r = Recognizer()
        with AudioFile(audio_wav) as source:
            audio = r.record(source)
        result = r.recognize_google(audio, language="pt-BR")
        text = f"Pareceu-me que ele disse: \n\n"
        text += f"__{result}__"
        await msg.reply(text)
    except UnknownValueError:
        await msg.reply("Não consegui reconhecer o idioma que ele falou :/")
    except RequestError as re:
        await msg.reply("Não consegui reconhecer o idioma que ele falou :/")
    except Exception as e:
        await msg.reply("Meu sistema falhou inexplicavelmente")

    try:
        remove(filename)
        remove(audio_wav)
    except Exception as e:
        pass
    return
