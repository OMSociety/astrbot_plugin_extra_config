<div align="center">

<h1><img src="https://raw.githubusercontent.com/OMSociety/astrbot_plugin_extra_config/main/logo.png" width="192" alt="平台实例附加配置图标" /><br />平台实例附加配置</h1>
<p><strong>给每个机器人各配一份表达规范</strong> —— 附加提示词 · Markdown 兜底清理 · 超长回复打回分条</p>

[![Version](https://img.shields.io/github/v/tag/OMSociety/astrbot_plugin_extra_config?label=version)](CHANGELOG.md)
[![AstrBot](https://img.shields.io/badge/AstrBot-4.x-6f42c1.svg)](https://github.com/AstrBotDevs/AstrBot)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/OMSociety/astrbot_plugin_extra_config)](https://github.com/OMSociety/astrbot_plugin_extra_config/stargazers)
[![Issues](https://img.shields.io/github/issues/OMSociety/astrbot_plugin_extra_config)](https://github.com/OMSociety/astrbot_plugin_extra_config/issues)

[核心特性](#核心特性) • [功能概览](#功能概览) • [用法示例](#用法示例) • [快速开始](#快速开始) • [配置项说明](#配置项说明) • [常见问题](#常见问题) • [更新日志](CHANGELOG.md)

</div>

## 核心特性

| 特性 | 说明 |
|---|---|
| **按机器人配置** | 三项参数分别作用于每个平台实例，多个机器人互不影响 |
| **字段落在机器人页** | 直接显示在 Dashboard 的「机器人」编辑页，保存即写入 `cmd_config.json` |
| **按平台切换表达** | 同一个 bot 可以给 QQ 官方机器人写 Markdown 规范、给微信写纯文本规范 |
| **不改人格** | 附加提示词每轮追加到系统提示词末尾，不动人格与用户消息，不破坏前缀缓存 |
| **Markdown 兜底清理** | 不支持 Markdown 的平台自动转为纯文本，保留代码块原文与链接地址 |
| **超长回复打回** | 超过字数上限先请模型重写为多条，仍超限则按句末截断 |
| **零第三方依赖** | 只用 Python 标准库与 AstrBot 运行时，安装即用 |

## 功能概览

### 附加提示词

「附加提示词」在该机器人每次请求模型前，追加到系统提示词的末尾；同一机器人的这段文本恒定，不影响上游前缀缓存。字段默认空，表示不追加任何内容。

它适合写平台特有的表达规范：QQ 官方机器人可以使用标题、粗体、列表与代码块，微信侧则要求不使用任何 Markdown 语法、用短句与文字序号分点。

### Markdown 格式清理

打开「Markdown 格式清理」后，该机器人的回复在发送前会把文本组件中的 Markdown 语法清理成纯文本：去掉标题井号、粗体与斜体标记、行内代码反引号、图片与链接语法、引用符号与分隔线，表格改为按行排列的文本，无序列表改为「·」。围栏代码块保留代码原文、只去掉围栏，链接改写为「文字 地址」。

该开关只处理文本组件，图片等非文本消息不受影响；同时会把该条结果标记为纯文本，避免支持 Markdown 的适配器再按 Markdown 发送。

### 超长回复打回

开启后，该机器人的系统提示词末尾会多一条约定：回复较长时用 `[分条]` 把内容分成多条消息，每条不超过「单轮字数上限」。

发送前按以下顺序处理：

1. 回复里已有 `[分条]`，按标记切成多条，首条正常发送，其余依次补发，间隔 0.8 秒。
2. 没有标记且整条超过上限，打回当前模型，要求按同样约定重写；最多两次。
3. 每条仍然超过上限时，按句末截断并补省略号。

打回只改写排版与长度，不新增事实、不改变结论。整条回复只包含文本组件时才处理；含图片、语音等组件时保持原样发送。

## 用法示例

两个平台各填一份「附加提示词」，内容不同，互不干扰：

```text
# QQ 官方机器人（支持 Markdown）
可以使用标题、粗体、列表与代码块；需要分点时优先用 Markdown 列表，
表格用于对比多项内容。

# 微信（不支持 Markdown）
不要使用任何 Markdown 语法；小标题用【】包裹，分点用「1. 2. 3.」，
每段控制在两三行以内，链接直接贴出完整地址。
```

微信侧同时打开「Markdown 格式清理」作为兜底：即使模型偶尔写出 `**粗体**`、`# 标题`，发送前也会被清理为纯文本。

## 快速开始

### 第一步：安装

AstrBot WebUI → 插件市场 → 搜索「平台实例附加配置」，或把插件目录放入实例的 `data/plugins` 后重载插件。

### 第二步：在机器人页配置

打开「机器人」页，编辑要配置的机器人，在「接入设置」中填写「附加提示词」，按需打开「Markdown 格式清理」、填写「单轮字数上限」，保存。

> **提示**：首次加载插件时，配置里缺少这些字段的机器人会自动补上默认值，写入前在 `cmd_config.json` 同目录留一份带时间戳的备份，旧备份只保留最近五份。三个字段在机器人页各带一行说明；「单轮字数上限」填 0 表示不限制，不打回。插件页里关掉某个功能的启用开关后，机器人页对应的字段会隐藏。

## 配置项说明

插件自身配置（「插件」页内该插件的设置）：

| 配置项 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `enable_prompt` | bool | `true` | 启用附加提示词；关闭后机器人页隐藏该字段，也不注入 |
| `enable_clean` | bool | `true` | 启用 Markdown 清理；关闭后机器人页隐藏该开关 |
| `enable_bounce` | bool | `false` | 启用超长回复打回；关闭后机器人页隐藏字数上限字段 |
| `debug` | bool | `false` | 在日志中输出注入、清理与打回的明细，便于排查 |

机器人级配置（由插件自动补入，无需手工创建）：

| 配置项 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `附加提示词` | text | 空 | 追加到该机器人系统提示词末尾的文本 |
| `Markdown 格式清理` | bool | `false` | 是否把该机器人的回复清理为纯文本 |
| `单轮字数上限` | int | `0` | 单条消息的字数上限，0 表示不限制，不打回 |

插件配置落在 `data/config/astrbot_plugin_extra_config_config.json`，结构如下：

```json
{
  "enable_prompt": true,
  "enable_clean": true,
  "enable_bounce": false,
  "debug": false
}
```

## 常见问题

### Q1：需要安装额外依赖吗？

不需要。插件只使用 Python 标准库与 AstrBot 运行时。

### Q2：机器人页里找不到这三个字段？

先在「插件」页重载本插件，再刷新机器人页。字段由插件在加载时注入；插件未启用或加载失败时不会出现。

### Q3：修改了字段却没有生效？

确认机器人页保存成功并刷新一次；插件页的启用开关关闭时，机器人页对应字段会隐藏且不生效。改了字段说明文案后，需要重载插件才会更新。

### Q4：会影响图片、语音等消息吗？

不会。「Markdown 格式清理」只处理文本组件；含图片、语音等组件的回复保持原样发送，「超长回复打回」也不会处理这类消息。

### Q5：打回会不会让下一轮对话继续模仿 `[分条]`？

打回是一次独立请求，不写入会话历史，下一轮看到的仍是模型自己的原始输出。若模型在短回复里误写了 `[分条]`，插件会剥掉标记、按单条发送。

### Q6：多个机器人会互相影响吗？

不会。三项参数都按机器人（平台实例）分别读取，各自生效；插件自身的启用开关只决定功能是否可用。

## 更新日志

> **[查看更新日志 →](CHANGELOG.md)**

## 支持与致谢

如果这个插件对你有帮助，欢迎点亮 Star，有问题和建议请提交 [Issue](https://github.com/OMSociety/astrbot_plugin_extra_config/issues) 或 [Pull Request](https://github.com/OMSociety/astrbot_plugin_extra_config/pulls)。

- [AstrBot](https://github.com/AstrBotDevs/AstrBot) 开源聊天机器人框架

## 许可证与作者

本项目采用 **MIT** 开源协议，见 [LICENSE](LICENSE)。

[@OMSociety](https://github.com/OMSociety)
