# micropython-expert CLAUDE.md

This file provides context for AI coding agents working on the MicroPython Expert fine-tuning project.

## Project Overview

This project creates a fine-tuned model (no RAG) that provides:
1. **Code review** in dpgeorge's style and standards
2. **Architectural guidance** for MicroPython core development
3. **Application development guidance** for end-users building on MicroPython
4. **Intimate knowledge** of the entire MicroPython codebase (all 20 ports)

## Current Status

**Phase:** Data preparation complete - ready for training

| Component | Status | Details |
|-----------|--------|---------|
| Review SFT dataset | ✅ Complete | 16,753 training + 1,861 eval |
| Wiki Q&A | ✅ Complete | 403 examples from 80 wiki pages |
| Codebase Q&A | ✅ Complete | 3,936 examples from 412 source files |
| App dev Q&A | ✅ Complete | 539 examples across 12 topics |
| DPO preferences | ✅ Complete | 5,359 preference pairs |
| Eval benchmarks | ✅ Complete | 408 total (factual, port, style) |
| Combined dataset | ✅ Complete | 23,679 weighted examples |
| Training | ⏳ Pending | Waiting for RTX 8000 access |

## Training Data Summary

| Dataset | Original | Weight | After Weighting |
|---------|----------|--------|-----------------|
| reviews_sft | 16,753 | 1.0 | 16,753 |
| wiki_qa | 403 | 1.2 | 483 |
| codebase_qa | 3,936 | 1.5 | 5,904 |
| app_dev_qa | 539 | 1.0 | 539 |
| **combined_sft** | | | **23,679** |

## Directory Structure

```
micropython-expert/
├── micropython/                    # Submodule pinned to v1.27.0
├── data/
│   ├── raw/dpgeorge_reviews.db     # Source: 18,614 categorized reviews
│   ├── wiki/                       # 80 scraped wiki pages
│   ├── training/
│   │   ├── reviews_sft.jsonl       # ✅ 16,753 examples (40MB)
│   │   ├── wiki_qa.jsonl           # ✅ 403 examples (0.5MB)
│   │   ├── codebase_qa.jsonl       # ✅ 3,936 examples (4.2MB)
│   │   ├── app_dev_qa.jsonl        # ✅ 539 examples (0.6MB)
│   │   ├── dpo_preferences.jsonl   # ✅ 5,359 pairs (10MB)
│   │   └── combined_sft.jsonl      # ✅ 23,679 examples (weighted)
│   └── eval/
│       ├── held_out_reviews.jsonl  # ✅ 1,861 examples
│       ├── factual_qa.jsonl        # ✅ 113 examples
│       ├── port_knowledge.jsonl    # ✅ 95 examples
│       └── style_benchmark.jsonl   # ✅ 200 examples
├── scripts/                        # Data preparation scripts
├── training/                       # Training scripts and configs
├── models/                         # Trained model outputs (empty)
├── inference/                      # CLI for trained model
├── docs/                           # Documentation
│   ├── PLAN.md                     # Full implementation plan
│   ├── JOURNAL.md                  # Development log
│   ├── DATA_PREPARATION.md         # Dataset details
│   ├── REMOTE_DEPLOYMENT.md        # Remote training guide
│   ├── TRAINING_LOG.md             # Training run tracking
│   └── EVALUATION_RESULTS.md       # Benchmark results
└── setup_remote.sh                 # RTX 8000 setup script
```

## Next Steps: Remote Training

See `docs/REMOTE_DEPLOYMENT.md` for detailed instructions.

Quick summary:
```bash
# 1. Copy to remote
rsync -avz --exclude 'venv/' --exclude '.git/' \
  /home/anl/mpy/micropython-expert/ remote:micropython-expert/

# 2. On remote machine
cd micropython-expert
./setup_remote.sh

# 3. Start training in tmux
tmux new -s training
source venv/bin/activate
python training/train_sft.py 2>&1 | tee logs/sft_$(date +%Y%m%d_%H%M%S).log

# 4. After SFT (~8-12h), run DPO
python training/train_dpo.py 2>&1 | tee logs/dpo_$(date +%Y%m%d_%H%M%S).log
```

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

- **Training**: RTX 8000 (48GB VRAM) via SSH
- **Deployment**: Cloud, local GPU, or AMD NPU (quantized GGUF)

## Documentation

For detailed information:
- `docs/PLAN.md` - Complete implementation plan with rationale
- `docs/JOURNAL.md` - Running log of work done
- `docs/DATA_PREPARATION.md` - Dataset format and generation details
- `docs/REMOTE_DEPLOYMENT.md` - Step-by-step remote training guide
