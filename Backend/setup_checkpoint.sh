#!/bin/bash
# Setup script for downloading Arabic model checkpoint during deployment
# This can be called during Render build process

set -e

echo "=========================================="
echo "Arabic Model Checkpoint Setup"
echo "=========================================="

# Check if checkpoint download is needed
if [ -z "$LOCAL_MODEL_CHECKPOINT_PATH" ]; then
    export LOCAL_MODEL_CHECKPOINT_PATH="/tmp/checkpoints/checkpoint-100000"
fi

CHECKPOINT_DIR="$LOCAL_MODEL_CHECKPOINT_PATH"

# Check if checkpoint already exists
if [ -f "$CHECKPOINT_DIR/adapter_model.safetensors" ]; then
    echo "✅ Checkpoint already exists at $CHECKPOINT_DIR"
    exit 0
fi

echo "📥 Checkpoint not found. Attempting download..."

# Navigate to Base_backend directory
cd "$(dirname "$0")/Base_backend" || exit 1

# Run download script
python download_checkpoint.py

if [ $? -eq 0 ]; then
    echo "✅ Checkpoint setup completed successfully"
    exit 0
else
    echo "⚠️ Checkpoint download failed or not configured"
    echo "The Arabic model will use fallback providers (Groq/OpenAI)"
    exit 0  # Don't fail deployment, just warn
fi









