# SPDX-License-Identifier: GPL-3.0
# Copyright (C) 2020 Cezar H. <https://github.com/usernein>

import html


class LangsFormatMap(dict):
    def __getitem__(self, key):
        if key in self:
            self.used.append(key)
            if type(self.get(key)) is str:
                return html.escape(self.get(key))
        else:
            return self.__missing__(key)

    def __missing__(self, key):
        if self.debug:
            print(
                f"Key '{key}' is missing on the string '{self.string}', language '{self.code}'"
            )
        return "{" + key + "}"


class LangString(str):
    def __call__(self, **kwargs):
        mapping = LangsFormatMap(**kwargs)
        mapping.string = self.key
        mapping.code = self.code
        mapping.debug = self.debug
        mapping.used = []
        formatted = self.format_map(mapping)

        not_used = [key for key in kwargs if key not in mapping.used]
        if self.debug and len(not_used):
            for key in not_used:
                print(
                    f"The parameter '{key}' was passed to the string '{self.key}' (language '{self.code}') but was not used"
                )
            print("")
        return formatted


class Langs:
    strings = {}
    available = []
    code = "en"
    debug = True

    def __init__(self, strings=None, debug=True, **kwargs):
        if strings is None:
            strings = {}
        self.strings = strings

        if not kwargs and not strings:
            raise ValueError(
                "Pass the language codes and their objects (dictionaries containing the strings) as keyword arguments (language=dict)"
            )

        for language_code, strings_object in kwargs.items():
            self.strings[language_code] = strings_object
            self.strings[language_code].update({"LANGUAGE_CODE": language_code})

        # self.strings = {'en':{'start':'Hi {name}!'}}
        self.available = list(self.strings.keys())
        self.code = "en" if "en" in self.available else self.available[0]
        self.debug = debug

    def __getattr__(self, key):
        try:
            result = self.strings[self.code][key]
        except BaseException:
            result = key
        obj = LangString(result)
        obj.key = key
        obj.code = self.code
        obj.debug = self.debug
        return obj

    def get_language(self, language_code):
        lang_copy = Langs(strings=self.strings)
        lang_copy.code = language_code
        return lang_copy
