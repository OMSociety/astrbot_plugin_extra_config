"""回复分条与截断工具。"""

from __future__ import annotations

MARKER = "[分条]"

_SENTENCE_END = "。！？!?；;…"


def split_parts(text: str, marker: str = MARKER) -> list[str]:
    """按分条标记切分回复，丢弃空段并保留段内换行。"""
    parts = []
    for piece in text.split(marker):
        piece = piece.strip()
        if piece:
            parts.append(piece)
    return parts


def truncate(text: str, limit: int) -> str:
    """把超长文本截到上限以内，优先停在句末，截断处补省略号。"""
    if limit <= 0 or len(text) <= limit:
        return text
    if limit == 1:
        return "…"
    head = text[: limit - 1]
    cut = -1
    for ch in _SENTENCE_END:
        cut = max(cut, head.rfind(ch))
    newline = head.rfind("\n")
    if newline > cut and newline > limit // 2:
        cut = newline
    if cut > 0:
        return head[: cut + 1].rstrip() + "…"
    space = head.rfind(" ")
    if space > limit // 2:
        return head[:space].rstrip() + "…"
    return head.rstrip() + "…"
