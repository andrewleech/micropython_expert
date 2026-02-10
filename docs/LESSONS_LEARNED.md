# Lessons Learned

This document captures insights, challenges, and recommendations from the fine-tuning process.

---

## Data Preparation

### What Worked

1. **Review database from dpgeorge-review-db** - Having 18,614 categorized reviews from a single expert reviewer provided high-quality, consistent training data.

2. **Wiki scraping** - GitHub wiki provided practical, community-tested content that complements the technical review data.

3. **Quality-weighted oversampling** - Weighting by `has_code_suggestion` (1.5x), `is_pattern` (1.2x), and `is_style_example` (1.3x) lets the dataset emphasize higher-signal examples without discarding others.

4. **PR-based train/eval split** - Individual comments from the same PR share context, so random splitting gives the model access to adjacent comments during training that appear in eval. PR-based splitting prevents this data leakage.

5. **Automated validation** - `validate_training_data.py` with 8 checks catches regressions before training. The first run exposed 4 issues that would have gone undetected otherwise.

### Challenges

1. **Issue comments polluted the SFT dataset.** The v1 pipeline included 9,518 issue_comments and 393 review verdicts alongside 6,842 review_comments. Issue comments lack diff context and include merge acknowledgements, CI reports, and general discussion -- none of which teach the model to review code. This was the primary cause of the model producing "fabricated responses that don't engage with the actual diff."

2. **Role confusion from feedback_type mixing.** 2,189 merge + 1,583 praise + 5,869 information comments were trained as "review" examples. The model learned that reviews include "Merged.", "LGTM", and "Thanks for the PR" -- the opposite of the intended behavior.

3. **DPO prompt format was model-specific.** The v1 `export_dpo_dataset.py` hardcoded `<|system|>...<|end|>` tokens in the prompt field. These are model-specific and wrong for Qwen's chat template. The correct approach is messages-based prompts that let TRL's DPOTrainer apply the model's chat template.

4. **Severity-only DPO pairs didn't address actual failure modes.** The v1 DPO pairs ranked by severity and style_example. The benchmark revealed the model's actual failures were role confusion, hallucination, and non-specificity -- none addressed by the existing pairs.

5. **Validation false positives.** Terse dpgeorge corrections like "uint32_t?", "(void)", "`void`" are under 10 chars but are legitimate reviews. "Thanks for fixing this, but the fix is in the wrong commit..." starts with "Thanks for" but is substantive feedback. Validation thresholds need to account for the reviewer's terse style.

### Recommendations

1. Always filter training data by comment_type AND feedback_type. Not all comments from a reviewer are reviews.
2. Every SFT example for code review must include diff context in the user prompt.
3. Use PR-based splits (not random) for any dataset derived from GitHub comments.
4. Design DPO pairs to target observed model failures, not theoretical preference orderings.
5. Run automated validation before every training run. The 8-check suite catches: role confusion, missing diff context, train/eval leakage, format errors, length outliers, domain imbalance, duplicates, and message format violations.
6. Test validation rules against known edge cases (terse corrections, "Thanks for... but..." patterns) to avoid false positives.

---

## Training

### What Worked

1. **QLoRA with r=64 on RTX 8000 (46GB)** - 4-bit quantized base model + LoRA adapters fit in memory.
2. **8-bit Adam optimizer** - Reduced memory without measurable quality loss.

### Challenges

1. **RTX 8000 (Turing) doesn't support Flash Attention 2 or TF32** - Had to use SDPA fallback, resulting in ~150 sec/step.
2. **Full fine-tuning (56GB required) exceeds 46GB VRAM** - QLoRA was the only option.
3. **TRL API changed:** `max_seq_length` to `max_length` in SFTConfig.
4. **Multi-GPU with mismatched cards** (RTX 8000 + Quadro K1200) required explicit `CUDA_VISIBLE_DEVICES=0`.

### Recommendations

1. For Turing-era GPUs, budget for ~4x longer training times vs Ampere/Hopper with Flash Attention.
2. Always pin TRL version in requirements.txt -- API changes break configs silently.
3. Training on the v2 dataset (substantive reviews only) should be re-run to validate the quality improvement.

---

## Evaluation

### What Worked

1. **Claude as a judge with structured rubrics** - Gave actionable feedback on model outputs.

### Challenges

1. The v1 model scored 1.79-2.02/5 on review quality -- below the Claude+RAG baseline (2.63-3.59).
2. Judge identified "fabricated responses that don't engage with the actual diff" and "PR descriptions written from the author's perspective" as primary failure modes.
3. These failures were traceable to training data quality, not model capacity or hyperparameters.

### Recommendations

1. Evaluate training data quality before investing in training runs. A quick spot-check of 20 random SFT examples would have revealed the issue_comment contamination.
2. Re-evaluate after training on v2 data to confirm the hypothesis that data quality was the bottleneck.
3. Compare fine-tuned model vs Claude+RAG baseline -- the RAG approach may remain competitive depending on v2 results.

---

## Key Decisions

### Base Model Selection: Qwen2.5-Coder-7B-Instruct

**Decision:** Use dense 7B model as first trial

**Rationale:**
- HumanEval 88.4%, proven fine-tuning ecosystem
- Dense architecture, simpler fine-tuning than MoE
- Fits in 46GB with QLoRA
- Follow-up with Qwen3-Coder-Next planned for comparison

### Dataset Weighting Strategy

**Decision:** Oversample pr_reviews (2.0x), synthetic_reviews (2.5x), codebase Q&A (1.5x), wiki (1.2x)

**Rationale:**
- PR reviews and synthetic reviews are highest-signal (direct diff-to-review pairs)
- Codebase knowledge needs emphasis for factual accuracy
- Wiki provides practical guidance missing from reviews
- reviews_sft at 1.0x is already the largest dataset

### Training Data v2: Quality Over Quantity

**Decision:** Reduce SFT from 23,679 to ~15,460 examples by removing low-quality data

**Rationale:**
- v1 benchmark showed the model learned to produce noise, not reviews
- 61% of training data (issue_comments) was actively harmful -- teaching wrong behavior
- Fewer but higher-quality examples should outperform more but noisy data
- Added DPO pairs specifically targeting the observed failure modes

### Evaluation-First Approach

**Decision:** Create evaluation benchmarks before training

**Rationale:**
- Defines success criteria upfront
- Enables baseline comparison
- Catches issues early

---

## Retrospective Notes

- The v1 training produced a model that scored below baselines, but the failure was in data preparation, not training infrastructure. The training scripts, QLoRA configuration, and inference pipeline all worked correctly.
- Time from benchmark results (Feb 9) to refined pipeline (Feb 10): 1 day. The rebuild was fast because the review database already had the categorization metadata needed for filtering -- the v1 pipeline just hadn't used it.
- Synthetic data generation via `claude -p` (Claude Code CLI) requires no API key setup -- it uses existing Claude Code authentication. This makes it practical for local development.
