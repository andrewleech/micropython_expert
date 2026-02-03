# Training Log

This document tracks training runs, hyperparameters, and metrics.

---

## Training Runs

*No training runs yet. Training will be performed on RTX 8000 (48GB VRAM).*

### Planned Configuration

**SFT Training:**
- Model: Qwen/Qwen3-Coder-8B-Instruct
- Epochs: 3
- Batch size: 4 (gradient accumulation: 8, effective: 32)
- Learning rate: 2e-5
- Scheduler: cosine with warmup
- Max sequence length: 4096
- Precision: bf16

**DPO Training:**
- Starting checkpoint: SFT output
- Epochs: 1
- Batch size: 2 (gradient accumulation: 8, effective: 16)
- Learning rate: 5e-7
- Beta: 0.1

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
