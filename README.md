# OpenClaw Whisper STT

Mac mini M4 Pro 本地语音转文字服务，基于 [whisper.cpp](https://github.com/ggerganov/whisper.cpp) + Metal GPU 加速，为 OpenClaw 飞书 bot 提供语音消息转写能力。

## 架构

```
飞书语音消息 → OpenClaw (feishu 扩展) → 本地 STT 服务 (localhost:8765) → whisper.cpp → 转写文本
```

OpenClaw 飞书扩展收到语音消息后，调用本地 HTTP 服务转写，agent 收到的是 `[语音转文字] xxx` 文本，无需改动 OpenClaw 核心代码。

## 快速开始

### 1. 一键安装

```bash
cd /path/to/openclaw_whisper
bash setup.sh
```

脚本会自动：
- 安装 cmake（如果没有）
- 编译 whisper.cpp（Metal 加速自动启用）
- 下载 large-v3 模型（~3GB）
- 生成 `.env` 配置

### 2. 手动安装

```bash
# 编译 whisper.cpp
brew install cmake
git clone https://github.com/ggerganov/whisper.cpp vendor/whisper.cpp
cd vendor/whisper.cpp
cmake -B build -DWHISPER_METAL=ON
cmake --build build -j$(sysctl -n hw.ncpu)
cd ../..

# 下载模型
mkdir -p models
curl -L -o models/ggml-large-v3.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin

# 安装 Python 依赖
pip install -e .

# 配置
cp .env.example .env
# 编辑 .env 填入路径
```

### 3. 启动服务

```bash
# 前台运行
python -m openclaw_whisper

# 后台运行
nohup python -m openclaw_whisper > stt.log 2>&1 &

# 验证
curl --noproxy '*' http://127.0.0.1:8765/health
```

### 4. 对接 OpenClaw

将以下两个文件放入 `~/.openclaw/extensions/feishu/src/`：

**stt.ts** — STT 服务客户端（已包含在本仓库 `patch/` 目录）

**bot.ts** — 需添加两处改动：

```diff
+ import { transcribeAudio } from "./stt.js";

  // 在 mediaPayload 之后、quotedContent 之前添加：
+ if (event.message.message_type === "audio" && mediaList.length > 0) {
+   try {
+     const transcription = await transcribeAudio(mediaList[0].path, log);
+     if (transcription) {
+       ctx.content = `[语音转文字] ${transcription}`;
+     }
+   } catch (err) {
+     log(`audio transcription failed: ${String(err)}`);
+   }
+ }
```

改完后重启 OpenClaw 即可。

## API

### POST /transcribe

上传音频文件，返回转写文本。支持 wav/opus/ogg/mp3 格式，非 wav 自动通过 ffmpeg 转换。

```bash
curl --noproxy '*' -X POST http://127.0.0.1:8765/transcribe \
  -F "file=@audio.wav"
# {"text": "你好世界"}
```

### GET /health

```bash
curl --noproxy '*' http://127.0.0.1:8765/health
# {"status": "ok", "model": "/path/to/ggml-large-v3.bin"}
```

## 配置

通过 `.env` 文件或环境变量：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `WHISPER_BIN` | — | whisper-cli 路径 |
| `WHISPER_MODEL` | — | ggml 模型文件路径 |
| `WHISPER_LANGUAGE` | `zh` | 识别语言 |
| `WHISPER_THREADS` | `8` | CPU 线程数 |
| `STT_HOST` | `0.0.0.0` | 监听地址 |
| `STT_PORT` | `8765` | 监听端口 |
| `STT_SERVER_URL` | `http://127.0.0.1:8765` | OpenClaw 侧 stt.ts 调用地址 |

## 性能（M4 Pro, large-v3）

- 30 秒语音 ≈ 3-5 秒转写
- Metal GPU 加速自动启用
- 如需更快可换 `medium` 模型（中文效果也不错）

## 项目结构

```
openclaw_whisper/
├── setup.sh                  # 一键安装脚本
├── .env.example              # 配置模板
├── pyproject.toml
├── openclaw_whisper/
│   ├── __main__.py           # 入口: python -m openclaw_whisper
│   ├── config.py             # 配置管理
│   ├── stt_server.py         # FastAPI HTTP 服务
│   ├── transcriber.py        # whisper.cpp 调用封装
│   ├── audio.py              # ffmpeg 音频格式转换
│   ├── feishu.py             # 飞书 API 客户端（备用）
│   └── handler.py            # 高层集成接口（备用）
├── patch/
│   └── stt.ts                # OpenClaw 飞书扩展补丁
├── vendor/whisper.cpp/       # whisper.cpp（gitignore）
└── models/                   # 模型文件（gitignore）
```

## 依赖

- Python ≥ 3.10
- ffmpeg（`brew install ffmpeg`）
- Xcode Command Line Tools（编译 whisper.cpp）
