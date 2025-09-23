## 🧭 方向探索派对 · 历史模式 & Meme 生成

一款面向普通用户的 AI 娱乐创作工具。我们致力于将专业内容创作者的“节目效果”能力，赋能给每一位用户，让大家都能轻松创造并分享属于自己的爆款 Meme，并通过历史模式探索地点在不同时期的趣味故事与知识。

## ✨ 功能特性

### 核心能力
- **历史模式（主打）**：基于地理位置与方向/路径采样，展示近现代（如约100年前）的历史事件、趣闻与背景信息，支持分段距离取样与卡片化展示。
- **Meme 生成（主打）**：使用模板化 Prompt 与大语言模型自动生成文案梗点，结合图片素材打造“一键出梗”的创作体验。
- **模板系统**：内置多种 Meme Prompt 模板，支持变量占位、语气风格与场景切换（见 `backend/meme_prompt_templates.json`）。
- **模式切换**：在“历史模式”和“Meme 生成”之间一键切换，创作与探索自由流转。
- **可视化与交互**：卡片流展示、图片与文字并重，强调“节目效果”的表达方式。

### 进阶能力
- **方向与定位（可选）**：利用设备方向与地理位置增强历史探索的临场感。
- **路径大圆航线计算**：在地球表面按设定间隔采样，沿路径展示地点卡片。
- **分段距离与速度**：可调节分段距离（如 50/100/200km）与虚拟移动速度，控制内容密度与节奏。

## 🛠️ 技术栈

### 前端
- **HTML5 / CSS3 / JavaScript**
- 浏览器能力：`DeviceOrientationEvent`（方向检测，可选）、`Geolocation`（位置获取，可选）、`Fetch API`（后端通信）

### 后端
- **Python FastAPI**（高性能 API 框架）
- **Pydantic**（数据校验与序列化）
- **Uvicorn**（ASGI 服务器）
- **CORS**（跨域支持）
- **GeographicLib**（大圆航线与地理计算，用于历史模式路径采样）

### AI/生成
- **LLM 接入：Google Gemini**（通过环境变量注入 API Key）
- **Prompt 模板**：`backend/meme_prompt_templates.json`（支持风格、场景与变量占位）
- 可扩展到其他大模型提供商（按需替换接入层）

### 数据与资源
- 静态 JSON/图片等资源（地点、描述、素材）
- 统一的模板与素材管理，方便扩展与协作

## 🚀 快速开始

### 环境要求
- Python 3.8+
- 现代浏览器（建议移动端获取更好体验；桌面端可用方向模拟）

推荐使用 pyenv 管理 Python 版本。

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置环境变量
```bash
# 必需：Gemini API Key
export GEMINI_API_KEY=你的_Gemini_API_Key
```

### 启动方式（两个终端分别运行）
```bash
python start_backend.py
python start_frontend.py
```

- 后端默认运行在 `http://localhost:8000`（文档 `http://localhost:8000/docs`）
- 前端默认运行在 `http://localhost:3000`

## 📖 使用说明

1. 打开前端页面，首次进入可授权“地理位置/方向”（用于提升历史模式体验）。
2. 在顶部或设置区选择模式：
   - **历史模式**：设置分段距离 → 选择/确认方向或路径 → 生成沿途地点卡片 → 浏览历史事件与趣闻。
   - **Meme 生成**：选择模板 → 填写变量（如主题、对象、语气）→ 一键生成 → 复制文案或下载图片/卡片。
3. 可随时在两种模式间切换，组合“历史趣味 + 节目效果”创作更具话题性。

## 🧩 目录结构（简要）

```
direction-exploration-party/
├── index.html                  # 前端主页面
├── styles.css                  # 样式
├── app.js                      # 前端逻辑（模式切换、请求、渲染）
├── backend/
│   ├── main.py                 # FastAPI 主入口
│   ├── meme_prompt_templates.json  # Meme Prompt 模板库
│   └── ...                     # 其它后端模块
├── requirements.txt            # Python 依赖
├── start_backend.py            # 后端启动脚本
├── start_frontend.py           # 前端启动脚本
└── README.md                   # 项目说明
```

## 🔌 API（示例，具体以实际代码为准）
- `POST /api/explore`：历史模式探索（输入位置/方向/分段距离等，返回地点卡片）
- `POST /api/meme/generate`：根据选择的模板与变量生成 Meme 文案/卡片
- `GET /api/health`：健康检查
- `GET /docs`：OpenAPI 文档

## ⚙️ 配置项（建议）

- **环境变量**
  - `GEMINI_API_KEY`：用于 Meme 生成模型调用
  - 可根据需要扩展：`MODEL_NAME`、`HTTP_PROXY`、`HTTPS_PROXY` 等

- **模板扩展**
  - 在 `backend/meme_prompt_templates.json` 中新增或调整模板、变量占位与风格
  - 统一维护模板命名、变量命名与中文注释，便于协作

## ❓常见问题

- **浏览器不触发方向事件**：部分桌面浏览器不支持或需手动授权；可使用内置模拟或直接使用历史模式的列表/路径视图。
- **生成失败或为空**：检查 `GEMINI_API_KEY` 是否配置；稍后重试或更换模板与变量。
- **跨域问题**：确保后端已开启 CORS；前后端地址一致或正确配置代理。

## 🤝 贡献指南
1. Fork 仓库并创建功能分支
2. 提交更改（建议遵循规范化提交信息）
3. 发起 Pull Request，描述变更点与验证方式

## 📄 许可证
MIT License（详见 `LICENSE`）

## 🙏 致谢
- FastAPI（`https://fastapi.tiangolo.com/`）
- GeographicLib（`https://geographiclib.sourceforge.io/`）
- Google Gemini（`https://ai.google.dev/`）

—— 让“节目效果”成为每个人的日常创作力。🎭✨