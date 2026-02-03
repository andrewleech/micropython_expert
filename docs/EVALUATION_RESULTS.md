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
| held_out_reviews.jsonl | Complete | 1,861 |
| factual_qa.jsonl | Pending | Target: 300-500 |
| port_knowledge.jsonl | Pending | Target: 220+ |
| style_benchmark.jsonl | Pending | Target: 200 |

---

## Results

### Baseline: Qwen3-Coder-8B-Instruct (unmodified)

*To be recorded before training.*

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
