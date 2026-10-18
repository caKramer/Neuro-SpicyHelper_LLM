#!/usr/bin/env bash
# Imports the fine-tuned Hugging Face model into Ollama as "llama3.2-3b-ft" (the name app.py uses).
# Requires: ollama (running) and the Hugging Face CLI (`pip install huggingface_hub`).
set -euo pipefail

HF_REPO="ck-star/llama-3.2-3b-instruct-ft"
MODEL_NAME="llama3.2-3b-ft"
MODEL_DIR="$(cd "$(dirname "$0")" && pwd)/model"

hf download "$HF_REPO" --local-dir "$MODEL_DIR"

# The checkpoint stores RoPE settings under the transformers-5 "rope_parameters" key, which
# Ollama's importer ignores. Without the llama3 RoPE scaling, long prompts produce garbage,
# so copy them to the legacy top-level "rope_theta" / "rope_scaling" keys.
python3 - "$MODEL_DIR/config.json" <<'EOF'
import json, sys
path = sys.argv[1]
config = json.load(open(path))
rope = config.get("rope_parameters")
if rope:
    config["rope_theta"] = rope["rope_theta"]
    config["rope_scaling"] = {k: v for k, v in rope.items() if k != "rope_theta"}
    json.dump(config, open(path, "w"), indent=2)
EOF

printf 'FROM %s\nPARAMETER stop <|eot_id|>\n' "$MODEL_DIR" > "$MODEL_DIR/Modelfile"
ollama create "$MODEL_NAME" -f "$MODEL_DIR/Modelfile" --quantize int8

echo "Imported $MODEL_NAME. The downloaded files in $MODEL_DIR can be deleted."
