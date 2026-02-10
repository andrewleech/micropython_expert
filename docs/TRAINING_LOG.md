# Training Log

This document tracks training runs, hyperparameters, and metrics.

---

## Training Runs

*Training pending - waiting for RTX 8000 access.*

### Dataset Summary

| Dataset | Examples | Purpose |
|---------|----------|---------|
| combined_sft.jsonl | 16,710 (v2) | SFT training |
| dpo_preferences.jsonl | 4,974 (v2) | DPO alignment |
| held_out_reviews.jsonl | 551 (v2, PR-based split) | Evaluation |

### Planned Configuration

**SFT Training:**
- Model: Qwen/Qwen2.5-Coder-7B-Instruct
- Dataset: combined_sft.jsonl (16,710 examples)
- Epochs: 3
- Batch size: 4 (gradient accumulation: 8, effective: 32)
- Learning rate: 2e-5
- Scheduler: cosine with warmup
- Max sequence length: 4096
- Precision: bf16
- Estimated time: 8-12 hours

**DPO Training:**
- Starting checkpoint: SFT output
- Dataset: dpo_preferences.jsonl (4,974 pairs)
- Epochs: 1
- Batch size: 2 (gradient accumulation: 8, effective: 16)
- Learning rate: 5e-7
- Beta: 0.1
- Estimated time: 1-2 hours

**Note:** Actual training used QLoRA (r=64, alpha=128) due to VRAM constraints, not full fine-tuning.

---

## Template for Recording Runs

```
### Run [ID]: [Date]

**Configuration:**
- Dataset: combined_sft.jsonl ([N] examples)
- Epochs: [N]
- Batch size: [N]
- Learning rate: [X]
- Hardware: RTX 8000 (48GB)

**Training Metrics:**
- Final train loss: [X]
- Final eval loss: [X]
- Training time: [X] hours
- Checkpoints saved: [X]

**Notes:**
- [Observations, issues, decisions]
```

---

## Baseline Metrics

*To be recorded before SFT training with unmodified Qwen2.5-Coder-7B-Instruct.*

### v1 Training Results (2026-02-09 Benchmark)

The v1 model (trained on 23,679 SFT examples including issue_comments) scored:
- Review quality: 1.79-2.02/5 (judge: Claude)
- Claude+RAG baseline: 2.63-3.59/5
- Primary failures: "fabricated responses that don't engage with the actual diff", "PR descriptions written from the author's perspective"

Root cause: training data quality (61% issue_comments without diff context). See `docs/LESSONS_LEARNED.md` for details. Training data v2 pipeline addresses these issues.
