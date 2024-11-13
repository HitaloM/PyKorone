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


def lang_code_to_language(lang_code: str) -> Language:
    # IsoCode639_1 is stupid enum, it doesn't support any kind of magic getter, therefore we get its attribute
    return Language.from_iso_code_639_1(getattr(IsoCode639_1, lang_code.upper()))


def build_language_detector() -> LanguageDetector:
    return (
        LanguageDetectorBuilder.from_languages(
            *tuple(lang_code_to_language(lang_code) for lang_code in i18n.locales_iso_639_1)
        )
        .with_preloaded_language_models()
        .build()
    )


DETECTOR = build_language_detector()


def detect_languages(text: str) -> list[ConfidenceValue]:
    confidences = DETECTOR.compute_language_confidence_values(text)
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
