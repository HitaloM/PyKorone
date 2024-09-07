# Translator

This module uses [DeepL](https://www.deepl.com/en/whydeepl) to translate text from one language to another. DeepL is a high-quality translation service that uses neural networks to translate text.

## Commands

- `/tr (?source):(?target) (?text)`: Translate text from one language to another, can also be used to reply to a message. If the source language is not specified, it is automatically automatically detected. If the target language is not specified, it defaults to English.

```{seealso}
For a list of supported languages, check the [DeepL API Docs - Supported languages](https://developers.deepl.com/docs/resources/supported-languages).
```

```{warning}
The free version of the DeepL API has a limit of 500,000 characters per month. If the bot reaches this limit, it will stop translating until the next month. If this happens, the bot will inform you about the limit when you try to translate a text.
```

### Examples

- Send a message with the translation of _Hello, world!_ from English to Brazilian Portuguese.
  > `/tr en:pt-br Hello, world!`

- Send a message with the translation of _Hallo, Welt!_ from German to English.
  > `/tr en Hallo, Welt!`
