# MicroPython Expert

Fine-tuned LLM for MicroPython code review and development assistance, trained on 18,614 categorized code review comments from [dpgeorge](https://github.com/dpgeorge) (Damien George, MicroPython creator).

## Overview

This project fine-tunes Qwen2.5-Coder-7B-Instruct using:
- **SFT (Supervised Fine-Tuning)**: 23,679 examples covering code review, codebase knowledge, and practical guidance
- **DPO (Direct Preference Optimization)**: 5,359 preference pairs for style alignment

The resulting model understands MicroPython internals, coding conventions, and review patterns.

## Data

All training data is included via Git LFS (~142MB):

| Dataset | Examples | Description |
|---------|----------|-------------|
| `reviews_sft.jsonl` | 16,753 | Code review comments converted to instruction format |
| `codebase_qa.jsonl` | 3,936 | Q&A generated from MicroPython source code |
| `wiki_qa.jsonl` | 403 | Q&A from MicroPython GitHub wiki |
| `app_dev_qa.jsonl` | 539 | Practical development guidance |
| `dpo_preferences.jsonl` | 5,359 | Preference pairs for DPO alignment |

Source database: `data/raw/dpgeorge_reviews.db` (SQLite, 18,614 categorized reviews from 5,542 PRs)

## Training

### Requirements

- Python 3.10+
- CUDA GPU with 46GB+ VRAM (full fine-tuning) or 16GB+ (QLoRA)
- ~100 hours training time on RTX 8000

### Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run Training

```bash
# SFT training (QLoRA by default)
CUDA_VISIBLE_DEVICES=0 python training/train_sft.py

# DPO alignment (after SFT completes)
CUDA_VISIBLE_DEVICES=0 python training/train_dpo.py
```

Training config: `training/sft_config.yaml`

## Post-Training Conversion

Convert the trained model for local deployment:

```bash
# 1. Merge LoRA adapters into base model
python scripts/merge_lora.py

# 2. Convert to GGUF (requires llama.cpp)
python scripts/convert_to_gguf.py --quantizations q4_k_m q5_k_m q8_0

# 3. Import to Ollama
python scripts/create_ollama_model.py --quant q4_k_m
```

### Quantization Options

| Format | Size | VRAM | Quality |
|--------|------|------|---------|
| Q8_0 | ~8GB | 8GB+ | ~99% |
| Q5_K_M | ~5.5GB | 6GB+ | ~97% |
| Q4_K_M | ~4.5GB | 5GB+ | ~95% |

## Local Inference

After conversion, run with Ollama:

```bash
ollama run micropython-expert:q4-k-m "Review this MicroPython code for issues"
```

Or use the inference CLI:

```bash
python -m inference.cli chat
python -m inference.cli review --diff changes.patch
```

## Project Structure

```
micropython-expert/
├── data/
│   ├── raw/                 # Source database
│   ├── training/            # SFT and DPO datasets
│   ├── eval/                # Evaluation benchmarks
│   └── wiki/                # MicroPython wiki pages
├── training/
│   ├── train_sft.py         # SFT training script
│   ├── train_dpo.py         # DPO training script
│   ├── sft_config.yaml      # Training configuration
│   └── evaluate.py          # Evaluation metrics
├── scripts/
│   ├── merge_lora.py        # Merge adapters
│   ├── convert_to_gguf.py   # GGUF conversion
│   └── create_ollama_model.py
├── inference/
│   └── cli.py               # Inference CLI
└── docs/
    ├── PLAN.md              # Project plan
    └── JOURNAL.md           # Development log
```

## Related Projects

- [dpgeorge-review-db](https://github.com/andrewleech/dpgeorge-review-db) - RAG system for dpgeorge's review patterns
- [MicroPython](https://github.com/micropython/micropython) - The MicroPython project

## License

MIT License - see [LICENSE](LICENSE).

Training data derived from public GitHub comments. Fine-tuned model weights subject to [Qwen license terms](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct/blob/main/LICENSE).
