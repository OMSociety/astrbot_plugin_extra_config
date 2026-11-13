"""机器人（平台实例）配置项：字段元数据注入与默认值补齐。"""

from __future__ import annotations

import os
import shutil
from datetime import datetime
from typing import Any

from astrbot.api import logger

FIELD_PROMPT = "附加提示词"
FIELD_CLEAN = "Markdown 格式清理"
FIELD_LIMIT = "单轮字数上限"

FIELD_DEFAULTS: dict[str, Any] = {
    FIELD_PROMPT: "",
    FIELD_CLEAN: False,
    FIELD_LIMIT: 0,
}

FIELD_METADATA: dict[str, dict[str, Any]] = {
    FIELD_PROMPT: {"type": "text", "default": ""},
    FIELD_CLEAN: {"type": "bool", "default": False},
    FIELD_LIMIT: {"type": "int", "default": 0},
}

FIELD_FEATURES: dict[str, str] = {
    FIELD_PROMPT: "enable_prompt",
    FIELD_CLEAN: "enable_clean",
    FIELD_LIMIT: "enable_bounce",
}


def _platform_meta() -> dict | None:
    """返回机器人页字段所在的元数据节点，结构不符时返回 None。"""
    try:
        from astrbot.core.config.default import CONFIG_METADATA_2
    except Exception:
        logger.warning("无法导入配置元数据，机器人页字段将不会出现")
        return None
    node = CONFIG_METADATA_2.get("platform_group")
    if not isinstance(node, dict):
        return None
    node = node.get("metadata")
    if not isinstance(node, dict):
        return None
    node = node.get("platform")
    return node if isinstance(node, dict) else None


def inject_metadata(enabled: dict[str, bool] | None = None) -> bool:
    """把自定义字段写进机器人页的表单元数据，返回是否有改动。

    未启用的功能对应字段带 invisible 标记，机器人页不渲染该行。
    """
    platform_meta = _platform_meta()
    if platform_meta is None:
        return False

    changed = False
    items = platform_meta.get("items")
    if isinstance(items, dict):
        for key, meta in FIELD_METADATA.items():
            item = dict(meta)
            feature = FIELD_FEATURES[key]
            if enabled is not None and not enabled.get(feature, True):
                item["invisible"] = True
            if items.get(key) != item:
                items[key] = item
                changed = True

    templates = platform_meta.get("config_template")
    if isinstance(templates, dict):
        for template in templates.values():
            if not isinstance(template, dict):
                continue
            for key, default in FIELD_DEFAULTS.items():
                if key not in template:
                    template[key] = default
                    changed = True
    return changed


def ensure_bot_defaults(config: dict) -> bool:
    """给已有机器人的配置条目补上缺失字段，返回是否有改动。"""
    changed = False
    platforms = config.get("platform")
    if not isinstance(platforms, list):
        return False
    for item in platforms:
        if not isinstance(item, dict):
            continue
        for key, default in FIELD_DEFAULTS.items():
            if key not in item:
                item[key] = default
                changed = True
    return changed


_BACKUP_KEEP = 5


def _prune_backups(path: str) -> None:
    """裁掉同名的旧备份，只保留最近 _BACKUP_KEEP 份。"""
    folder = os.path.dirname(path) or "."
    prefix = f"{os.path.basename(path)}.bak-"
    try:
        entries = sorted(
            name for name in os.listdir(folder) if name.startswith(prefix)
        )
    except OSError as exc:
        logger.warning("读取备份目录失败：%s", exc)
        return
    for name in entries[:-_BACKUP_KEEP]:
        try:
            os.remove(os.path.join(folder, name))
        except OSError as exc:
            logger.warning("清理旧备份失败：%s", exc)


def backup_config(config: dict) -> None:
    """写入机器人配置前复制一份原文件，并裁掉超出保留份数的旧备份。"""
    path = getattr(config, "config_path", "")
    if not path:
        return
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    try:
        shutil.copy2(path, f"{path}.bak-{stamp}")
    except OSError as exc:
        logger.warning("备份机器人配置失败：%s", exc)
        return
    _prune_backups(path)
