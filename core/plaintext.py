"""把 Markdown 文本转成纯文本，供不渲染 Markdown 的聊天平台阅读。"""

from __future__ import annotations

import re

_TOKEN_RE = re.compile("\x00(\\d+)\x00")

_IMAGE_RE = re.compile(
    r"!\[([^\]]*)\]\(\s*<?([^)\s>]+)>?(?:\s+[\"'][^\"']*[\"'])?\s*\)"
)
_LINK_RE = re.compile(
    r"\[([^\]\n]+)\]\(\s*<?([^)\s>]+)>?(?:\s+[\"'][^\"']*[\"'])?\s*\)"
)
_AUTOLINK_RE = re.compile(r"<(https?://[^>\s]+)>")
_URL_RE = re.compile(r"https?://[^\s<>()\[\]\x00]+")
_INLINE_CODE_RE = re.compile(r"(`+)([^\n]+?)\1")

_HEADING_RE = re.compile(r"(?m)^[ \t]{0,3}#{1,6}[ \t]+(.+?)[ \t]*#*[ \t]*$")
_EMPTY_HEADING_RE = re.compile(r"(?m)^[ \t]{0,3}#{1,6}[ \t]*$")
_HR_RE = re.compile(r"(?m)^[ \t]{0,3}([-*_])(?:[ \t]*\1){2,}[ \t]*$")
_QUOTE_RE = re.compile(r"(?m)^[ \t]{0,3}>[ \t]?")
_BULLET_RE = re.compile(r"(?m)^([ \t]*)[-*+][ \t]+")


_ASCII_WORD = "A-Za-z0-9_"


def _strip_emphasis(text: str) -> str:
    """去掉强调标记；用 ASCII 词边界保护 snake_case 与 **粗体**。"""
    text = re.sub(r"\*\*\*(?=\S)(.+?)(?<=\S)\*\*\*", r"\1", text, flags=re.S)
    text = re.sub(
        rf"(?<![{_ASCII_WORD}])___(?=\S)(.+?)(?<=\S)___(?![{_ASCII_WORD}])",
        r"\1",
        text,
        flags=re.S,
    )
    text = re.sub(r"\*\*(?=\S)(.+?)(?<=\S)\*\*", r"\1", text, flags=re.S)
    text = re.sub(
        rf"(?<![{_ASCII_WORD}])__(?=\S)(.+?)(?<=\S)__(?![{_ASCII_WORD}])",
        r"\1",
        text,
        flags=re.S,
    )
    text = re.sub(r"~~(?=\S)(.+?)(?<=\S)~~", r"\1", text, flags=re.S)
    text = re.sub(r"(?<!\*)\*(?=[^\s*])([^*\n]+?)(?<=[^\s*])\*(?!\*)", r"\1", text)
    text = re.sub(
        rf"(?<![{_ASCII_WORD}])_(?=[^\s_])([^_\n]+?)(?<=[^\s_])_(?![{_ASCII_WORD}])",
        r"\1",
        text,
    )
    return text


def _strip_tables(text: str) -> str:
    lines: list[str] = []
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped or "\x00" in stripped or "|" not in stripped:
            lines.append(line)
            continue
        if set(stripped) <= set("|-: ") and "-" in stripped:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        cells = [cell for cell in cells if cell]
        if len(cells) >= 2:
            lines.append("  ".join(cells))
        else:
            lines.append(line)
    return "\n".join(lines)


def _extract_fences(text: str, stash) -> str:
    lines: list[str] = []
    fence: str | None = None
    buffer: list[str] = []
    for line in text.split("\n"):
        stripped = line.strip()
        if fence is None and (stripped.startswith("```") or stripped.startswith("~~~")):
            fence = stripped[:3]
            buffer = []
            continue
        if fence is not None:
            if stripped.startswith(fence):
                lines.append(stash("\n".join(buffer)))
                fence = None
                buffer = []
            else:
                buffer.append(line)
            continue
        lines.append(line)
    if fence is not None:
        lines.append(stash("\n".join(buffer)))
    return "\n".join(lines)


def clean_markdown(text: str) -> str:
    """去掉 Markdown 语法，保留文字、代码与链接地址。"""
    if not text or not text.strip():
        return text

    text = text.replace("\r\n", "\n").replace("\r", "\n")

    tokens: list[str] = []

    def stash(value: str) -> str:
        tokens.append(value)
        return f"\x00{len(tokens) - 1}\x00"

    text = _extract_fences(text, stash)
    text = _INLINE_CODE_RE.sub(lambda m: stash(m.group(2).strip()), text)
    text = _IMAGE_RE.sub(lambda m: stash(m.group(2)), text)
    text = _LINK_RE.sub(lambda m: f"{m.group(1)} {stash(m.group(2))}", text)
    text = _AUTOLINK_RE.sub(lambda m: stash(m.group(1)), text)
    text = _URL_RE.sub(lambda m: stash(m.group(0)), text)

    text = _strip_emphasis(text)
    text = _HEADING_RE.sub(r"\1", text)
    text = _EMPTY_HEADING_RE.sub("", text)
    text = _HR_RE.sub("", text)
    text = _QUOTE_RE.sub("", text)
    text = _strip_tables(text)
    text = _BULLET_RE.sub(r"\1· ", text)

    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    text = _TOKEN_RE.sub(lambda m: tokens[int(m.group(1))], text)
    return text.strip()
