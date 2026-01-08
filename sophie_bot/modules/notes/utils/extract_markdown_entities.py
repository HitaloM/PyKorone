# Copyright https://github.com/LonamiWebs/Telethon
# https://github.com/LonamiWebs/Telethon/blob/v1/LICENSE

import re
import struct

from aiogram.types import MessageEntity

DEFAULT_DELIMITERS = {
    "**": "bold",
    "__": "italic",
    "~~": "strikethrough",
    "++": "underline",
    "`": "code",
    "```": "pre",
}

DEFAULT_URL_RE = re.compile(r"\[([\S\s]+?)\]\((.+?)\)")
DEFAULT_URL_FORMAT = "[{0}]({1})"


def overlap(a, b, x, y):
    return max(a, x) < min(b, y)


def strip_text(text: str, entities: list[MessageEntity]) -> str:
    """
    Strips whitespace from the given surrogated text modifying the provided
    entities, also removing any empty (0-length) entities.

    This assumes that the length of entities is greater or equal to 0, and
    that no entity is out of bounds.
    """
    if not entities:
        return text.strip()

    len_ori = len(text)
    text = text.lstrip()
    left_offset = len_ori - len(text)
    text = text.rstrip()
    len_final = len(text)

    for i in reversed(range(len(entities))):
        e = entities[i]
        if e.length == 0:
            del entities[i]
            continue

        if e.offset + e.length > left_offset:
            if e.offset >= left_offset:
                #  0 1|2 3 4 5       |       0 1|2 3 4 5
                #     ^     ^        |          ^
                #   lo(2)  o(5)      |      o(2)/lo(2)
                e.offset -= left_offset
                #     |0 1 2 3       |          |0 1 2 3
                #           ^        |          ^
                #     o=o-lo(3=5-2)  |    o=o-lo(0=2-2)
            else:
                # e.offset < left_offset and e.offset + e.length > left_offset
                #  0 1 2 3|4 5 6 7 8 9 10
                #   ^     ^           ^
                #  o(1) lo(4)      o+l(1+9)
                e.length = e.offset + e.length - left_offset
                e.offset = 0
                #         |0 1 2 3 4 5 6
                #         ^           ^
                #        o(0)  o+l=0+o+l-lo(6=0+6=0+1+9-4)
        else:
            # e.offset + e.length <= left_offset
            #   0 1 2 3|4 5
            #  ^       ^
            # o(0)   o+l(4)
            #        lo(4)
            del entities[i]
            continue

        if e.offset + e.length <= len_final:
            # |0 1 2 3 4 5 6 7 8 9
            #   ^                 ^
            #  o(1)       o+l(1+9)/lf(10)
            continue
        if e.offset >= len_final:
            # |0 1 2 3 4
            #           ^
            #       o(5)/lf(5)
            del entities[i]
        else:
            # e.offset < len_final and e.offset + e.length > len_final
            # |0 1 2 3 4 5 (6) (7) (8) (9)
            #   ^         ^           ^
            #  o(1)     lf(6)      o+l(1+8)
            e.length = len_final - e.offset
            # |0 1 2 3 4 5
            #   ^         ^
            #  o(1) o+l=o+lf-o=lf(6=1+5=1+6-1)

    return text


def add_surrogate(text):
    return "".join(
        # SMP -> Surrogate Pairs (Telegram offsets are calculated with these).
        # See https://en.wikipedia.org/wiki/Plane_(Unicode)#Overview for more.
        "".join(chr(y) for y in struct.unpack("<HH", x.encode("utf-16le"))) if (0x10000 <= ord(x) <= 0x10FFFF) else x
        for x in text
    )


def del_surrogate(text):
    return text.encode("utf-16", "surrogatepass").decode("utf-16")


