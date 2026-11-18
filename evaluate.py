"""Score BAGEL, and optionally run one local Hugging Face model.

The dataset itself is loaded from Hugging Face once HF_DATASET_ID is set,
or from a local JSONL via --jsonl. This script does not ship the questions.

Reported overall accuracy is the unweighted mean of the Wikipedia, GloBI,
and bioRxiv accuracies. Decoding for a local run matches the paper setting:
greedy, seed 0, at most 16 new tokens, inputs truncated to 1,000 tokens.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

# Fill this in after the dataset is uploaded, for example "org/bagel".
HF_DATASET_ID = ""
GITHUB_REPO = "https://github.com/Patrickhshs/bagel"

DOMAINS = ("wiki", "globi", "biorxiv")
LETTERS = "ABCD"


def build_prompt(item: dict) -> str:
    """Closed-book prompt. Provenance and source text are not included."""
    option_lines = [f"{letter}. {text}" for letter, text in zip(LETTERS, item["options"])]
    return (
        "You are answering a multiple-choice closed-book benchmark question for testing animal expertise.\n"
        "Choose exactly one answer.\n"
        "Output exactly one capital letter: A, B, C, or D.\n"
        "Do not output any explanation, words, punctuation, or extra text.\n\n"
        f"Question: {item['question']}\n"
        "Options:\n"
        + "\n".join(option_lines)
        + "\n\nAnswer:"
    )


def normalize_text(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"\s+", " ", value)
    return value.strip(" .,:;\"'`")


def predict_letter(raw_text: str, options: list[str]) -> str:
    """Map a model string to A-D. Empty string means the output was not a choice."""
    raw = (raw_text or "").strip()
    if not raw or raw.lower() in {"analysis", "final", "answer"}:
        return ""
    letter_match = re.search(r"\b([A-D])\b", raw.upper())
    if letter_match:
        return letter_match.group(1)
    normalized = normalize_text(raw)
    for index, option in enumerate(options):
        if normalize_text(option) == normalized or normalize_text(option) in normalized:
            return LETTERS[index]
    return ""


def score(items: list[dict], predictions: dict[str, str]) -> dict[str, float]:
    """predictions maps item id to a predicted letter."""
    correct = {domain: 0 for domain in DOMAINS}
    total = {domain: 0 for domain in DOMAINS}
    missing = 0
    for item in items:
        domain = item["domain"]
        if domain not in total:
            continue
        total[domain] += 1
        letter = predictions.get(item["id"], "")
        if not letter:
            missing += 1
        elif letter == item["answer_letter"]:
            correct[domain] += 1
    scores = {
        domain: (correct[domain] / total[domain]) if total[domain] else 0.0
        for domain in DOMAINS
    }
    scores["overall"] = sum(scores[domain] for domain in DOMAINS) / len(DOMAINS)
    scores["missing"] = missing
    for domain in DOMAINS:
        scores[f"{domain}_n"] = total[domain]
    return scores


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def load_items(dataset_id: str, jsonl: str, split: str) -> list[dict]:
    if jsonl:
        return load_jsonl(Path(jsonl))
    if not dataset_id:
        raise SystemExit(
            "Set HF_DATASET_ID in evaluate.py, or pass --dataset org/name, or pass --jsonl."
        )
    from datasets import load_dataset

    dataset = load_dataset(dataset_id, split=split)
    return list(dataset)


def load_predictions(path: Path) -> dict[str, str]:
    """Each line needs id and either letter or raw model text in 'prediction'."""
    predictions: dict[str, str] = {}
    items_for_options: dict[str, list[str]] = {}
    for row in load_jsonl(path):
        item_id = str(row["id"])
        if row.get("letter"):
            predictions[item_id] = str(row["letter"]).strip().upper()[:1]
        else:
            options = row.get("options") or items_for_options.get(item_id) or ["", "", "", ""]
            predictions[item_id] = predict_letter(str(row.get("prediction", "")), options)
    return predictions


def run_model(items: list[dict], model_name: str, max_new_tokens: int, max_length: int) -> dict[str, str]:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch.manual_seed(0)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype="auto", device_map="auto")
    model.eval()

    predictions: dict[str, str] = {}
    for item in items:
        prompt = build_prompt(item)
        messages = [{"role": "user", "content": prompt}]
        try:
            text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
        except TypeError:
            text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        encoded = tokenizer(text, return_tensors="pt", truncation=True, max_length=max_length)
        encoded = {key: value.to(model.device) for key, value in encoded.items()}
        with torch.no_grad():
            generated = model.generate(
                **encoded,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
        new_tokens = generated[0, encoded["input_ids"].shape[1] :]
        raw = tokenizer.decode(new_tokens, skip_special_tokens=True)
        predictions[item["id"]] = predict_letter(raw, item["options"])
    return predictions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate BAGEL from a Hugging Face dataset or a local JSONL.")
    parser.add_argument("--dataset", default=HF_DATASET_ID, help="Hugging Face dataset id. Empty until upload.")
    parser.add_argument("--split", default="test")
    parser.add_argument("--jsonl", default="", help="Local JSONL instead of Hugging Face.")
    parser.add_argument("--predictions", default="", help="JSONL of id plus letter or prediction. Scores without running a model.")
    parser.add_argument("--model", default="", help="Local Hugging Face model id or path.")
    parser.add_argument("--max-new-tokens", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=1000)
    parser.add_argument("--output", default="", help="Optional JSONL of id and predicted letter.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    items = load_items(args.dataset, args.jsonl, args.split)
    if args.predictions:
        predictions = load_predictions(Path(args.predictions))
    elif args.model:
        predictions = run_model(items, args.model, args.max_new_tokens, args.max_length)
    else:
        raise SystemExit("Pass --predictions to score a run, or --model to generate answers.")

    scores = score(items, predictions)
    for domain in DOMAINS:
        print(f"{domain:8s} {scores[domain]:.4f}  n={int(scores[f'{domain}_n'])}")
    print(f"{'overall':8s} {scores['overall']:.4f}  (unweighted mean of the three domains)")
    if scores["missing"]:
        print(f"missing predictions: {int(scores['missing'])}")

    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            for item in items:
                handle.write(json.dumps({
                    "id": item["id"],
                    "letter": predictions.get(item["id"], ""),
                    "answer_letter": item["answer_letter"],
                }, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
