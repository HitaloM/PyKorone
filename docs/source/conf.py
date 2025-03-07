# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import sys
from datetime import UTC, datetime
from pathlib import Path

docs_dir = Path(__file__).parent.parent
sys.path.insert(0, Path("../../src").resolve().as_posix())

import korone  # noqa: E402

project = "PyKorone"
author = "Hitalo M."
date_time = datetime.now(tz=UTC)
date = date_time.date()
copyright = f"{date.year}, {author}"
release = korone.__version__.split(" ")[0]

extensions = ["myst_parser", "sphinxcontrib.towncrier"]

html_use_modindex = False
html_use_index = False

master_doc = "index"
source_suffix = [".rst", ".md"]
autodoc_member_order = "bysource"
autodoc_typehints = "none"
pygments_style = "sphinx"

towncrier_draft_autoversion_mode = "draft"
towncrier_draft_include_empty = True
towncrier_draft_working_directory = Path(__file__).parent.parent.parent

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_static_path = ["_static"]
html_logo = "_static/img/korone-alone.png"
html_theme = "furo"
html_title = f"{project} {release} documentation"
html_last_updated_fmt = f"{date_time.strftime('%d/%m/%Y, %H:%M:%S')} UTC"
html_copy_source = False

html_theme_options = {
    "navigation_with_keys": True,
    # "announcement": (
    #     "Korone is currently under development and breaking changes may "
    #     "be introduced frequently. Please monitor the commits for updates: "
    #     "<a href='https://github.com/HitaloM/PyKorone/commits/main/'>Commits</a>."
    # ),
    "footer_icons": [  # these icons are getten from: https://react-icons.github.io/react-icons/
        {
            "name": "Telegram",
            "url": "https://t.me/PyKorone/",
            "html": (
                '<svg stroke="currentColor" fill="currentColor" stroke-width="0" '
                'viewBox="0 0 16 16" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg">'
                '<path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM8.287 5.906c-.778.324-2.334.994'
                "-4.666 2.01-.378.15-.577.298-.595.442-.03.243.275.339.69.47l.175.055c.408.133."
                "958.288 1.243.294.26.006.549-.1.868-.32 2.179-1.471 3.304-2.214 3.374-2.23.0"
                "5-.012.12-.026.166.016.047.041.042.12.037.141-.03.129-1.227 1.241-1.846 1.81"
                "7-.193.18-.33.307-.358.336a8.154 8.154 0 0 1-.188.186c-.38.366-.664.64.015 1.08"
                "8.327.216.589.393.85.571.284.194.568.387.936.629.093.06.183.125.27.187.331.23"
                "6.63.448.997.414.214-.02.435-.22.547-.82.265-1.417.786-4.486.906-5.751a1.426 "
                "1.426 0 0 0-.013-.315.337.337 0 0 0-.114-.217.526.526 0 0 0-.31-.093c-.3.005-.7"
                '63.166-2.984 1.09z"></path></svg>'
            ),
            "class": "",
        },
        {
            "name": "GitHub",
            "url": "https://github.com/HitaloM/PyKorone/",
            "html": (
                '<svg stroke="currentColor" fill="currentColor" stroke-width="0" '
                'viewBox="0 0 16 16"><path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 '
                "2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.4"
                "9-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23"
                ".82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 "
                "0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.2"
                "7 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.5"
                "1.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 "
                '1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z">'
                "</path></svg>"
            ),
            "class": "",
        },
    ],
}
