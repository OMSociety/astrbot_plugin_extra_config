<div align="center">

<img src="https://raw.githubusercontent.com/OMSociety/astrbot_plugin_extra_config/main/logo.png" width="128" alt="平台实例附加配置图标">

# 平台实例附加配置

为每个机器人单独配置附加提示词与字数上限；对不支持 Markdown 的平台，把回复兜底清理为纯文本，超长回复拆成多段发送。

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/OMSociety/astrbot_plugin_extra_config/releases)
[![AstrBot](https://img.shields.io/badge/AstrBot-4.x-6f42c1.svg)](https://github.com/AstrBotDevs/AstrBot)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/OMSociety/astrbot_plugin_extra_config?style=flat)](https://github.com/OMSociety/astrbot_plugin_extra_config/stargazers)
[![Issues](https://img.shields.io/github/issues/OMSociety/astrbot_plugin_extra_config?style=flat)](https://github.com/OMSociety/astrbot_plugin_extra_config/issues)

</div>

[核心特性](#核心特性) • [功能概览](#功能概览) • [快速开始](#快速开始) • [配置项说明](#配置项说明) • [开发](#开发)

## 核心特性

| 特性 | 说明 |
|---|---|
| **按机器人配置** | 三项参数分别作用于每个平台实例，多个机器人互不影响 |
| **字段落在机器人页** | 配置直接显示在 Dashboard 的「机器人」编辑页，保存即写入 `cmd_config.json` |
| **不改人格** | 提示词每轮追加到系统提示词末尾，不动人格与用户消息 |
| **兜底清理** | 按开关把回复中的 Markdown 语法清理为纯文本，仅处理文本组件 |
| **超长回复分条** | 超过字数上限的回复按句拆分，首段正常发送，其余分段补发 |

## 功能概览

### 附加提示词

「附加提示词」在该机器人每次请求模型前，追加到系统提示词的末尾；同一机器人的这段文本恒定，不影响上游前缀缓存。字段默认空，表示不追加任何内容。

「附加提示词」适合写平台特有的表达规范，例如 QQ 官方机器人可以使用标题、粗体、列表、代码块，而微信侧要求不使用任何 Markdown 语法、用短句与文字序号分点。

### Markdown 格式清理

打开「Markdown 格式清理」后，该机器人的回复在发送前会把文本组件中的 Markdown 语法清理成纯文本：去掉标题井号、粗体与斜体标记、行内代码反引号、图片与链接语法、引用符号与分隔线，表格改为按行排列的文本，无序列表改为「·」。围栏代码块保留代码原文、只去掉围栏，链接改写为「文字 地址」。

该开关只处理文本组件，图片等非文本消息不受影响；同时会把该条结果标记为纯文本，避免支持 Markdown 的适配器再按 Markdown 发送。

### 超长回复分条

「单轮字数上限」大于 0 且回复超过该字数时，插件按段落与句号、问号、感叹号、分号、省略号切分，再把句子拼成不超过上限的若干段。首段留在原回复链里正常发送，引用、前缀与平台适配器行为不受影响；其余分段在该条消息发送完成后依次补发，段间隔 0.8 秒。上限为 0 表示不分条。

整条回复只包含文本组件时才分条；含图片、语音等组件时保持原样发送。

## 快速开始

1. 在 AstrBot 面板的「插件」页安装本项目，或把插件目录放入 `data/plugins` 后重载插件。
2. 打开「机器人」页，编辑要配置的机器人，在「接入设置」中填写「附加提示词」，按需打开「Markdown 格式清理」、填写「单轮字数上限」，保存。
3. 首次加载插件时，配置里缺少这些字段的机器人会自动补上默认值，写入前在 `cmd_config.json` 同目录留一份带时间戳的备份。
4. 修改机器人页后如未生效，刷新页面再确认字段已保存。

> **提示**：三个字段的标签直接取自字段名，机器人与插件都不提供额外说明文案；含义以上文为准。插件页里关掉某个功能的启用开关后，机器人页对应的字段会隐藏。

## 配置项说明

插件自身配置（「插件」页内该插件的设置）：

| 配置项 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `enable_prompt` | bool | `true` | 启用附加提示词；关闭后机器人页隐藏该字段，也不注入 |
| `enable_clean` | bool | `true` | 启用 Markdown 清理；关闭后机器人页隐藏该开关 |
| `enable_split` | bool | `false` | 启用超长回复分条；关闭后机器人页隐藏字数上限字段 |
| `debug` | bool | `false` | 在日志中输出注入、清理与拆分的明细，便于排查 |

机器人级配置（都由插件自动补入，无需手工创建）：

| 配置项 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `附加提示词` | text | 空 | 追加到该机器人系统提示词末尾的文本 |
| `Markdown 格式清理` | bool | `false` | 是否把该机器人的回复清理为纯文本 |
| `单轮字数上限` | int | `0` | 单条回复的字数上限，0 表示不分条 |

## 开发

- 依赖：仅 Python 标准库与 AstrBot 运行时，无第三方包。
- 测试：在仓库根目录执行 `python -m pytest tests -q`，单元测试覆盖清理器与分条器的各类边界。
- 目录：`main.py` 注册生命周期与三个钩子；`core/registry.py` 负责字段注入与默认值补齐；`core/plaintext.py` 是 Markdown 清理器；`core/split.py` 负责按字数分条。

## 许可证

MIT，见 [LICENSE](LICENSE)。作者：OMSociety。
