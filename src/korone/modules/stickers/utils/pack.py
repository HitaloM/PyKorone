import hashlib


def default_pack_title(first_name: str | None) -> str:
    base_name = (first_name or "User").strip() or "User"
    return f"{base_name[:35]}'s Stolen Pack"


def normalize_pack_title(title: str) -> str:
    normalized = title.strip()
    if not normalized:
        return "Stolen Pack"
    return normalized[:64]


def build_pack_id(user_id: int, pack_title: str, bot_username: str | None) -> str:
    username = (bot_username or "bot").strip()
    user_hash = hashlib.sha1(str(user_id).encode("utf-8")).hexdigest()
    title_hash = hashlib.sha1(pack_title.lower().encode("utf-8")).hexdigest()
    return f"K{title_hash[:10]}{user_hash[:10]}_by_{username}"
