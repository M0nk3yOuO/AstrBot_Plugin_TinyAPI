# AstrBot_Plugin_TinyAPI

[![AstrBot Plugin](https://img.shields.io/badge/AstrBot-插件-green)](https://github.com/AstrBotDevs/AstrBot)
[![Version](https://img.shields.io/badge/version-1.8.0-blue)](https://github.com/M0nk3yOuO/AstrBot_Plugin_TinyAPI)
[![License](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)

AstrBot 插件，聚合调用 TinyAPI 的 300+ 免费 API 接口，支持关键词快捷调用、智能参数提示，图片/音频/视频自动识别并直接发送。

## 📖 目录

- [功能特性](#功能特性)
- [安装方法](#安装方法)
- [配置说明](#配置说明)
- [使用方法](#使用方法)
- [API 示例](#api-示例)
- [LLM 回复改写功能](#llm-回复改写功能)
- [查看接口参数说明](#查看接口参数说明)
- [常见问题](#常见问题)
- [技术说明](#技术说明)
- [更新日志](#更新日志)
- [贡献指南](#贡献指南)
- [授权协议](#授权协议)
- [作者留言](#作者留言)
- [联系方式](#联系方式)

## ✨ 功能特性

- ✅ **290+ 免费 API 接口**：覆盖出行、AI、游戏、工具、生活、娱乐等多个领域
- ✅ **关键词智能匹配**：直接发送关键词即可调用对应 API
- ✅ **api查询**：发送「api查询」查看所有关键词→API名称映射列表
- ✅ **零参数直出**：无需参数的 API 直接返回结果，需要参数的自动提示参数格式
- ✅ **智能参数提示**：参数不匹配时自动提示正确格式
- ✅ **支持多种参数类型**：文本、图片URL、音频URL、视频URL、图片文件
- ✅ **LLM 回复改写**：开启后，API 返回的文本会由 LLM 进行人性化改写，让回复更像真人（默认使用 AstrBot 配置的对话大模型）
- ✅ **站点池配置**：支持配置多个 API 站点
- ✅ **API 池配置**：统一管理 API 和关键词映射
- ✅ **灵活的调用方式**：支持关键词直出、参数提示、媒体自动识别

## 📦 安装方法

### 方法一：从 Release 安装（推荐）

1. 前往 [Release 页面](https://github.com/M0nk3yOuO/AstrBot_Plugin_TinyAPI/releases) 下载最新版的 `AstrBot_Plugin_TinyAPI-v1.7.9.zip`
2. 解压后得到 `AstrBot_Plugin_TinyAPI` 文件夹
3. 将文件夹复制到 AstrBot 的 `data/plugins/` 目录下
4. 重启 AstrBot 或在管理面板启用插件

### 方法二：从源码安装

1. 克隆本仓库到本地：
   ```bash
   git clone https://github.com/M0nk3yOuO/AstrBot_Plugin_TinyAPI.git
   ```

2. 将 `AstrBot_Plugin_TinyAPI` 文件夹复制到 AstrBot 的 `data/plugins/` 目录下

3. 重启 AstrBot

### 方法三：通过 AstrBot 管理面板安装

1. 打开 AstrBot 管理面板
2. 进入「插件市场」
3. 搜索「TinyAPI」
4. 点击「一键安装」

## ⚙️ 配置说明

### 插件配置（通过 AstrBot 管理面板）

在 AstrBot 管理面板 → 插件设置 → TinyAPI 聚合插件 中配置：

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|--------|
| `api_key` | string | TinyAPI Key（**必填**，格式：`sk_xxx`） | 空 |
| `base_url` | string | API 基础 URL 地址 | `https://api.tinyaii.top` |
| `timeout` | int | 请求超时时间（秒） | `30` |
| `enable_keyword_match` | bool | 是否启用关键词匹配 | `true` |
| `enable_llm_rewrite` | bool | 是否启用 LLM 回复改写（开启后，API 返回的文本会由 LLM 进行人性化改写，让回复更像真人） | `true` |

#### 如何获取 API Key？

1. 访问 [TinyAPI 官网](https://api.tinyaii.top)
2. 注册账号并登录
3. 在个人中心获取免费 API Key（格式：`sk_xxx`）

### 站点池配置（`config/sites.json`）

配置多个 API 站点（可选）：

```json
{
  "sites": [
    {
      "name": "TinyAPI主站",
      "url": "https://api.tinyaii.top",
      "description": "TinyAPI 290+ 免费 API 接口平台",
      "enabled": true
    }
  ]
}
```

### API 池配置（`config/apis.json`）

插件已内置 292 个 API 接口配置，涵盖：

- 🚄 出行：12306、航班查询
- 🎨 AI：绘画、问答、创作
- 🎮 游戏：AK、APEX 等游戏数据
- 📱 工具：二维码生成、短链接、OCR
- 🌤️ 生活：天气、黄历、星座
- 🎬 娱乐：动漫识别、视频解析、音乐搜索

如需添加自定义 API，编辑 `config/apis.json`：

```json
{
  "apis": [
    {
      "name": "我的自定义API",
      "path": "/v1/myapi",
      "description": "自定义 API 描述",
      "keywords": ["关键词1", "关键词2", "快捷指令"],
      "required_params": ["param1"],
      "param_types": {
        "param1": "text"
      },
      "params": {
        "param1": "参数说明"
      }
    }
  ]
}
```

修改后重启 AstrBot 重新加载配置。

#### 参数类型说明

| 类型 | 说明 | 示例 |
|------|------|------|
| `text` | 文本参数 | `火车 北京` |
| `image_url` | 图片 URL | `动漫搜番 https://example.com/img.jpg` |
| `image_file` | 图片文件（直接发送图片给 Bot） | 先发送图片，然后输入关键词 |
| `audio_url` | 音频 URL | `音乐识别 https://example.com/audio.mp3` |
| `video_url` | 视频 URL | `视频解析 https://example.com/video.mp4` |
| `url` | 一般 URL | `网盘解析 https://example.com/file` |

## 📖 使用方法

### 1. 查看所有可用 API（推荐首次使用）

直接对 Bot 发送以下任意消息即可触发（已注册为指令行为，支持别名）：

```
api查询
查看api
查看接口
api列表
关键词列表
可用api
查询api
```

Bot 会返回所有关键词到 API 名称的映射列表（每行一个：`关键词 → API名称`），格式紧凑，方便快速查找。

### 2. 关键词快捷调用（推荐）

直接发送**关键词**，Bot 自动判断并调用对应 API：

#### 无参数 API → 直接返回结果

```
黄历           → 今日黄历（直接返回结果）
缩写 HTTP      → HTTP 缩写含义（直接返回结果）
```

#### 有参数 API → 自动提示参数格式

如果只发关键词但缺少必填参数，Bot 会自动回复参数格式说明：

```
用户：火车
Bot：
⚠️ 12306火车查询 需要提供参数才能使用！

必填参数：
  📝 msg：车站名

💡 正确输入格式：
  火车 车站名
```

提供参数后正常调用：

```
火车 北京          → 查询北京车次信息
绘画 一只猫        → AI 生成猫咪图片
动漫搜番 https://xxx.jpg  → 识别动漫截图
```

### 3. LLM 回复改写功能

插件支持将 API 返回的文本结果发送给 LLM 进行人性化改写，让回复更像真人。

#### 开启方法

在 AstrBot 管理面板 → 插件设置 → TinyAPI 聚合插件 中，将 `enable_llm_rewrite` 设置为 `true`，然后重启 AstrBot。

#### 功能说明

- **开启后**：API 返回的文本结果会发送给 LLM，由 LLM 进行人性化改写后再回复给用户（去掉 JSON 结构化，让回复更像真人回复）
- **关闭后**：直接返回 API 调用的原始结果
- **使用的模型**：默认使用 AstrBot 配置的对话大模型（无需额外配置）
- **改写失败**：若 LLM 调用失败，会自动降级为返回原始结果

#### 注意事项

- LLM 改写会增加回复时间（需要等待 LLM 处理）
- 改写后的内容可能因 LLM 的理解而产生细微变化
- 图片、音频、视频等媒体内容不会经过 LLM 改写，直接发送

### 3. 查看接口参数说明（？查询）

发送「关键词？」或「关键词?」，Bot 会返回该接口的描述、必填参数和可选参数，无需调用 API。

```
火车？
```

Bot 会返回「12306火车查询」的参数格式说明（含描述、必填参数、可选参数、正确输入格式）。

**支持所有已注册的关键词。**

---

### 4. 参数格式提示

当参数不正确时，Bot 会自动提示正确格式：

**示例 1：缺少必填参数（发送关键词但没带参数）**

```
用户：火车
Bot：
⚠️ 12306火车查询 需要提供参数才能使用！

必填参数：
  📝 msg：车站名

💡 正确输入格式：
  火车 车站名
```

**示例 2：参数格式不正确（图片URL格式错误）**

```
用户：动漫搜番 这不是URL
Bot：
⚠️ 参数 url 需要提供图片URL地址，请以 http:// 或 https:// 开头

💡 正确格式：
  动漫搜番 https://example.com/image.jpg
```

## 🎯 API 示例

### 1. 12306 火车票查询

```
火车 北京
```

### 2. 黄历查询

```
黄历
```

### 3. AI 绘画

```
绘画 美丽的风景
```

### 4. 动漫识别

```
动漫搜番 https://example.com/anime.jpg
```

### 5. 天气查询

```
天气 北京
```

## 🔧 常见问题

### 1. 安装插件后无法使用？

**可能原因**：
- 未配置 `api_key`（必填）
- API Key 格式不正确（应为 `sk_xxx` 格式）
- 插件未启用

**解决方法**：
1. 在 AstrBot 管理面板配置 `api_key`
2. 确认插件已启用
3. 重启 AstrBot

### 2. 关键词匹配不工作？

**检查方法**：
1. 确认插件配置中 `enable_keyword_match` 为 `true`
2. 检查 `config/apis.json` 中是否正确配置了 `keywords` 字段
3. 查看 Bot 返回的关键词列表，确认关键词已加载
4. 要严格按照bot提示的输入标准才会调用api

### 3. 如何添加自定义 API？

编辑 `config/apis.json`，添加新 API 配置：

```json
{
  "name": "我的API",
  "path": "/v1/myapi",
  "description": "我的自定义API",
  "keywords": ["关键词1", "关键词2"],
  "required_params": ["param1"],
  "param_types": {
    "param1": "text"
  },
  "params": {
    "param1": "参数说明"
  }
}
```

修改后重启 AstrBot 重新加载配置。

### 4. 关键词误触发怎么办？

"api查询"已注册为独立指令行为（支持别名），直接对 Bot 说即可触发，不参与关键词匹配。

关键词快捷调用使用两层匹配策略，按优先级递减：

1. **精确首词匹配**：消息首词精确匹配关键词 → 调用对应 API
2. **子串兜底匹配**：仅短消息（≤4 字）中触发，且只匹配无参数 API

如果仍然误触发，可以在插件配置中将 `enable_keyword_match` 设为 `false`，停用关键词匹配功能。

### 5. 如何更新 API 池？

API 池基于 [TinyAPI 官方文档](https://api.tinyaii.top/docs) 自动生成，如需更新：

1. 下载最新的 OpenAPI 文档（`json-format.json`）
2. 运行 `python parse_openapi.py` 重新生成 `config/apis.json`
3. 重启 AstrBot 重新加载配置

## 🔬 技术说明

### 插件架构

```
AstrBot_Plugin_TinyAPI/
├── main.py                # 插件主文件
├── metadata.yaml          # 插件元数据
├── _conf_schema.json      # 配置 Schema
├── README.md             # 说明文档
├── config/               # 配置文件目录
│   ├── apis.json        # API 池配置
│   └── sites.json       # 站点池配置
└── parse_openapi.py      # OpenAPI 文档解析脚本
```

### 核心类和方法

- **TinyAPIPlugin**：插件主类，继承自 `astrbot.api.star.Star`
- **_call_api()**：异步调用 TinyAPI 接口
- **_build_keyword_map()**：构建关键词到 API 路径的映射
- **keyword_match_handler()**：关键词匹配处理器
- **_build_keyword_messages()**：构建关键词→API名称映射消息列表

### API 调用流程

1. 用户发送消息
2. 插件进行关键词匹配（三层策略）
3. 提取关键词和参数
4. 调用 `_call_api()` 发送 HTTP 请求
5. 解析响应并格式化结果
6. 返回给用户信息

### 请求格式

- **基础 URL**：`https://api.tinyaii.top`
- **认证方式**：Query 参数 `?apikey=sk_xxx`
- **请求方法**：GET/POST（根据 API 定义）
- **响应格式**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    // API 返回的数据
  }
}
```

### 依赖项

- `aiohttp`：异步 HTTP 请求
- `json`：JSON 解析
- `os`：文件路径处理

## 📝 更新日志

### v1.8.0 (2026-06-21)

- 🖼️📝 **媒体+文字同时输出**：API 返回图片/视频/音频时，自动将媒体和文字说明合并到同一条消息发送，不再只发媒体丢失文字
- 🚫 **限制单条消息图片数量**：单条消息最多发送 5 张图片，避免 QQ NT 接口因图片过多报错（retcode=1200）
- 📝 **LLM 改写优化**：改写 prompt 增强，不再提及 JSON 字段名（如 json_data、raw_data 等），空值/空列表自动跳过不提及，输出增加换行方便手机阅读
- 🔒 **日志脱敏**：API 调用日志中的 `apikey` 值显示为 `***`，不再明文打印
- ❓ **新增「？查询」功能**：关键词后加 `？` 或 `?`（如 `火车？`），Bot 返回该接口的描述和参数说明，不调用 API
- 🛡️ 新增 `.gitignore`，防止误提交敏感文件
- 🐛 修复 `_send_result` 逻辑：媒体和文字正确同时发送（之前文字会丢失）

### v1.7.11 (2026-06-21)
- 🐛 修复 `_send_result` 逻辑：媒体和文字现在正确同时发送到同一条消息中（之前文字会丢失）
- 🔧 优化消息构建方式：统一使用 `result_obj.chain` 追加文字和媒体组件

### v1.7.10 (2026-06-21)
- 🔒 日志脱敏：API 调用日志中的 `apikey` 值显示为 `***`，不再明文打印，避免 key 泄露
- 📋 LLM 回复改写增强：改写时传入完整原始数据，并要求 LLM 保留每一个字段，不得遗漏信息
- 🛡️ 新增 `.gitignore`，防止误提交敏感文件

### v1.7.9 (2026-06-21)
- 图片接收功能改为始终开启，移除 `enable_image_receive` 配置开关
- 修正 `metadata.yaml` 命令列表，去掉不存在的 `/tinyapi` 系列命令
- `enable_llm_rewrite` 默认值修正为 `false`

### v1.7.8 (2026-06-21)

- 🧹 移除图片「分开发送」相关功能及所有 cache 缓存代码
- 🗑️ 移除已失效的「古诗词」API（/v1/poem 接口已永久 404）
- 🧹 清理无用 import（shutil、time）
- 📝 更新插件描述及 _conf_schema.json 配置项

### v1.7.7 (2026-06-21)

- 🔧 **移除图片分开发送功能**：只保留「关键词+图片一起发」，避免群里发表情包被误触发
- 🗑️ 移除已失效的「古诗词」API（`/v1/poem` 返回 404）

### v1.7.6 (2026-06-21)

- 🔧 **修复图片/音频/视频URL识别问题**：重写 `_format_result`，加入递归搜索逻辑，自动查找响应数据结构中的媒体URL
- 🔍 通过键名关键字判断媒体类型（`img`/`pic`/`photo` → 图片，`audio`/`music` → 音频，`video`/`movie` → 视频）
- 🖼️ 通用链接键名（`url`/`link`/`src` 等）无法判断扩展名时，**默认按图片处理**
- 🛠️ 修复 `content` 键检查顺序，避免纯文本API被误判为媒体

### v1.7.5 (2026-06-21)

- 🔧 修复 `keyword_match_handler` 函数丢失问题（多次编辑 main.py 时函数体被覆盖/删除）
- 📝 添加插件启动日志（`[TinyAPI] 插件加载完成`），方便确认插件加载状态
- 🔧 修复事件传播未终止问题：匹配到关键词时正确调用 `event.stop_event()`

### v1.7.4 (2026-06-21)

- ✨ **简化 `api查询` 输出格式**：改为纯垂直列表，每行一个「关键词 → API名称」
- 🧹 移除横向分隔线 `━━━━━━━━━━`，头部只显示总数
- 📋 每行缩进两格，列表更清晰

### v1.7.3 (2026-06-21)

- ✨ **优化参数提示格式**：输入关键词后若无法直接调用API，现在会完整展示：
  - 📌 API 名称 + 功能描述（description）
  - 📋 必填参数（含参数说明和快捷方式提示）
  - 📎 可选参数
  - 💡 正确输入格式（含具体示例）
- 🔧 修复参数判断逻辑：当API需要`image_url`参数但用户未提供图片时，正确显示使用提示而非直接调API导致报错
- ✨ 新增 `_guess_example_value` 方法：根据参数名自动生成合理的示例值，让格式提示更直观

### v1.7.2 (2026-06-21)

- 🔧 **修复 `image_url` 类型参数的图片处理（针对QQ平台）**：当有本地图片文件时，自动通过 TinyAPI 图床接口上传，获取稳定公网 URL 再调用 API，不再依赖平台图片 URL 的可访问性
- 🌐 新增 `_upload_image_to_host` 方法：将本地图片上传到图床，返回公网 URL
- 🔧 优化图片输入判断逻辑：有图片文件或图片 URL 均视为"有图片输入"，避免因仅发图片无文本而被误判为缺少必填参数

### v1.7.1 (2026-06-21)

- 🔧 修复 `image_url` 类型参数的图片处理：优先尝试获取平台图片URL（QQ/Telegram等平台发图时自带URL）
- 📝 更新 README 文档，补充参数类型说明（`image_url` vs `image_file`）和参数类型说明表
- 🔧 优化图片参数处理逻辑，同时支持本地图片（`image_file`）和图片URL（`image_url`）

### v1.7.0 (2026-06-21)

- ✨ **支持关键词和图片一起发送**：用户可以在一条消息中同时发送关键词和图片，Bot 会自动识别并调用对应的 API（无需分两次发送）
- 📝 更新 README 文档，添加新的使用方式说明
- 🔧 优化图片处理逻辑，优先使用当前消息中的图片

### v1.6.0 (2026-06-21)

- 🔄 更新 metadata.yaml 版本号
- 📝 更新文档和版本徽章

### v1.5.0 (2026-06-21)

- 🔑 主触发词改为「api查询」，旧关键词（查看api、api列表等）保留为别名
- 📋 「api查询」返回紧凑的关键词→API名称映射列表（每行一个，格式：`关键词 → API名称`）
- ⚡ 无参数API：直接发送关键词即返回结果，无需额外确认
- 💡 有参数API：只发关键词时自动提示必填/可选参数格式，不再调用失败
- 📝 更新 README 文档

### v1.4.0 (2026-06-20)

- 🖼️ **图片直接发送**：API返回图片URL时，Bot直接发送图片而非文本链接
- 🎬 **视频直接发送**：API返回视频URL时，Bot直接发送视频
- 🔊 **音频直接发送**：API返回音频URL时，Bot直接发送语音消息
- 🧠 **智能媒体类型检测**：通过URL扩展名 + 响应字段名双重判断，精确识别图片/音频/视频
- 📋 支持data为字符串URL、列表等多种返回格式的媒体识别

### v1.3.0 (2026-06-20)

- 🏗️ 将 `/tinyapi` 重构为指令组（command_group），每个子命令（help/list/sites/call/reload）成为独立的行为
- ✨ 将"查看api"注册为正式指令行为，支持"查看接口""api列表""关键词列表"等多个别名
- 🔧 修复关键词匹配处理器无条件停止事件传播的问题，仅在真正匹配到关键词时才停止
- 📝 更新 metadata.yaml 指令列表和 README 文档

### v1.2.0 (2026-06-20)

- 🔧 修复非 200 响应码时不读取响应体的问题
- 🔧 修复「查天气」等消息误触发的问题
- ✨ 新增「查询API」等触发词
- ✨ 优化参数校验和错误提示
- 📝 更新 README 文档

### v1.1.0 (2026-06-20)

- ✨ 新增「查看API」关键词列表展示功能
- ✨ 新增关键词+参数快捷调用（如：火车 北京）
- 🔧 改进关键词匹配逻辑（精确首词匹配优先，减少误触发）
- 📝 返回结果中显示 API 名称

### v1.0.0 (2026-06-20)

- 🎉 初始版本
- ✅ 支持 290+ TinyAPI 接口调用
- ✅ 支持关键词自动匹配
- ✅ 支持站点池和 API 池配置

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发规范

1. 遵循 [AstrBot 插件开发规范](https://docs.astrbot.app/dev/star/plugin.html)
2. 使用 `ruff` 格式化代码
3. 添加必要的注释和文档
4. 测试通过后再提交

### 提交 PR

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

### 报告 Bug

提交 Issue 时请包含：

- 插件版本
- AstrBot 版本
- 复现步骤
- 期望行为和实际行为
- 相关日志

## 📄 授权协议

本项目采用 MIT  License 授权协议，详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [AstrBot](https://github.com/AstrBotDevs/AstrBot)：优秀的 AI 助手框架
- [TinyAPI](https://api.tinyaii.top)：提供 290+ 免费 API 接口

## 💬 作者留言

感谢使用本插件！如果你觉得好用，欢迎给个 Star ⭐

如果你在使用过程中遇到问题，或者有好的建议，欢迎通过以下方式联系我：

- GitHub Issue：[https://github.com/M0nk3yOuO/AstrBot_Plugin_TinyAPI/issues](https://github.com/M0nk3yOuO/AstrBot_Plugin_TinyAPI/issues)
- 也欢迎在 AstrBot 社区中交流使用心得

希望这个插件能对你的Bot有所帮助！🎉

PS:这个插件是我第一次纯使用Agent跑的所有代码(也是第一次开发)，对于Astrbot和插件的写法规范并不是很熟练，我唯一只手动修改了关键词（keywords）和api接口的映射，并没有做其他的检查，可能存在很多bug和不足的地方，欢迎反馈，或者有更好的建议哪怕是聊天都可以联系我。

## 📧 联系方式

- 作者：M0nk3yOuO
- QQ：451982575
- 项目主页：[https://github.com/M0nk3yOuO/AstrBot_Plugin_TinyAPI](https://github.com/M0nk3yOuO/AstrBot_Plugin_TinyAPI)
- Issue 追踪：[https://github.com/M0nk3yOuO/AstrBot_Plugin_TinyAPI/issues](https://github.com/M0nk3yOuO/AstrBot_Plugin_TinyAPI/issues)

---

⭐ 如果这个插件对你有帮助，请给它一个 Star！