def _process_headings_surrogate(text: str) -> tuple[str, list[MessageEntity]]:
    """
    Process ATX-style markdown headings in the surrogate text and return the
    modified text along with bold entities spanning each heading's content.
    Operates on surrogate text to keep offsets in UTF-16 code units.
    """
    out_parts: list[str] = []
    entities: list[MessageEntity] = []
    offset = 0

    for line in text.splitlines(keepends=True):
        # Preserve newline endings exactly
        if line.endswith("\r\n"):
            line_body = line[:-2]
            newline = "\r\n"
        elif line.endswith("\n") or line.endswith("\r"):
            newline = line[-1]
            line_body = line[:-1]
        else:
            newline = ""
            line_body = line

        m = re.match(r"^(#{1,6})[ \t]+(.+)$", line_body)
        if m:
            content = m.group(2)
            # Remove optional closing hashes (CommonMark): trailing spaces, hashes, optional spaces
            content = re.sub(r"[ \t]+#{1,}\s*$", "", content)
            content = content.strip()
            if content:
                entities.append(MessageEntity(type="bold", offset=offset, length=len(content)))
            out_parts.append(content + newline)
            offset += len(content) + len(newline)
        else:
            out_parts.append(line)
            offset += len(line)

    return "".join(out_parts), entities


def extract_markdown_entities(
    text: str, delimiters=None, url_re=None, extract_headings: bool = False
) -> tuple[str, list[MessageEntity]]:
    """
    Parses the given markdown message and returns its stripped representation
    plus a list of the MessageEntity's that were found.
    :param text: the message with markdown-like syntax to be parsed.
    :param delimiters: the delimiters to be used, {delimiter: type}.
    :param url_re: the URL bytes regex to be used. Must have two groups.
    :return: a tuple consisting of (clean message, [message entities]).
    """
    if not text:
        return text, []

    if url_re is None:
        url_re = DEFAULT_URL_RE
    elif isinstance(url_re, str):
        url_re = re.compile(url_re)

    if not delimiters:
        if delimiters is not None:
            return text, []
        delimiters = DEFAULT_DELIMITERS

    # Build a regex to efficiently test all delimiters at once.
    # Note that the largest delimiter should go first, we don't
    # want ``` to be interpreted as a single back-tick in a code block.
    delim_re = re.compile(
        "|".join("({})".format(re.escape(k)) for k in sorted(delimiters, key=len, reverse=True))  # type: ignore[literal-required]
    )

    # Cannot use a for loop because we need to skip some indices
    i = 0
    result: list[MessageEntity] = []

    # Work on byte level with the utf-16le encoding to get the offsets right.
    # The offset will just be half the index we're at.
    text = add_surrogate(text)

    # Optionally process markdown headings and pre-populate entities.
    if extract_headings:
        text, heading_entities = _process_headings_surrogate(text)
        result.extend(heading_entities)

    while i < len(text):
        m = delim_re.match(text, pos=i)

        # Did we find some delimiter here at `i`?
        if m:
            delim = next(filter(None, m.groups()))

            # +1 to avoid matching right after (e.g. "****")
            end = text.find(delim, i + len(delim) + 1)

            # Did we find the earliest closing tag?
            if end != -1:
                # Remove the delimiter from the string
                text = "".join(
                    (
                        text[:i],
                        text[i + len(delim) : end],
                        text[end + len(delim) :],
                    )
                )

                # Check other affected entities
                for ent in result:
                    # If the end is after our start, it is affected
                    if ent.offset + ent.length > i:
                        # If the old start is also before ours, it is fully enclosed
                        if ent.offset <= i:
                            ent.length -= len(delim) * 2
                        else:
                            ent.length -= len(delim)

                # Append the found entity
                ent_type = delimiters[delim]
                result.append(MessageEntity(type=ent_type, offset=i, length=end - i - len(delim)))

                continue

        elif url_re:
            m = url_re.match(text, pos=i)
            if m:
                # Replace the whole match with only the inline URL text.
                text = "".join((text[: m.start()], m.group(1), text[m.end() :]))

                # Number of characters removed when replacing the whole match with only its text.
                delim_size = (m.end() - m.start()) - len(m.group(1))
                for ent in result:
                    # If the end is after our start, it is affected
                    if ent.offset + ent.length > m.start():
                        ent.length -= delim_size

                result.append(
                    MessageEntity(
                        type="text_link",
                        offset=m.start(),
                        length=len(m.group(1)),
                        url=del_surrogate(m.group(2)),
                    )
                )
                i += len(m.group(1))
                continue

        i += 1

    text = strip_text(text, result)
    return del_surrogate(text), result
