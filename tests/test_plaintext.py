import importlib.util
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "plaintext.py"
_SPEC = importlib.util.spec_from_file_location("plaintext_under_test", _MODULE_PATH)
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

clean_markdown = _MODULE.clean_markdown


def test_plain_text_unchanged():
    text = "今天天气不错。\n记得带伞。"
    assert clean_markdown(text) == text


def test_blank_text_returned_as_is():
    assert clean_markdown("") == ""
    assert clean_markdown("   \n ") == "   \n "


def test_heading():
    assert clean_markdown("## 小标题\n正文") == "小标题\n正文"
    assert clean_markdown("### 【重点】") == "【重点】"


def test_emphasis():
    assert clean_markdown("**重点** 和 *斜体* 以及 ~~删除~~") == "重点 和 斜体 以及 删除"
    assert clean_markdown("这是_强调_的文字") == "这是强调的文字"
    assert clean_markdown("***加粗斜体***") == "加粗斜体"


def test_snake_case_preserved():
    text = "变量 a_b 与 snake_case_name 保持不变"
    assert clean_markdown(text) == text


def test_inline_code():
    assert clean_markdown("运行 `pip install foo` 即可") == "运行 pip install foo 即可"


def test_fenced_code_keeps_content():
    text = "```python\ndef f(*args, **kwargs):\n    return a_b\n```"
    assert clean_markdown(text) == "def f(*args, **kwargs):\n    return a_b"


def test_bare_url_protected():
    text = "见 https://example.com/a_b_c?x=1_2 末尾"
    assert clean_markdown(text) == text


def test_link_and_image():
    assert (
        clean_markdown("[文档](https://example.com/doc)")
        == "文档 https://example.com/doc"
    )
    assert (
        clean_markdown("![示意图](https://example.com/a.png)")
        == "https://example.com/a.png"
    )


def test_table():
    text = "| 项目 | 值 |\n|---|---|\n| 温度 | 25 |"
    result = clean_markdown(text)
    assert "|" not in result
    assert "项目" in result and "温度" in result and "25" in result


def test_quote_and_hr():
    assert clean_markdown("> 引用内容") == "引用内容"
    assert clean_markdown("上面\n\n---\n\n下面") == "上面\n\n下面"


def test_bullet_list():
    assert clean_markdown("- 第一\n- 第二") == "· 第一\n· 第二"
    assert clean_markdown("* 第一") == "· 第一"
    assert clean_markdown("1. 一\n2. 二") == "1. 一\n2. 二"


def test_mixed_report():
    text = (
        "## 今日安排\n\n"
        "- **上午**：写周报\n"
        "- 下午：见 [客户](https://example.com/meet)\n\n"
        "| 时间 | 事项 |\n|---|---|\n| 10:00 | 站会 |"
    )
    result = clean_markdown(text)
    for marker in ("#", "**", "|", "](", "---"):
        assert marker not in result
    assert "今日安排" in result and "写周报" in result
    assert "https://example.com/meet" in result
