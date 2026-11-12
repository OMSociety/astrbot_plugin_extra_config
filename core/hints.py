"""机器人页字段的说明文案。

核心在把配置元数据交给 Dashboard 之前，会把 description 与 hint 改写成
i18n 键（`platform_group.platform.<字段>.<属性>`）。机器人页只认核心自带的
翻译表，查不到翻译就显示键名，所以插件直接写 hint 会被显示成裸键。

这里在核心完成转换之后，把本插件三个字段的文案还原成字面文本；前端对查不到
翻译的文本按原文显示。核心的转换函数是唯一的可用挂点，包装时保持失败可退。
"""

from __future__ import annotations

from typing import Any

FIELD_TEXT: dict[str, dict[str, str]] = {
    "附加提示词": {
        "description": "附加提示词",
        "hint": "只对该机器人生效，追加到系统提示词末尾；留空则不追加。",
    },
    "Markdown 格式清理": {
        "description": "Markdown 格式清理",
        "hint": "发送前把 Markdown 语法清理为纯文本，适合不支持 Markdown 的平台。",
    },
    "单轮字数上限": {
        "description": "单轮字数上限",
        "hint": "单条回复超过该字数时先打回重写；填 0 表示不限制，也不打回。",
    },
}

_PATCH_FLAG = "_extra_config_field_text"


def _logger():
    try:
        from astrbot.api import logger

        return logger
    except Exception:
        return None


def apply_field_text(metadata: dict[str, Any]) -> None:
    """把平台条目上本插件字段的说明还原为字面文本。"""
    try:
        items = metadata["platform_group"]["metadata"]["platform"]["items"]
    except (KeyError, TypeError):
        return
    if not isinstance(items, dict):
        return
    for field, text in FIELD_TEXT.items():
        item = items.get(field)
        if isinstance(item, dict):
            item.update(text)


def install() -> bool:
    """包装核心的元数据转换，使说明文案出现在机器人页。"""
    try:
        from astrbot.core.config.i18n_utils import ConfigMetadataI18n
    except Exception:
        return False

    logger = _logger()
    try:
        from .registry import FIELD_CLEAN, FIELD_LIMIT, FIELD_PROMPT

        if set(FIELD_TEXT) != {FIELD_PROMPT, FIELD_CLEAN, FIELD_LIMIT}:
            if logger:
                logger.warning("字段说明文案与字段名不一致，部分说明将不显示")
    except Exception:
        pass

    if getattr(ConfigMetadataI18n, _PATCH_FLAG, False):
        return True

    original = getattr(ConfigMetadataI18n, "convert_to_i18n_keys", None)
    if not callable(original):
        return False

    def convert(metadata: dict[str, Any]) -> dict[str, Any]:
        result = original(metadata)
        apply_field_text(result)
        return result

    ConfigMetadataI18n.convert_to_i18n_keys = staticmethod(convert)
    setattr(ConfigMetadataI18n, _PATCH_FLAG, True)
    return True
