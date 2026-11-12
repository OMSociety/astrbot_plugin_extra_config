"""把超过长度上限的回复切成多段。"""

from __future__ import annotations

import re

_SENTENCE_RE = re.compile(r"[^。！？!?；;…\n]+[。！？!?；;…]*")


def _sentences(line: str) -> list[str]:
    return [s for s in _SENTENCE_RE.findall(line) if s.strip()]


def _hard_split(text: str, limit: int) -> list[str]:
    """单句本身超长时按空白或硬切点切分。"""
    parts: list[str] = []
    rest = text
    while len(rest) > limit:
        cut = rest.rfind(" ", limit // 2, limit)
        if cut <= 0:
            cut = limit
        parts.append(rest[:cut].rstrip())
        rest = rest[cut:].lstrip()
    if rest:
        parts.append(rest)
    return [p for p in parts if p]


def split_text(text: str, limit: int) -> list[str]:
    """按句子边界把文本切成不超过 limit 个字符的若干段。"""
    if limit <= 0 or len(text) <= limit:
        return [text]

    pieces: list[tuple[str, bool]] = []
    lines = text.split("\n")
    for line_index, line in enumerate(lines):
        for sent_index, sentence in enumerate(_sentences(line)):
            at_line_start = line_index > 0 and sent_index == 0
            if len(sentence) > limit:
                for part_index, part in enumerate(_hard_split(sentence, limit)):
                    pieces.append((part, at_line_start and part_index == 0))
            else:
                pieces.append((sentence, at_line_start))

    chunks: list[str] = []
    current = ""
    for piece, newline_before in pieces:
        joiner = "\n" if current and newline_before else ""
        if current and len(current) + len(joiner) + len(piece) > limit:
            chunks.append(current)
            current = piece
        else:
            current = current + joiner + piece
    if current:
        chunks.append(current)
    return [chunk for chunk in chunks if chunk.strip()]
