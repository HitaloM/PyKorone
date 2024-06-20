from aiogram import types
from aiogram.filters import Filter


class NoArgs(Filter):
    key = "no_args"

    def __init__(self, no_args):
        self.no_args = no_args

    async def __call__(self, message: types.Message):
        if not len(message.text.split(" ")) > 1:
            return True


class HasArgs(Filter):
    key = "has_args"

    def __init__(self, has_args):
        self.has_args = has_args

    async def __call__(self, message: types.Message):
        if len(message.text.split(" ")) > 1:
            return True
