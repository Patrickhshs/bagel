# BAGEL evaluation

Code for the closed-book BAGEL evaluation. The questions are not stored in this repository. They will be released as a Hugging Face dataset.

**Dataset:** [to be filled in after upload](https://huggingface.co/datasets/EarthSpeciesProject/BAGEL)

<!-- Replace the line above with the dataset page, for example:
https://huggingface.co/datasets/<namespace>/bagel
Also set HF_DATASET_ID in evaluate.py.
-->

**This repository:** https://github.com/Patrickhshs/bagel

**Paper:** https://arxiv.org/pdf/2604.16241

The dataset card to upload with the questions is `hf/README.md`. It links back here.

The questions are released under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Attribution requirements, including the bioRxiv per-article check, are in `hf/README.md`.

## What this measures

Each item is a four-option question. The model sees the question and the options only. The reported overall score is the unweighted mean of accuracy on Wikipedia, GloBI, and bioRxiv.

The paper setting for a local run is greedy decoding, seed 0, at most 16 new tokens, and inputs truncated to 1,000 tokens.

## Score a finished run

Predictions are a JSONL file with `id` and either `letter` or `prediction` (the raw model string).

```bash
python evaluate.py --jsonl /path/to/bagel.jsonl --predictions predictions.jsonl
```

After the dataset id is filled in:

```bash
python evaluate.py --dataset <namespace>/bagel --predictions predictions.jsonl
```

## Run one local model

```bash
pip install -r requirements.txt torch transformers
python evaluate.py --dataset <namespace>/bagel --model <hf-model-id-or-path>
```

`evaluate.py` uses the same instruction text as the paper evaluation: one capital letter, no explanation. API models are not wrapped here. Use the same prompt from `build_prompt` and the same scoring rule.

## Layout

| File | Role |
|---|---|
| `evaluate.py` | Prompt, letter parsing, and the three-domain mean |
| `hf/README.md` | Dataset card for the Hugging Face upload |
| `requirements.txt` | `datasets` for loading the split |
