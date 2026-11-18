---
language:
- en
pretty_name: BAGEL
size_categories:
- 1K<n<10K
task_categories:
- question-answering
license: cc-by-sa-4.0
configs:
- config_name: default
  data_files:
  - split: test
    path: bagel.jsonl
---

# BAGEL

BAGEL (Benchmarking Animal knowledGe Expertise in Language models) is a closed-book, four-option benchmark of animal knowledge. This dataset is the evaluation set: 6,822 questions from Wikipedia, GloBI, and bioRxiv. There is no training split.

**Evaluation code:** https://github.com/Patrickhshs/bagel

**Paper:** https://arxiv.org/pdf/2604.16241


<!-- Replace the line above with this dataset's page, for example:
https://huggingface.co/datasets/<namespace>/bagel
-->

This folder is the Hugging Face dataset: this card and `bagel.jsonl`. That file is the `test` split. The loader in the GitHub repository reads that split.

## Fields

| Field | Meaning |
|---|---|
| `id` | Stable item id, such as `wiki-0001` |
| `domain` | `wiki`, `globi`, or `biorxiv` |
| `dimension` | Question type within that domain |
| `question` | Stem shown to the model |
| `options` | Four strings, in order A, B, C, D |
| `answer` | Gold option text |
| `answer_letter` | `A`, `B`, `C`, or `D` |
| `difficulty` | `easy`, `medium`, or `hard` |
| `provenance` | Source pointer for Wikipedia and bioRxiv. Not model input |

| Domain | Questions |
|---|---:|
| Wikipedia | 1,806 |
| GloBI | 3,117 |
| bioRxiv | 1,899 |
| **Total** | **6,822** |

`difficulty` records whether GPT-5.4, Claude Opus 4.6, and Gemini 3.1 Flash Lite got the item right: easy if all three did, medium if one or two did, and hard if none did.

Give a model only `question` and `options`. Do not include `provenance`, `answer`, or `difficulty` in the prompt. The overall score used in the paper is the unweighted mean of the three domain accuracies. The scoring script is in the GitHub repository linked above.

Questions were written from English Wikipedia, Global Biotic Interactions, and animal-related bioRxiv preprints, then screened for incorrect or ambiguous gold labels. Article text, interaction tables, and preprint bodies are not included.

## License

The questions are released under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Credit the sources when you reuse them:

- Wikipedia items: the article title in `provenance.wikipedia_title`, and the Wikipedia text license (CC BY-SA 4.0).
- GloBI items: Global Biotic Interactions and the original contributing datasets. GloBI's integrated data are available under CC BY 4.0 unless a source says otherwise.
- bioRxiv items: the paper authors and `provenance.doi`.

bioRxiv redistribution follows each article's own license. Before a public release, drop any item whose source paper is CC BY-NC, CC BY-ND, or not openly licensed. Those items cannot sit in this CC BY-SA set.
