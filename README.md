# Neuro-SpicyHelper_LLM

Application containing an LLM to help neurodivergent individuals with interoception and executive dysfunction issues

Model:
Ollama llama3.2-3b-ft, imported from Hugging Face [ck-star/llama-3.2-3b-instruct-ft](https://huggingface.co/ck-star/llama-3.2-3b-instruct-ft)

Full fine-tuning of llama3.2-3b-Instruct using Google Colab. Requires A100 GPU to complete full fine tuning.
Tuned model pushed to [HuggingFace/ck-star](https://huggingface.co/ck-star/llama-3.2-3b-instruct-ft/settings)

Application:
Created with Streamlit


## Setup

```bash
cd neuro-spicy-app
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt huggingface_hub
./setup_model.sh        # downloads the model and imports it into Ollama
streamlit run app.py
```
=======
## 2 Options to run:

- Pull repository and open neuro-spicy-app in PyCharm/VSCode/etc
  - Pull hugging face model locally
```
# in bash - download model
python3 -c '
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="ck-star/llama-3.2-3b-instruct-ft",
    token="yourTokenHere",
    local_dir="llama-3.2-3b-instruct-ft"
)
'

# create the Modelfile pointing directly to your downloaded model directory
echo "FROM ~/wherever_you_have_it/llama-3.2-3b-instruct-ft" > Modelfile

# register model with ollama
ollama create llama3.2-3b-ft -f Modelfile

# verify you see the model
ollama list

# test the model
ollama run llama3.2-3b-ft
```
  - pip install requirements.txt
  - run app with  `streamlit run app.py`
- Run in Jupyter lab
  - pull near-spicyHelper Jupyter notebook & run

