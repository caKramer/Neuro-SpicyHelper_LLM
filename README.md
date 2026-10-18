# Neuro-SpicyHelper_LLM

Application containing an LLM to help neurodivergent individuals with interoception and executive dysfunction issues

Model:
Ollama llama3.2-3b-ft, imported from Hugging Face [ck-star/llama-3.2-3b-instruct-ft](https://huggingface.co/ck-star/llama-3.2-3b-instruct-ft)

Application:
Created with Streamlit

## Setup

```bash
cd neuro-spicy-app
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt huggingface_hub
./setup_model.sh        # downloads the model weights into model/ and imports them into Ollama (see model/README.md)
streamlit run app.py
```
