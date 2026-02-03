# micropython-expert CLAUDE.md

This file provides context for AI coding agents working on the MicroPython Expert fine-tuning project.

## Project Overview

This project creates a fine-tuned model (no RAG) that provides:
1. **Code review** in dpgeorge's style and standards
2. **Architectural guidance** for MicroPython core development
3. **Application development guidance** for end-users building on MicroPython
4. **Intimate knowledge** of the entire MicroPython codebase (all 22 ports)

## Current Status

**Phase:** Data preparation - partially complete

| Component | Status | Details |
|-----------|--------|---------|
| Review SFT dataset | ✅ Complete | 16,753 training + 1,861 eval examples |
| Wiki Q&A | ✅ Complete | 403 examples from 80 wiki pages |
| DPO preferences | ✅ Complete | 5,359 preference pairs |
| Codebase Q&A | ⏳ Pending | Target: 10-20K examples |
| App dev Q&A | ⏳ Pending | Target: 3-5K examples |
| Eval benchmarks | ⏳ Pending | factual_qa, port_knowledge, style_benchmark |
| Combined dataset | ⏳ Pending | Merge all with weighting |
| Training | ⏳ Pending | Waiting for RTX 8000 access |

## Next Steps

Run these commands in order:

```bash
cd /home/anl/mpy/micropython-expert
source venv/bin/activate

# 1. Generate codebase Q&A (uses Claude CLI, ~2-4 hours)
python scripts/generate_codebase_qa.py

# 2. Generate app dev Q&A (uses Claude CLI, ~1-2 hours)
python scripts/generate_app_dev_qa.py

# 3. Generate evaluation benchmarks
python scripts/generate_eval_benchmark.py --all

# 4. Combine all datasets with weighting
python scripts/combine_datasets.py
```

After data prep, copy to RTX 8000 and train:
```bash
# On remote machine
./setup_remote.sh
python training/train_sft.py
python training/train_dpo.py
```

## Directory Structure

```
micropython-expert/
├── data/
│   ├── raw/dpgeorge_reviews.db      # Source: 18,614 categorized reviews
│   ├── wiki/                        # ✅ 80 scraped wiki pages
│   ├── training/
│   │   ├── reviews_sft.jsonl        # ✅ 16,753 examples (40MB)
│   │   ├── wiki_qa.jsonl            # ✅ 403 examples (0.5MB)
│   │   ├── dpo_preferences.jsonl    # ✅ 5,359 pairs (10MB)
│   │   ├── codebase_qa.jsonl        # ⏳ Pending
│   │   ├── app_dev_qa.jsonl         # ⏳ Pending
│   │   └── combined_sft.jsonl       # ⏳ Pending
│   └── eval/
│       ├── held_out_reviews.jsonl   # ✅ 1,861 examples
│       ├── factual_qa.jsonl         # ⏳ Pending
│       ├── port_knowledge.jsonl     # ⏳ Pending
│       └── style_benchmark.jsonl    # ⏳ Pending
├── scripts/                         # Data preparation scripts
├── training/                        # Training scripts and configs
├── models/                          # Trained model outputs (empty)
├── inference/                       # CLI for trained model
├── docs/                            # Documentation
│   ├── PLAN.md                      # Full implementation plan
│   ├── JOURNAL.md                   # Development log
│   ├── DATA_PREPARATION.md          # Dataset details
│   ├── TRAINING_LOG.md              # Training run tracking
│   └── EVALUATION_RESULTS.md        # Benchmark results
└── setup_remote.sh                  # RTX 8000 setup script
```

## Key Scripts

| Script | Purpose | Status |
|--------|---------|--------|
| `scripts/export_sft_dataset.py` | Convert reviews to SFT format | ✅ Run |
| `scripts/scrape_wiki.py` | Scrape GitHub wiki | ✅ Run |
| `scripts/export_dpo_dataset.py` | Create DPO preference pairs | ✅ Run |
| `scripts/generate_codebase_qa.py` | Generate Q&A from source code | ⏳ Ready |
| `scripts/generate_app_dev_qa.py` | Generate practical Q&A | ⏳ Ready |
| `scripts/generate_eval_benchmark.py` | Create eval benchmarks | ⏳ Ready |
| `scripts/combine_datasets.py` | Merge datasets with weighting | ⏳ Ready |
| `training/train_sft.py` | SFT training with checkpointing | ⏳ Ready |
| `training/train_dpo.py` | DPO alignment | ⏳ Ready |
| `training/evaluate.py` | Run evaluation benchmarks | ⏳ Ready |

## Base Model

**Qwen3-Coder-8B-Instruct** (Dense)
- 8B parameters, 256K context
- Source: https://huggingface.co/Qwen/Qwen3-Coder-8B-Instruct

## Training Configuration

**SFT (3 epochs, ~8-12h on RTX 8000):**
- Batch: 4 × 8 gradient accumulation = 32 effective
- LR: 2e-5, cosine scheduler
- Max seq length: 4096
- bf16, gradient checkpointing

**DPO (~1-2h):**
- 1 epoch, beta=0.1
- LR: 5e-7

## Success Criteria

| Metric | Target | Blocking |
|--------|--------|----------|
| Factual Q&A accuracy | >90% | Yes |
| Issue detection rate | >85% | Yes |
| Severity calibration | >90% | Yes |
| Per-port accuracy | >90% all | Yes |
| Style A/B win rate | >70% | No |

## Hardware

- **Training**: RTX 8000 (48GB VRAM) via SSH - access pending
- **Deployment**: Cloud, local GPU, or AMD NPU (quantized GGUF)

## Documentation

For detailed information:
- `docs/PLAN.md` - Complete implementation plan with rationale
- `docs/JOURNAL.md` - Running log of work done
- `docs/DATA_PREPARATION.md` - Dataset format and generation details
