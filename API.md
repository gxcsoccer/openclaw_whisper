# OpenClaw Whisper STT API 文档

本地语音转文字服务，基于 [whisper.cpp](https://github.com/ggerganov/whisper.cpp) 构建，为 OpenClaw 飞书机器人提供语音识别能力。

## 基本信息

| 项目 | 值 |
|------|-----|
| 默认地址 | `http://0.0.0.0:8765` |
| 协议 | HTTP |
| 响应格式 | JSON |

---

## 接口列表

### 1. 语音转文字

**`POST /transcribe`**

上传音频文件，返回转录文本。

#### 请求

- **Content-Type:** `multipart/form-data`
- **参数:**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file` | file | 是 | 音频文件，支持 WAV、Opus、OGG、MP3 格式 |

> 非 WAV 格式会自动通过 ffmpeg 转换为 16kHz 单声道 WAV 后再进行识别。

#### 响应

**成功 (200)**

```json
{
  "text": "你好世界"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `text` | string | 转录后的文本内容 |

**失败 (400)** — 文件为空

```json
{
  "detail": "Empty file"
}
```

**失败 (500)** — 转录失败（ffmpeg 转换出错或 whisper.cpp 执行失败）

#### 示例

**cURL:**

```bash
curl -X POST http://127.0.0.1:8765/transcribe \
  -F "file=@voice.opus"
```

**TypeScript:**

```typescript
const formData = new FormData();
formData.append("file", new Blob([fileBuffer]), "voice.opus");

const resp = await fetch("http://127.0.0.1:8765/transcribe", {
  method: "POST",
  body: formData,
  signal: AbortSignal.timeout(120_000),
});

const { text } = await resp.json();
```

**Python:**

```python
import httpx

with open("voice.opus", "rb") as f:
    resp = httpx.post(
        "http://127.0.0.1:8765/transcribe",
        files={"file": ("voice.opus", f)},
    )

print(resp.json()["text"])
```

---

### 2. 健康检查

**`GET /health`**

检查服务是否正常运行。

#### 请求

无参数。

#### 响应

**成功 (200)**

```json
{
  "status": "ok",
  "model": "/path/to/ggml-large-v3.bin"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | string | 服务状态，正常时为 `"ok"` |
| `model` | string | 当前加载的模型文件路径 |

#### 示例

```bash
curl http://127.0.0.1:8765/health
```

---

## 配置项

通过 `.env` 文件或环境变量配置（参考 `.env.example`）：

| 变量 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `WHISPER_BIN` | string | — (必填) | whisper-cli 可执行文件的绝对路径 |
| `WHISPER_MODEL` | string | — (必填) | GGML 模型文件的绝对路径 |
| `WHISPER_LANGUAGE` | string | `zh` | 识别语言代码（如 `en`、`zh`、`ja`） |
| `WHISPER_THREADS` | int | `8` | CPU 线程数 |
| `STT_HOST` | string | `0.0.0.0` | 服务绑定地址 |
| `STT_PORT` | int | `8765` | 服务监听端口 |

---

## 启动服务

```bash
# 安装依赖
pip install -e .

# 配置环境变量
cp .env.example .env
# 编辑 .env，填写 WHISPER_BIN 和 WHISPER_MODEL 路径

# 启动
python -m openclaw_whisper
```

---

## 注意事项

- 系统需预装 **ffmpeg**（用于非 WAV 格式的音频转换）
- 单次转录超时时间为 **300 秒**
- 默认使用 `ggml-large-v3` 模型，30 秒音频约需 3-5 秒完成转录（M4 Pro Mac mini）
