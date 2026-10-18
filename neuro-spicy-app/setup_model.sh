#!/usr/bin/env bash
# Imports the fine-tuned model in model/ into Ollama as "llama3.2-3b-ft" (the name app.py uses).
# Requires: ollama (running) and the Hugging Face CLI (`pip install huggingface_hub`).
# See model/README.md for details, including why model/config.json is patched.
set -euo pipefail

HF_REPO="ck-star/llama-3.2-3b-instruct-ft"
MODEL_NAME="llama3.2-3b-ft"
MODEL_DIR="$(cd "$(dirname "$0")" && pwd)/model"

# The weights are too large for git; everything else in model/ is committed.
hf download "$HF_REPO" model.safetensors --local-dir "$MODEL_DIR"

cd "$MODEL_DIR"
ollama create "$MODEL_NAME" -f Modelfile --quantize int8

echo "Imported $MODEL_NAME into Ollama."
