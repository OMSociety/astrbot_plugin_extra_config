"""按机器人（平台实例）配置附加提示词、Markdown 清理与超长回复打回。"""

from __future__ import annotations

import asyncio

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, MessageChain, filter
from astrbot.api.message_components import Plain
from astrbot.api.provider import ProviderRequest
from astrbot.api.star import Context, Star

from .core.parts import MARKER, split_parts, truncate
from .core.plaintext import clean_markdown
from .core.registry import (
    FIELD_CLEAN,
    FIELD_LIMIT,
    FIELD_PROMPT,
    backup_config,
    ensure_bot_defaults,
    inject_metadata,
)

_EXTRA_PARTS = "_extra_config_split_parts"
_SPLIT_INTERVAL = 0.8
_BOUNCE_TIMES = 2

_PART_RULE = (
    "如果回复内容较长，请用 {marker} 把回复分成多条消息，每条不超过 {limit} 字；"
    "不需要分条时不要出现这个标记。"
)
_REWRITE_SYSTEM = (
    "把用户给出的回复重新组织：不新增事实，不改变结论与语气；"
    "每条消息不超过 {limit} 字，多条之间用 {marker} 分隔。只输出正文。"
)


class ExtraConfigPlugin(Star):
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
                logger.info("已为机器人配置补齐附加提示词、格式清理与字数上限字段")
        except Exception:
            logger.warning("补齐机器人配置字段失败", exc_info=True)

    async def terminate(self):
        logger.info("平台实例附加配置插件已停用")

    def _option(self, key: str, default):
        try:
            return self.config.get(key, default)
        except Exception:
            return default

    def _features(self) -> dict[str, bool]:
        return {
            "enable_prompt": bool(self._option("enable_prompt", True)),
            "enable_clean": bool(self._option("enable_clean", True)),
            "enable_bounce": bool(self._option("enable_bounce", False)),
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
                if getattr(meta, "id", None) == platform_id and isinstance(conf, dict):
                    return conf
        except Exception:
            pass
        return {}

    def _limit(self, conf: dict) -> int:
        try:
            return max(0, int(conf.get(FIELD_LIMIT) or 0))
        except (TypeError, ValueError):
            return 0

    @filter.on_llm_request()
    async def on_llm_request(self, event: AstrMessageEvent, req: ProviderRequest):
        """把该机器人的附加提示词与分条约定追加到系统提示词末尾。"""
        current = req.system_prompt or ""
        additions = []

        if self._option("enable_prompt", True):
            extra = str(self._bot_conf(event).get(FIELD_PROMPT) or "").strip()
            if extra:
                additions.append(extra)

        if self._option("enable_bounce", False):
            limit = self._limit(self._bot_conf(event))
            if limit > 0:
                additions.append(_PART_RULE.format(marker=MARKER, limit=limit))

        for block in additions:
            if block in current:
                continue
            current = f"{current}\n\n{block}".strip()
        req.system_prompt = current
        if additions and self._option("debug", False):
            logger.info("为机器人 %s 追加系统提示词", event.get_platform_id())

    @filter.on_decorating_result()
    async def on_decorating_result(self, event: AstrMessageEvent):
        """把该机器人回复中的 Markdown 清理为纯文本，并按约定拆条或打回重写。"""
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

        if not self._option("enable_bounce", False):
            return
        limit = self._limit(conf)
        if limit <= 0 or any(not isinstance(comp, Plain) for comp in chain):
            return

        text = "\n".join((comp.text or "") for comp in chain)
        if len(text) <= limit:
            if MARKER in text:
                for comp in chain:
                    comp.text = (comp.text or "").replace(MARKER, "").strip()
            return

        if MARKER not in text:
            text = await self._rewrite(event, text, limit)

        parts = [truncate(part, limit) for part in split_parts(text)]
        if not parts:
            return
        result.chain = [Plain(parts[0])]
        if len(parts) > 1:
            setattr(event, _EXTRA_PARTS, parts[1:])
        if self._option("debug", False):
            logger.info("回复 %s 字，分为 %s 条", len(text), len(parts))

    async def _rewrite(self, event: AstrMessageEvent, text: str, limit: int) -> str:
        """把超长回复打回给模型，要求按标记重写成多条。"""
        try:
            provider = self.context.get_using_provider(umo=event.unified_msg_origin)
        except Exception:
            logger.warning("获取当前模型失败，超长回复保持原样", exc_info=True)
            return text
        if provider is None:
            return text

        system_prompt = _REWRITE_SYSTEM.format(marker=MARKER, limit=limit)
        best = text
        for attempt in range(_BOUNCE_TIMES):
            try:
                resp = await provider.text_chat(
                    prompt=text,
                    system_prompt=system_prompt,
                    contexts=[],
                )
            except Exception:
                logger.warning("打回重写失败，保留原回复", exc_info=True)
                return best
            candidate = (getattr(resp, "completion_text", "") or "").strip()
            if not candidate:
                continue
            if len(candidate) < len(best):
                best = candidate
            if MARKER in candidate or len(candidate) <= limit:
                return candidate
            text = candidate
            if self._option("debug", False):
                logger.info("第 %s 次打回后仍超上限，继续改写", attempt + 1)
        return best

    @filter.after_message_sent()
    async def after_message_sent(self, event: AstrMessageEvent):
        """把超长回复拆出的后续消息依次发出。"""
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
                logger.warning("发送拆分后的消息失败", exc_info=True)
                break
