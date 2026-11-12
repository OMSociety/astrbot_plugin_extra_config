import importlib.util
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "parts.py"
_SPEC = importlib.util.spec_from_file_location("parts_under_test", _MODULE_PATH)
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

MARKER = _MODULE.MARKER
split_parts = _MODULE.split_parts
truncate = _MODULE.truncate


def test_short_text_kept_whole():
    assert truncate("短句。", 20) == "短句。"


def test_zero_limit_keeps_text():
    text = "任意长度" * 20
    assert truncate(text, 0) == text


def test_truncate_at_sentence_end():
    text = "第一句话。第二句话。第三句话。"
    result = truncate(text, 10)
    assert len(result) <= 10
    assert result.endswith("…")
    assert result.startswith("第一句话。")


def test_truncate_hard_cut_without_punctuation():
    result = truncate("啊" * 50, 10)
    assert len(result) <= 10
    assert result.endswith("…")


def test_split_parts_by_marker():
    text = f"第一段内容。{MARKER}第二段内容。{MARKER}第三段内容。"
    assert split_parts(text) == ["第一段内容。", "第二段内容。", "第三段内容。"]


def test_split_parts_drops_blank_segments():
    text = f"{MARKER}{MARKER}内容{MARKER}"
    assert split_parts(text) == ["内容"]


def test_split_parts_without_marker_returns_single():
    assert split_parts("普通回复。") == ["普通回复。"]
