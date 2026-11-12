# AGENTS.md

AstrBot 插件 `astrbot_plugin_extra_config`（显示名「平台实例附加配置」）。按「机器人」（AstrBot 的 platform 实例）维度提供三项配置：附加提示词、Markdown 格式清理、单轮字数上限（超长回复打回）。

本文件只记录本仓库特有的、工具与通用开发技能管不住的事实。改代码的通用纪律见 dev-playbook，AstrBot 插件 API 见 astrbot-plugin-creator。

## 命令

测试（仓库自带的两个测试文件，共 20 例）：

```bash
python -m pytest tests -q
```

离线结构自检（用 AstrBot 宿主的 core 校验 API 用法）：

```bash
python <astrbot-plugin-creator 技能目录>/scripts/check_plugin.py . --host-root <AstrBot 实例>/core --json
```

宿主内冒烟（宿主 venv 通常没有 pytest，这一步只验证模块能被插件加载器导入）：

```bash
<AstrBot 实例>/venv/Scripts/python.exe -c "import data.plugins.astrbot_plugin_extra_config.main as m; print(m.ExtraConfigPlugin)"
```

在宿主 `core` 目录下执行上述命令；插件以 `data.plugins.<目录名>.<模块>` 形式加载。

## 目录职责

| 路径 | 职责 |
| --- | --- |
| `main.py` | 插件类 `ExtraConfigPlugin`；`initialize` 注入字段与补默认值；三个钩子 `on_llm_request`、`on_decorating_result`、`after_message_sent` |
| `core/registry.py` | 机器人页字段注入、机器人条目补默认值、配置备份 |
| `core/plaintext.py` | Markdown 转纯文本 |
| `core/parts.py` | `[分条]` 标记拆分与单段截断 |
| `tests/` | 纯函数测试，不依赖宿主 |

## 不可违反的约定

1. **中文字段名就是持久化键。** `附加提示词`、`Markdown 格式清理`、`单轮字数上限` 会写进用户的 `cmd_config.json` 的 `platform` 条目。改名等于让存量数据失联：必须同步改 `core/registry.py` 的 `FIELD_*`、`FIELD_DEFAULTS`、`FIELD_FEATURES` 与测试，并考虑旧键迁移。
2. **注入的 metadata 只能有 `type` 与 `default`。** 机器人页不读插件 i18n，写入 `description` 或 `hint` 会让标签显示成裸 i18n 键；不写时标签就是键名本身。
3. **字段可见性每次 `initialize()` 重算。** 插件配置的开关决定把哪些字段标成 `invisible`；宿主保存插件配置后会热重载插件，靠这次重跑让开关生效，不要缓存到模块级。
4. **追加到 `req.system_prompt` 的文本必须每个机器人恒定且幂等。** 相同的块不能重复追加；随会话变化的内容不得进系统提示词，会破坏模型侧前缀缓存。
5. **结果修饰顺序固定：先清理，后拆分。** 链中出现非 `Plain` 组件时放弃拆分；清理改动过文本必须调用 `result.use_markdown_(False)`，否则 QQ 官方适配器仍按 markdown 载荷发送。
6. **`[分条]` 是与模型的契约。** 约定写在系统提示词里，发送前按标记拆条。整条回复未超过上限时，必须剥掉模型误写的标记按单条发出，不拆条也不打回。
7. **打回必须走独立调用。** 用 `provider.text_chat(prompt=..., system_prompt=..., contexts=[])`，不经过会话历史；打回产物不得进入下一轮上下文。历史在结果修饰之前落盘，改动钩子时别打乱这个前提。
8. **后续分段在 `after_message_sent` 补发。** 宿主的分段回复开关是全局设置、不能按机器人打开，插件不得去改它；首段留在结果链里走正常发送，其余段落逐条 `event.send()`。
9. **保持包导入。** 插件以包形式加载，模块内用相对导入 `from .core...`。测试不得用顶层 `core` 包导入（离线自检会把它误判成第三方依赖并报缺少 requirements.txt），测试一律用 `importlib` 按文件路径加载被测算函数。
10. **元数据与文档同步。** `metadata.yaml` 是插件识别依据，四个必填字段不能少；插件页展示的行为描述来自钩子 docstring，改行为要改 docstring；改配置项要同步 README 的两张配置表。

## 不要做

- 不要为插件引入第三方运行时依赖；确有必要时先建 `requirements.txt` 并说明安装代价。
- 不要手工改生产实例的 `cmd_config.json`：字段补齐由 `initialize()` 完成，写前有备份。
- 不要直接给插件目录改名。宿主按目录名识别插件，插件配置文件与已加载状态都跟着变；改名要同时处理旧配置文件与实例内 Junction 的迁移。
- 不要提交 `__pycache__`、`.pytest_cache` 与 `data/`。

## 验收

一次改动算完成，需同时满足：

1. `python -m pytest tests -q` 全绿。
2. `check_plugin.py` 无 error。
3. 宿主 venv 能导入插件模块，日志无加载异常。
4. 行为类改动在宿主里重载插件后，机器人页字段与钩子实际输出符合预期。
