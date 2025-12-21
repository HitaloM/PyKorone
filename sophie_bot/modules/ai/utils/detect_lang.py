from __future__ import annotations

from typing import Iterable, Optional

from lingua import (
    ConfidenceValue,
    IsoCode639_1,
    Language,
    LanguageDetector,
    LanguageDetectorBuilder,
)

from sophie_bot.middlewares import i18n
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.logger import log

_FALLBACK_LANGUAGES: tuple[Language, ...] = (Language.ENGLISH,)
_detector: Optional[LanguageDetector] = None


def lang_code_to_language(lang_code: str) -> Language:
    # IsoCode639_1 is a stupid enum, it doesn't support any kind of magic getter, therefore we get its attribute
    return Language.from_iso_code_639_1(getattr(IsoCode639_1, lang_code.upper()))


def _languages_from_locales(locales: Iterable[str]) -> tuple[Language, ...]:
    languages = tuple(lang_code_to_language(lang_code) for lang_code in locales)

    if not languages:
        log.warning(
            "Language detector: no locales available, falling back to default languages.",
        )
        return _FALLBACK_LANGUAGES

    return languages


def build_language_detector(locales: Optional[Iterable[str]] = None) -> LanguageDetector:
    language_codes = tuple(locales) if locales is not None else i18n.locales_iso_639_1
    languages = _languages_from_locales(language_codes)

    return LanguageDetectorBuilder.from_languages(*languages).with_preloaded_language_models().build()


def get_detector() -> LanguageDetector:
    global _detector

    if _detector is None:
        _detector = build_language_detector()

    return _detector


def detect_languages(text: str) -> list[ConfidenceValue]:
    detector = get_detector()

    confidences = detector.compute_language_confidence_values(text)
    log.debug("detect_languages", confidence=confidences)
    return confidences


def is_text_language(text: str, language: Language) -> bool:
    confidences = detect_languages(text)

    try:
        confidence = next(confidence for confidence in confidences if confidence.language == language)
    except StopIteration:
        raise SophieException("Language detection failed! No required language detected in the confidence list.")

    log.debug("is_text_language", confidence=confidence)
    return confidence.value >= 0.35
