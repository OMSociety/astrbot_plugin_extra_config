"""按机器人（平台实例）配置附加提示词，并把 Markdown 回复兜底清理为纯文本。"""

from __future__ import annotations

import asyncio

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, MessageChain, filter
from astrbot.api.message_components import Plain
from astrbot.api.provider import ProviderRequest
from astrbot.api.star import Context, Star

from .core.plaintext import clean_markdown
from .core.registry import (
    FIELD_CLEAN,
    FIELD_LIMIT,
    FIELD_PROMPT,
    backup_config,
    ensure_bot_defaults,
    inject_metadata,
)
from .core.split import split_text

_EXTRA_PARTS = "_platform_prompt_extra_parts"
_SPLIT_INTERVAL = 0.8


class PlatformPromptPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig | None = None):
        super().__init__(context)
        self.config = config if isinstance(config, dict) else {}

    async def initialize(self):
        try:
            inject_metadata(self._features())
        except Exception:
            logger.warning("注入机器人页字段失败", exc_info=True)

        try:
            conf = self.context.get_config()
            if isinstance(conf, dict) and ensure_bot_defaults(conf):
                backup_config(conf)
                await conf.save_config_async()
                logger.info("已为机器人配置补齐附加提示词与格式清理字段")
        except Exception:
            logger.warning("补齐机器人配置字段失败", exc_info=True)

    async def terminate(self):
        logger.info("机器人附加提示词插件已停用")

    def _option(self, key: str, default):
        try:
            return self.config.get(key, default)
        except Exception:
            return default

    def _features(self) -> dict[str, bool]:
        return {
            "enable_prompt": bool(self._option("enable_prompt", True)),
            "enable_clean": bool(self._option("enable_clean", True)),
            "enable_split": bool(self._option("enable_split", False)),
        }

    def _bot_conf(self, event: AstrMessageEvent) -> dict:
        """按平台实例 id 取该机器人的配置条目。"""
        try:
            platform_id = event.get_platform_id()
        except Exception:
            return {}
        if not platform_id:
            return {}

        try:
            for item in self.context.get_config().get("platform", []) or []:
                if isinstance(item, dict) and item.get("id") == platform_id:
                    return item
        except Exception:
            pass

        try:
            for inst in self.context.platform_manager.platform_insts:
                meta = getattr(inst, "metadata", None)
                conf = getattr(inst, "config", None)
                if (
                    getattr(meta, "id", None) == platform_id
                    and isinstance(conf, dict)
                ):
                    return conf
        except Exception:
            pass
        return {}

    @filter.on_llm_request()
    async def on_llm_request(self, event: AstrMessageEvent, req: ProviderRequest):
        """把该机器人的附加提示词追加到系统提示词末尾。"""
        if not self._option("enable_prompt", True):
            return
        extra = str(self._bot_conf(event).get(FIELD_PROMPT) or "").strip()
        if not extra:
            return
        current = req.system_prompt or ""
        if extra in current:
            return
        req.system_prompt = f"{current}\n\n{extra}".strip()
        if self._option("debug", False):
            logger.info("为机器人 %s 追加附加提示词", event.get_platform_id())

    @filter.on_decorating_result()
    async def on_decorating_result(self, event: AstrMessageEvent):
        """把该机器人回复中的 Markdown 清理为纯文本，并按上限拆分长回复。"""
        conf = self._bot_conf(event)
        result = event.get_result()
        chain = getattr(result, "chain", None) if result is not None else None
        if not chain:
            return

        if self._option("enable_clean", True) and conf.get(FIELD_CLEAN):
            changed = False
            for comp in chain:
                if not isinstance(comp, Plain):
                    continue
                raw = comp.text or ""
                cleaned = clean_markdown(raw)
                if cleaned != raw:
                    comp.text = cleaned
                    changed = True
                    if self._option("debug", False):
                        logger.info("Markdown 清理：%r -> %r", raw, cleaned)
            if changed:
                try:
                    result.use_markdown_(False)
                except Exception:
                    logger.warning("重置 Markdown 发送标志失败", exc_info=True)

        if self._option("enable_split", False):
            try:
                limit = int(conf.get(FIELD_LIMIT) or 0)
            except (TypeError, ValueError):
                limit = 0
            if limit > 0:
                self._split_chain(event, result, limit)

    def _split_chain(self, event: AstrMessageEvent, result, limit: int) -> None:
        chain = result.chain
        if any(not isinstance(comp, Plain) for comp in chain):
            return
        text = "\n".join((comp.text or "") for comp in chain)
        if len(text) <= limit:
            return
        parts = split_text(text, limit)
        if len(parts) < 2:
            return
        result.chain = [Plain(parts[0])]
        setattr(event, _EXTRA_PARTS, parts[1:])
        if self._option("debug", False):
            logger.info("回复 %s 字，拆为 %s 段", len(text), len(parts))

    @filter.after_message_sent()
    async def after_message_sent(self, event: AstrMessageEvent):
        """把超长回复拆出的后续分段依次发出。"""
        parts = getattr(event, _EXTRA_PARTS, None)
        if not parts:
            return
        setattr(event, _EXTRA_PARTS, None)
        for index, part in enumerate(parts):
            try:
                if index:
                    await asyncio.sleep(_SPLIT_INTERVAL)
                await event.send(MessageChain([Plain(part)]))
            except Exception:
                logger.warning("发送拆分后的分段失败", exc_info=True)
                break
