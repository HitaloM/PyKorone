# Translator

This module uses [DeepL](https://www.deepl.com/en/whydeepl) to translate text between languages. DeepL is a high quality translation service that uses neural networks to provide accurate translations.

## Commands

- `/tr (?source):(?target) (?text)`: Translate text from one language to another, can also be used to reply to a message. If the source language is not specified, it is automatically automatically detected. If the target language is not specified, it defaults to English.

```{note}
**Supported source languages**: `BG`, `CS`, `DA`, `DE`, `EL`, `EN`, `ES`, `ET`,
`FI`, `FR`, `HU`, `ID`, `IT`, `JA`, `KO`, `LT`, `LV`, `NB`, `NL`, `PL`, `PT`,
`RO`, `RU`, `SK`, `SL`, `SV`, `TR`, `UK`, `ZH`

**Supported target languages**: `BG`, `CS`, `DA`, `DE`, `EL`, `EN`, `EN-GB`,
`EN-US`, `ES`, `ET`, `FI`, `FR`, `HU`, `ID`, `IT`, `JA`, `KO`, `LT`, `LV`, `NB`,
`NL`, `PL`, `PT`, `PT-BR`, `PT-PT`, `RO`, `RU`, `SK`, `SL`, `SV`, `TR`, `UK`, `ZH`

[DeepL API Docs - Supported languages](https://developers.deepl.com/docs/resources/supported-languages)
```

### Examples

- Translate _Hello, world!_ from English to Portuguese (Brazilian):
  - `/tr en:pt-br Hello, world!`

- Translate _Hallo, Welt!_ from German to English:
  - `/tr en Hallo, Welt!`

```{warning}
The free version of the DeepL API has a limit of 500,000 characters per month. If the bot reaches this limit, it will stop translating until the next month. If this happens, the bot will inform you about the limit when you try to translate a text.
```
