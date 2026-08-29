from dataclasses import dataclass
from difflib import SequenceMatcher
from unicodedata import combining, normalize

from korone.modules.help.utils.extract_info import HELP_MODULES, ModuleHelp

MAX_SUGGESTIONS = 5
MIN_SIMILARITY = 0.55

type ModuleMatch = tuple[str, ModuleHelp]


@dataclass(frozen=True, slots=True)
class ModuleSearchResult:
    exact: ModuleMatch | None
    suggestions: tuple[ModuleMatch, ...]


def normalize_module_query(value: str) -> str:
    decomposed = normalize("NFKD", value.casefold())
    without_accents = "".join(character for character in decomposed if not combining(character))
    return " ".join("".join(character if character.isalnum() else " " for character in without_accents).split())


def _module_terms(module_name: str, module: ModuleHelp) -> tuple[str, ...]:
    return tuple(dict.fromkeys((normalize_module_query(module_name), normalize_module_query(str(module.name)))))


def _match_score(query: str, terms: tuple[str, ...]) -> float | None:
    best_score: float | None = None
    for term in terms:
        if term.startswith(query):
            score = 2.0 + len(query) / len(term)
        elif query in term:
            score = 1.0 + len(query) / len(term)
        elif len(query) >= 3:
            score = SequenceMatcher(a=query, b=term).ratio()
            if score < MIN_SIMILARITY:
                continue
        else:
            continue

        best_score = score if best_score is None else max(best_score, score)
    return best_score


def search_help_modules(query: str) -> ModuleSearchResult:
    normalized_query = normalize_module_query(query)
    if not normalized_query:
        return ModuleSearchResult(exact=None, suggestions=())

    public_modules = [(name, module) for name, module in HELP_MODULES.items() if not module.exclude_public]
    exact_matches = [
        (name, module) for name, module in public_modules if normalized_query in _module_terms(name, module)
    ]
    if len(exact_matches) == 1:
        return ModuleSearchResult(exact=exact_matches[0], suggestions=())

    ranked_matches: list[tuple[float, str, ModuleHelp]] = []
    for name, module in public_modules:
        if (score := _match_score(normalized_query, _module_terms(name, module))) is not None:
            ranked_matches.append((score, name, module))

    ranked_matches.sort(key=lambda match: (-match[0], str(match[2].name).casefold(), match[1]))
    suggestions = tuple((name, module) for _, name, module in ranked_matches[:MAX_SUGGESTIONS])
    return ModuleSearchResult(exact=None, suggestions=suggestions)
