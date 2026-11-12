import importlib.util
from pathlib import Path

_CORE = Path(__file__).resolve().parents[1] / "core"
_spec = importlib.util.spec_from_file_location("hints_under_test", _CORE / "hints.py")
hints = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hints)

apply_field_text = hints.apply_field_text
FIELD_TEXT = hints.FIELD_TEXT


def _metadata(items):
    return {"platform_group": {"metadata": {"platform": {"items": items}}}}


def test_restores_literal_text_for_plugin_fields():
    metadata = _metadata(
        {
            "单轮字数上限": {
                "type": "int",
                "description": "platform_group.platform.单轮字数上限.description",
                "hint": "platform_group.platform.单轮字数上限.hint",
            }
        }
    )

    apply_field_text(metadata)

    item = metadata["platform_group"]["metadata"]["platform"]["items"]["单轮字数上限"]
    assert item["description"] == "单轮字数上限"
    assert item["hint"] == FIELD_TEXT["单轮字数上限"]["hint"]
    assert "0" in item["hint"]


def test_leaves_other_fields_untouched():
    other = {
        "type": "bool",
        "description": "platform_group.platform.use_markdown.description",
        "hint": "platform_group.platform.use_markdown.hint",
    }
    metadata = _metadata({"use_markdown": dict(other), "附加提示词": {"type": "text"}})

    apply_field_text(metadata)

    items = metadata["platform_group"]["metadata"]["platform"]["items"]
    assert items["use_markdown"] == other
    assert items["附加提示词"]["hint"] == FIELD_TEXT["附加提示词"]["hint"]


def test_ignores_metadata_without_platform_items():
    apply_field_text({})
    apply_field_text({"platform_group": {}})
    apply_field_text(_metadata({"unknown": {"type": "text"}}))
