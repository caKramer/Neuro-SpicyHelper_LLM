# Model bundle: llama3.2-3b-ft

Fine-tuned Llama 3.2 3B Instruct used by the Decision Assistant in `app.py`, which calls it through
Ollama as `llama3.2-3b-ft`.

- **Source:** Hugging Face [ck-star/llama-3.2-3b-instruct-ft](https://huggingface.co/ck-star/llama-3.2-3b-instruct-ft)
- **Base model:** Llama 3.2 3B Instruct, fine-tuned with TRL SFT
- **Format:** safetensors (bfloat16), imported into Ollama with `int8` quantization (~3.8 GB)

## Files

| File | Purpose |
|---|---|
| `model.safetensors` | Model weights (6.4 GB). **Not committed** (over GitHub's 100 MB limit); run `../setup_model.sh` to download it |
| `config.json` | Model config, patched for Ollama (see below) |
| `config.original.json` | Unmodified config as published on Hugging Face |
| `generation_config.json` | Default sampling settings and stop tokens |
| `tokenizer.json`, `tokenizer_config.json` | Tokenizer |
| `chat_template.jinja` | Llama 3 chat template |
| `Modelfile` | Ollama build file |
| `MODEL_CARD.md` | Model card from Hugging Face |

## Import into Ollama

From `neuro-spicy-app/`:

```bash
./setup_model.sh
```

This downloads any missing files, applies the config patch, and runs
`ollama create llama3.2-3b-ft -f model/Modelfile --quantize int8`.

If `model.safetensors` is already present, you can import directly:

```bash
cd model && ollama create llama3.2-3b-ft -f Modelfile --quantize int8
```

## Config patch

The published `config.json` stores RoPE settings under the transformers 5 `rope_parameters` key.
Ollama's importer doesn't read that key, so the model loses its llama3 RoPE scaling. It still
answers short prompts, but long ones (like Food Options, ~2,000 tokens) come back as garbage.
The patched `config.json` copies the same values to the top-level `rope_theta` and
`rope_scaling` keys that Ollama reads. Nothing else differs from `config.original.json`.

## How the app calls it

`app.py` sends a raw Llama 3 prompt to `http://127.0.0.1:11434/api/generate` with
`"raw": true`, so Ollama's prompt template is bypassed. Stop tokens: `<|eot_id|>`, `<|eom_id|>`,
`<|start_header_id|>`, `<|end_header_id|>`.
