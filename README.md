# BAGEL

BAGEL (Benchmarking Animal knowledGe Expertise in Language models) is a closed-book, four-option benchmark of animal knowledge. This repository is the evaluation set: 6,822 questions from Wikipedia, GloBI, and bioRxiv. There is no training or development split.

A model should see only the question and the four options. Do not add `provenance` to the prompt. The overall score is the unweighted mean of the three domain accuracies.

## Data

`data/bagel.jsonl` has one JSON object per line.

| Field | Meaning |
|---|---|
| `id` | Stable item id, such as `wiki-0001` |
| `domain` | `wiki`, `globi`, or `biorxiv` |
| `dimension` | Question type within that domain |
| `question` | Stem |
| `options` | Four strings, in order A, B, C, D |
| `answer` | Gold option text |
| `answer_letter` | `A`, `B`, `C`, or `D` |
| `difficulty` | `easy`, `medium`, or `hard` |
| `provenance` | Source pointer. Present for Wikipedia and bioRxiv. Not model input |

Counts:

| Domain | Questions |
|---|---:|
| Wikipedia | 1,806 |
| GloBI | 3,117 |
| bioRxiv | 1,899 |
| **Total** | **6,822** |

`difficulty` is a reference label from three frontier models (GPT-5.4, Claude Opus 4.6, and Gemini 3.1 Flash Lite): easy if all three are correct, medium if one or two are correct, and hard if none is correct. It is not an independent measure of biological difficulty.

## Load and score

```python
import json
from pathlib import Path

def load_bagel(path="data/bagel.jsonl"):
    with Path(path).open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]

items = load_bagel()
assert len(items) == 6822

def prompt(item):
    letters = "ABCD"
    options = "\n".join(f"{letter}. {text}" for letter, text in zip(letters, item["options"]))
    return (
        "Choose exactly one answer. Output only A, B, C, or D.\n\n"
        f"Question: {item['question']}\n"
        f"Options:\n{options}\n\n"
        "Answer:"
    )

def domain_accuracy(items, predictions):
    """predictions maps item id to a letter."""
    correct = {name: [0, 0] for name in ("wiki", "globi", "biorxiv")}
    for item in items:
        hit, total = correct[item["domain"]]
        correct[item["domain"]] = [hit + (predictions[item["id"]] == item["answer_letter"]), total + 1]
    scores = {name: hit / total for name, (hit, total) in correct.items()}
    scores["overall"] = sum(scores.values()) / 3
    return scores
```

## Sources

Questions were written from English Wikipedia species articles, Global Biotic Interactions records, and animal-related bioRxiv preprints, then screened to remove items with an incorrect gold label or more than one defensible answer. Article text, interaction tables, and preprint bodies are not in this file. `provenance.wikipedia_title` and `provenance.doi` identify the source. Obtain the source itself from Wikipedia, GloBI, or bioRxiv under that source's terms.

## License

No dataset license is assigned yet. This repository is private until a license is chosen.
