from pydantic import BaseModel

AISAVE_JSON_SCHEMA = {
    "name": "chat_note",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": (
                    "The main text content of the chat note. Speak ONLY about the note topic! Keep it as short as "
                    "possible, about 10 lines of text are"
                    " the maximum. DO NOT use HTML/Markdown! Free to use emojis and newlines."
                ),
            },
            "description": {"type": "string", "description": "A very short description of the chat note."},
            "group": {
                "type": "string",
                "description": (
                    "The keyword of the topic of note belongs to. No spaces or special characters, maximum 8 symbols."
                ),
            },
            "notenames": {
                "type": "array",
                "description": (
                    "An array of UNIQUE keywords (no spaces) of note title, limited to a maximum of 2. Users would "
                    "need to"
                    " call one of keywords to access this note. Write the best most specific keyword matching the text"
                    " content and the aliases for users to choose.Make it as short as possible, if that's possible -"
                    " use one word, else - divide the words with _"
                ),
                "items": {"type": "string", "description": "A keyword that best describes the content of the note."},
            },
        },
        "required": ["text", "description", "group", "notenames"],
        "additionalProperties": False,
        "$defs": {},
    },
}


class AISaveResponseSchema(BaseModel):
    text: str
    description: str
    group: str
    notenames: list[str]
