#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WHISPER_DIR="$SCRIPT_DIR/vendor/whisper.cpp"
MODEL_NAME="large-v3"

echo "=== OpenClaw Whisper Setup ==="
echo ""

# 1. Install cmake if needed
if ! command -v cmake &>/dev/null; then
    echo "[1/4] Installing cmake..."
    brew install cmake
else
    echo "[1/4] cmake already installed"
fi

# 2. Clone & build whisper.cpp
if [ ! -f "$WHISPER_DIR/build/bin/whisper-cli" ]; then
    echo "[2/4] Building whisper.cpp with Metal support..."
    mkdir -p "$SCRIPT_DIR/vendor"

    if [ ! -d "$WHISPER_DIR" ]; then
        git clone https://github.com/ggerganov/whisper.cpp "$WHISPER_DIR"
    fi

    cd "$WHISPER_DIR"
    cmake -B build -DWHISPER_METAL=ON
    cmake --build build -j$(sysctl -n hw.ncpu)
    cd "$SCRIPT_DIR"
    echo "    Built successfully"
else
    echo "[2/4] whisper.cpp already built"
fi

# Find the actual binary name
WHISPER_BIN=""
for name in whisper-cli main; do
    if [ -f "$WHISPER_DIR/build/bin/$name" ]; then
        WHISPER_BIN="$WHISPER_DIR/build/bin/$name"
        break
    fi
done

if [ -z "$WHISPER_BIN" ]; then
    echo "ERROR: Could not find whisper binary in $WHISPER_DIR/build/bin/"
    ls "$WHISPER_DIR/build/bin/" 2>/dev/null
    exit 1
fi

echo "    Binary: $WHISPER_BIN"

# 3. Download model
MODEL_DIR="$SCRIPT_DIR/models"
MODEL_FILE="$MODEL_DIR/ggml-$MODEL_NAME.bin"

if [ ! -f "$MODEL_FILE" ]; then
    echo "[3/4] Downloading ggml-$MODEL_NAME model (~3GB, be patient)..."
    mkdir -p "$MODEL_DIR"

    # Use huggingface directly — more reliable than the shell script
    MODEL_URL="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-${MODEL_NAME}.bin"
    curl -L --progress-bar -o "$MODEL_FILE" "$MODEL_URL"

    echo "    Model downloaded: $MODEL_FILE"
else
    echo "[3/4] Model already exists: $MODEL_FILE"
fi

# 4. Create .env
ENV_FILE="$SCRIPT_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "[4/4] Creating .env..."
    cat > "$ENV_FILE" <<EOF
WHISPER_BIN=$WHISPER_BIN
WHISPER_MODEL=$MODEL_FILE
WHISPER_LANGUAGE=zh
WHISPER_THREADS=8
STT_HOST=0.0.0.0
STT_PORT=8765

# Feishu (fill in your credentials)
FEISHU_APP_ID=
FEISHU_APP_SECRET=
EOF
    echo "    Created $ENV_FILE"
else
    echo "[4/4] .env already exists, updating whisper paths..."
    # Update paths in existing .env
    sed -i '' "s|^WHISPER_BIN=.*|WHISPER_BIN=$WHISPER_BIN|" "$ENV_FILE"
    sed -i '' "s|^WHISPER_MODEL=.*|WHISPER_MODEL=$MODEL_FILE|" "$ENV_FILE"
fi

echo ""
echo "=== Setup complete ==="
echo ""
echo "Quick test:"
echo "  pip install -e ."
echo "  python -m openclaw_whisper"
echo ""
echo "Then in another terminal:"
echo "  curl -X POST http://localhost:8765/transcribe -F 'file=@your_audio.wav'"
