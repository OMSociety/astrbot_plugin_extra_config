import importlib.util
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "split.py"
_SPEC = importlib.util.spec_from_file_location("split_under_test", _MODULE_PATH)
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

split_text = _MODULE.split_text


def test_short_text_kept_whole():
    assert split_text("短句。", 100) == ["短句。"]


def test_zero_limit_keeps_text():
    text = "任意长度" * 100
    assert split_text(text, 0) == [text]


def test_split_at_sentence_boundaries():
    text = "第一句。第二句。第三句。"
    parts = split_text(text, 8)
    assert parts == ["第一句。第二句。", "第三句。"]


def test_each_part_within_limit():
    text = "这是一段比较长的中文回复内容，包含多个句子用于测试。" * 5
    parts = split_text(text, 20)
    assert len(parts) > 1
    assert all(len(part) <= 20 for part in parts)
    assert "".join(parts).replace("\n", "") == text.replace("\n", "")


def test_long_sentence_hard_split():
    text = "啊" * 25
    parts = split_text(text, 10)
    assert all(len(part) <= 10 for part in parts)
    assert "".join(parts) == text


def test_line_breaks_preserved_between_paragraphs():
    assert split_text("甲。\n乙。", 10) == ["甲。\n乙。"]
    parts = split_text("第一行内容比较长需要分开处理。\n第二行内容也不短。", 12)
    assert all(len(part) <= 12 for part in parts)
    assert len(parts) >= 3


def test_blank_segments_dropped():
    parts = split_text("句子。\n\n\n句子。", 5)
    assert all(part.strip() for part in parts)
