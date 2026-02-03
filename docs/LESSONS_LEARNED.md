# Lessons Learned

This document captures insights, challenges, and recommendations from the fine-tuning process.

---

## Data Preparation

### What Worked

1. **Review database from dpgeorge-review-db** - Having 18,614 categorized reviews from a single expert reviewer provided high-quality, consistent training data.

2. **Wiki scraping** - GitHub wiki provided practical, community-tested content that complements the technical review data.

3. **DPO from severity rankings** - Using severity (blocking > suggestion > nitpick) as an implicit preference signal was a clean way to generate DPO pairs.

### Challenges

*To be filled during execution.*

### Recommendations

*To be filled after completion.*

---

## Training

### What Worked

*To be filled after training.*

### Challenges

*To be filled during execution.*

### Recommendations

*To be filled after completion.*

---

## Evaluation

### What Worked

*To be filled after evaluation.*

### Challenges

*To be filled during execution.*

### Recommendations

*To be filled after completion.*

---

## Key Decisions

### Base Model Selection: Qwen3-Coder-8B-Instruct

**Decision:** Use dense 8B model instead of MoE

**Rationale:**
- All parameters active = consistent behavior across domains
- Simpler fine-tuning (no router instability)
- Fits in 48GB VRAM for full fine-tuning
- Good code understanding from base training

### Dataset Weighting Strategy

**Decision:** Oversample codebase Q&A (1.5x), wiki (1.2x)

**Rationale:**
- Reviews are the bulk of data but primarily teach style
- Codebase knowledge needs emphasis for accuracy
- Wiki provides practical guidance often missing from reviews

### Evaluation-First Approach

**Decision:** Create evaluation benchmarks before training

**Rationale:**
- Defines success criteria upfront
- Enables baseline comparison
- Catches issues early

---

## Retrospective Notes

*To be completed at project end.*
