# Evaluation Results

This document tracks evaluation metrics across model versions.

---

## Success Criteria

| Dimension | Metric | Target | Blocking? |
|-----------|--------|--------|-----------|
| Style | Blind A/B win rate | >70% | No |
| Factual | Q&A accuracy | >90% | Yes |
| Reviews | Issue detection rate | >85% | Yes |
| Reviews | Severity calibration | >90% | Yes |
| Port knowledge | Per-port accuracy | >90% all ports | Yes |
| Architecture | Deep question accuracy | >80% | No |

---

## Evaluation Datasets

| Dataset | Status | Examples |
|---------|--------|----------|
| held_out_reviews.jsonl | Complete (v2) | 551 |
| factual_qa.jsonl | Pending | Target: 300-500 |
| port_knowledge.jsonl | Pending | Target: 220+ |
| style_benchmark.jsonl | Pending | Target: 200 |

---

## Results

### Baseline: Qwen2.5-Coder-7B-Instruct (unmodified)

*To be recorded before training.*

### v1 Fine-Tuned: Qwen2.5-Coder-7B (QLoRA, v1 data)

Benchmarked 2026-02-09. Trained on v1 data (23,679 SFT examples including issue_comments).

**Review Quality (Claude-judged, 1-5 scale):**
| Model | Score |
|-------|-------|
| Fine-tuned Qwen2.5-Coder-7B (v1 data) | 1.79-2.02 |
| Claude + dpgeorge RAG | 2.63-3.59 |

**Failure Modes Identified:**
- Fabricated responses not engaging with actual diff content
- PR descriptions written from the author's perspective (role confusion)
- Non-specific feedback without code suggestions

**Root Cause:** Training data included 9,518 issue_comments (no diff context) and 2,189+1,583 merge/praise comments treated as review examples. See LESSONS_LEARNED.md.

**Status:** v2 training data pipeline created (2026-02-10) to address these issues. Retraining pending.

### After SFT

*To be recorded after SFT training.*

### After DPO

*To be recorded after DPO alignment.*

---

## Template for Recording Results

```
### Model: [Name/Version]

**Held-out Reviews:**
- Avg word count: [X] (reference: [Y])
- Word ratio: [X]
- Sentence count: [X]

**Factual Q&A:**
- Accuracy: [X]%
- Correct: [N]/[M]

**Port Knowledge:**
- Overall accuracy: [X]%
- Per-port breakdown:
  - stm32: [X]%
  - esp32: [X]%
  - rp2: [X]%
  - ...

**Notes:**
- [Observations, failure modes, areas for improvement]
```
