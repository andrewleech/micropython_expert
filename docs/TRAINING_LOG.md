# Training Log

This document tracks training runs, hyperparameters, and metrics.

---

## Training Runs

*Training pending - waiting for RTX 8000 access.*

### Dataset Summary

| Dataset | Examples | Purpose |
|---------|----------|---------|
| combined_sft.jsonl | 23,679 | SFT training |
| dpo_preferences.jsonl | 5,359 | DPO alignment |
| held_out_reviews.jsonl | 1,861 | Evaluation |

### Planned Configuration

**SFT Training:**
- Model: Qwen/Qwen3-Coder-8B-Instruct
- Dataset: combined_sft.jsonl (23,679 examples)
- Epochs: 3
- Batch size: 4 (gradient accumulation: 8, effective: 32)
- Learning rate: 2e-5
- Scheduler: cosine with warmup
- Max sequence length: 4096
- Precision: bf16
- Estimated time: 8-12 hours

**DPO Training:**
- Starting checkpoint: SFT output
- Dataset: dpo_preferences.jsonl (5,359 pairs)
- Epochs: 1
- Batch size: 2 (gradient accumulation: 8, effective: 16)
- Learning rate: 5e-7
- Beta: 0.1
- Estimated time: 1-2 hours

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

*To be recorded before SFT training with unmodified Qwen3-Coder-8B-Instruct.*
