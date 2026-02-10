# MicroPython Expert - Development Journal

Running log of the fine-tuning project from start to finish.

---

## 2026-02-03: Project Initialization

### Work Done
- Created project directory structure at `/home/anl/mpy/micropython-expert/`
- Copied `dpgeorge_reviews.db` from dpgeorge-review-db (28MB, 18,614 categorized reviews)
- Copied `schema.sql` for reference
- Created `pyproject.toml` with dependencies for training pipeline
- Created `requirements.txt` for remote deployment
- Created `CLAUDE.md` with project context
- Created `docs/PLAN.md` with full implementation plan
- Initialized this journal

### Directory Structure Created
```
micropython-expert/
├── data/
│   ├── raw/dpgeorge_reviews.db    # ✓ Copied
│   ├── wiki/                      # Empty - to be populated
│   ├── codebase/                  # Empty - to be populated
│   ├── training/                  # Empty - to be generated
│   └── eval/                      # Empty - to be generated
├── scripts/                       # Empty - to be created
├── training/                      # Empty - to be created
├── models/                        # Empty - training output
├── inference/                     # Empty - to be created
├── reference/schema.sql           # ✓ Copied
├── docs/
│   ├── PLAN.md                    # ✓ Created
│   └── JOURNAL.md                 # ✓ This file
├── logs/                          # Empty - for script logs
├── pyproject.toml                 # ✓ Created
├── requirements.txt               # ✓ Created
└── CLAUDE.md                      # ✓ Created
```

### Next Steps
1. Create `scripts/export_sft_dataset.py` - convert reviews to SFT format
2. Create `scripts/scrape_wiki.py` - download GitHub wiki pages
3. Reserve 10% of reviews for held-out evaluation set
4. Generate evaluation benchmarks

### Notes
- Base model: Qwen3-Coder-8B-Instruct (dense, 256K context)
- Training hardware: RTX 8000 (48GB VRAM) - access pending
- Target dataset: ~40,000 examples combined

---

## 2026-02-03: Data Preparation (continued)

### Work Done
- Created and ran `scripts/export_sft_dataset.py`
  - Exported 16,753 training examples, 1,861 held-out eval examples
  - Output: `data/training/reviews_sft.jsonl` (41MB)
  - Output: `data/eval/held_out_reviews.jsonl` (4.5MB)

- Created and ran `scripts/scrape_wiki.py`
  - Scraped 80/82 wiki pages from GitHub
  - Extracted 403 Q&A sections
  - Output: `data/training/wiki_qa.jsonl` (574KB)
  - Saved raw markdown to `data/wiki/`

- Created and ran `scripts/export_dpo_dataset.py`
  - Generated 5,359 preference pairs
  - 4,931 severity-based pairs (blocking > suggestion > nitpick)
  - 428 style-based pairs (is_style_example preference)
  - Output: `data/training/dpo_preferences.jsonl` (10MB)

- Created training infrastructure:
  - `training/sft_config.yaml` - SFT hyperparameters
  - `training/dpo_config.yaml` - DPO hyperparameters
  - `training/train_sft.py` - SFT training script with resume
  - `training/train_dpo.py` - DPO training script
  - `training/evaluate.py` - Evaluation metrics

- Created data generation scripts (to be run):
  - `scripts/generate_codebase_qa.py` - generates Q&A from MicroPython source
  - `scripts/generate_app_dev_qa.py` - generates practical guidance Q&A
  - `scripts/generate_eval_benchmark.py` - generates evaluation benchmarks
  - `scripts/combine_datasets.py` - merges datasets with weighting

- Created `setup_remote.sh` for RTX 8000 deployment

- Created inference tooling:
  - `inference/cli.py` - CLI for chat, review, and single questions
  - Supports interactive chat, diff review, and PR review modes

- Created documentation:
  - `docs/DATA_PREPARATION.md` - Dataset format and generation details
  - `docs/TRAINING_LOG.md` - Training run tracking template
  - `docs/EVALUATION_RESULTS.md` - Benchmark results template
  - `docs/LESSONS_LEARNED.md` - Retrospective notes template

### Current Dataset Status
| Dataset | Status | Examples |
|---------|--------|----------|
| reviews_sft.jsonl | ✓ Complete | 16,753 |
| wiki_qa.jsonl | ✓ Complete | 403 |
| dpo_preferences.jsonl | ✓ Complete | 5,359 |
| codebase_qa.jsonl | Pending | Target: 10-20K |
| app_dev_qa.jsonl | Pending | Target: 3-5K |
| held_out_reviews.jsonl | ✓ Complete | 1,861 |
| factual_qa.jsonl | Pending | Target: 300-500 |
| port_knowledge.jsonl | Pending | Target: 220+ |

### Next Steps
1. Run `scripts/generate_codebase_qa.py` to generate codebase knowledge Q&A
2. Run `scripts/generate_app_dev_qa.py` to generate practical guidance Q&A
3. Run `scripts/generate_eval_benchmark.py --all` to create evaluation benchmarks
4. Run `scripts/combine_datasets.py` to merge all datasets
5. Test training scripts locally (dry run)
6. Prepare bundle for remote RTX 8000 deployment

### Notes
- Wiki scraping worked well - 403 usable Q&A sections extracted
- DPO dataset uses severity ranking as implicit preference signal
- Codebase Q&A generation will be the longest step (uses Claude CLI)

---

## 2026-02-04: Data Generation Complete

### Work Done

**Git Repository Setup:**
- Initialized git repository in `/home/anl/mpy/micropython-expert/`
- Added MicroPython as a submodule pinned to v1.27.0
- Updated scripts to use relative path (`./micropython/`) instead of hardcoded path

**Script Fixes:**
- Fixed Claude CLI invocation (removed unsupported `--max-tokens` flag)
- Added `--model haiku` for cost efficiency
- Added unbuffered stdout for real-time log output
- Fixed `generate_app_dev_qa.py` to handle malformed responses gracefully
- Fixed append mode when running with `--topic` filter

**Codebase Q&A Generation (~5 hours):**
- Processed 412 source files across 5 categories
- Generated 3,936 Q&A pairs (target was 10-20K, actual limited by file count)
- Category breakdown:
  - py_core: 407 pairs (37 files)
  - extmod: 294 pairs (27 files)
  - ports: 3,059 pairs (332 files)
  - build_system: 88 pairs (8 files)
  - docs_develop: 88 pairs (8 files)

**App Dev Q&A Generation (~1.5 hours):**
- Generated 539 Q&A pairs across 12 topics
- 24 malformed responses filtered out
- Topics: GPIO, I2C/SPI, UART, timers, memory, freezing, networking, asyncio, filesystem, debugging, power, peripherals

**Evaluation Benchmarks:**
- Generated 113 factual Q&A pairs from core source files
- Generated 95 port-specific Q&A pairs
- Extracted 200 style benchmark examples from review database

**Dataset Combination:**
- Combined all SFT datasets with weighting
- Final combined_sft.jsonl: 23,679 examples
- Weight distribution:
  - reviews_sft (1.0): 16,753 (70.8%)
  - codebase_qa (1.5): 5,904 (24.9%)
  - wiki_qa (1.2): 483 (2.0%)
  - app_dev_qa (1.0): 539 (2.3%)

**Documentation:**
- Updated CLAUDE.md with current status
- Updated DATA_PREPARATION.md with final counts
- Created REMOTE_DEPLOYMENT.md with detailed training guide

### Final Dataset Summary

| Dataset | Count | Size |
|---------|-------|------|
| combined_sft.jsonl | 23,679 | 57MB |
| dpo_preferences.jsonl | 5,359 | 10MB |
| held_out_reviews.jsonl | 1,861 | 4.4MB |
| factual_qa.jsonl | 113 | 44KB |
| port_knowledge.jsonl | 95 | 35KB |
| style_benchmark.jsonl | 200 | 300KB |

### Git Commits
1. `13b8404` - Initial commit with data preparation pipeline
2. `e9c7b86` - scripts: Fix Claude CLI invocation for data generation
3. `e387bb4` - scripts: Add unbuffered output to app_dev and eval scripts
4. `453b511` - scripts: Fix app_dev_qa.py to append when filtering by topic

### Lessons Learned

1. **Target counts were optimistic:** Original targets of 10-20K codebase Q&A were based on generating many more pairs per file. Actual generation yielded ~11 pairs per file (5 explanation + 3 howto + 3 debugging).

2. **Claude CLI syntax differs from API:** No `--max-tokens` flag; use `--model` to select model.

3. **Timeout handling important:** Some Claude calls timed out (180s limit). Scripts continue gracefully.

4. **Checkpoint-based resume works well:** Codebase Q&A script successfully resumed from checkpoints when interrupted.

5. **Malformed responses happen:** ~4% of app_dev responses had parsing issues. Filtering is necessary.

### Next Steps
1. Transfer bundle to remote RTX 8000 server
2. Run setup_remote.sh to prepare environment
3. Start SFT training (~8-12 hours)
4. Run DPO alignment (~1-2 hours)
5. Evaluate model against benchmarks
6. Create quantized versions for deployment

### Status
**Phase: Data preparation COMPLETE - Ready for training**

---

## 2026-02-04: Remote Deployment & Model Selection

### Deployment to piai Server

Transferred project to remote RTX 8000 server:
```bash
rsync -avz --progress \
  --exclude 'venv/' --exclude '.git/' --exclude 'micropython/' \
  --exclude '__pycache__/' --exclude '*.pyc' --exclude 'logs/*.log' \
  --exclude 'models/' \
  /home/anl/mpy/micropython-expert/ piai:micropython-expert/
```

- Transfer successful: 142MB (26.9MB compressed)
- Training data verified: 50,669 total lines across 6 JSONL files
- Environment setup: venv created, dependencies installed
- flash-attn installed (required CUDA toolkit installation)
- HuggingFace authentication configured

### Model Investigation

Original plan specified `Qwen/Qwen3-Coder-8B-Instruct` but this model doesn't exist.

**Models evaluated:**

| Model | Params | Architecture | Strengths |
|-------|--------|--------------|-----------|
| Qwen2.5-Coder-7B-Instruct | 7B dense | Dense | HumanEval 88.4%, proven fine-tuning |
| Qwen3-Coder-Next | 80B/3B active | MoE (512 experts) | SWE-Bench 70.6%, agent-focused |
| Qwen3-8B | 8B dense | Dense | General purpose, not code-specific |
| Qwen3-Coder-30B-A3B-Instruct | 30B/3B active | MoE | Code-specific MoE |

**Benchmark comparison:**

*Qwen2.5-Coder-7B-Instruct:*
- HumanEval: 88.4% (outperforms DS-Coder-33B)
- Dense architecture, well-documented fine-tuning process
- 128K context

*Qwen3-Coder-Next:*
- SWE-Bench Verified: 70.6% (beats DeepSeek-V3.2 at 671B params)
- SWE-Bench Pro: 44.3%
- Aider: 66.2%
- 256K context, designed for coding agents
- MoE architecture complicates fine-tuning

**Decision:** Start with Qwen2.5-Coder-7B-Instruct for straightforward first trial. Plan to fine-tune Qwen3-Coder-Next as a follow-up experiment for comparison.

### Training Plan

**Phase 1: Qwen2.5-Coder-7B-Instruct (current)**
1. SFT training (~8-12 hours)
2. DPO alignment (~1-2 hours)
3. Evaluation against benchmarks

**Phase 2: Qwen3-Coder-Next (future)**
- Requires MoE-aware fine-tuning approach
- May need adjusted hyperparameters for sparse architecture
- Compare results with Phase 1 model

### Evaluation Plan

Once training completes, evaluate by:
1. **PR Review Quality:** Review a range of open MicroPython PRs
2. **MicroPython Knowledge Q&A:** Answer domain-specific questions
3. **Comparison Matrix:**
   - Fine-tuned Qwen2.5-Coder-7B
   - Fine-tuned Qwen3-Coder-Next (when complete)
   - Claude Opus (baseline)
   - Claude Sonnet (baseline)
   - Claude Opus + dpgeorge review RAG
   - Claude Sonnet + dpgeorge review RAG

This will quantify the value of fine-tuning vs RAG augmentation.

### Next Steps
1. ~~Update config to use Qwen2.5-Coder-7B-Instruct~~ ✓
2. ~~Start SFT training in tmux session~~ ✓
3. Monitor training progress (ongoing)

---

## 2026-02-04: Training Started (Late Evening)

### Configuration Issues Resolved

Multiple issues encountered during training startup:

1. **TRL API change**: `max_seq_length` → `max_length` in SFTConfig
2. **TF32 not supported**: RTX 8000 is Turing (not Ampere+), disabled TF32
3. **Flash Attention not supported**: Turing doesn't support FA2, switched to SDPA
4. **Multi-GPU interference**: System has RTX 8000 (46GB) + Quadro K1200 (4GB), set `CUDA_VISIBLE_DEVICES=0`
5. **Docker container conflict**: `qwen-text-to-image` container was using 27GB, stopped it
6. **Memory constraints**: Full fine-tuning requires ~56GB (model + gradients + optimizer states), switched to QLoRA

### Final Working Configuration

```yaml
model_name: Qwen/Qwen2.5-Coder-7B-Instruct
use_qlora: true
lora_r: 64
lora_alpha: 128
per_device_train_batch_size: 4
gradient_accumulation_steps: 8
max_seq_length: 2048
optim: adamw_8bit
```

QLoRA uses:
- 4-bit quantized base model (~4GB instead of 14GB)
- LoRA adapters (r=64, ~100M trainable params)
- 8-bit Adam optimizer

Memory usage: ~30GB of 46GB available

### Training Progress

- Started: 2026-02-04 23:15
- Total steps: 2220 (3 epochs × 740 steps)
- Current speed: ~157 seconds/step
- Estimated total time: ~97 hours
- GPU utilization: 100%

Note: Speed is limited by:
- No Flash Attention (Turing architecture)
- SDPA fallback is slower
- 4-bit quantization has dequantization overhead

### Trainable Parameters

Using QLoRA with r=64 targeting all linear layers:
- q_proj, k_proj, v_proj, o_proj (attention)
- gate_proj, up_proj, down_proj (MLP)

### Status
**Phase: SFT Training IN PROGRESS**

---

## 2026-02-05: Inference Planning & Conversion Scripts

### Training Progress Update

After 8 hours of monitoring:
- Step 177/2220 (8% complete)
- Speed: ~138-150 sec/step
- ETA: ~95 hours remaining (~4 days total)
- Training stable, no errors

### Local Inference Resource Analysis

Target deployment machine: Windows laptop with AMD Radeon 860M (8GB dedicated VRAM + 28GB shared).

**Memory requirements for Qwen2.5-Coder-7B:**

| Quantization | VRAM/RAM | Quality | Speed |
|--------------|----------|---------|-------|
| bf16/fp16 | ~14GB | 100% | Fast |
| 8-bit | ~8GB | ~99% | Good |
| 4-bit GGUF | ~4-5GB | ~97% | Good |
| Q4_K_M | ~4.5GB | ~95-97% | 15-30 tok/s |

**Recommendation:** Q4_K_M or Q5_K_M GGUF format
- Fits comfortably in 8GB dedicated VRAM
- Minimal quality loss for code review tasks
- Good inference speed

### AMD GPU Inference Strategy

AMD GPUs don't support ROCm in WSL2, so Windows-native inference is required:

1. **Ollama for Windows** - Easiest, good AMD support via ROCm/Vulkan
2. **LM Studio** - Nice GUI, Vulkan backend
3. **koboldcpp** - OpenAI-compatible API

Architecture:
```
Windows: Ollama/LM Studio (GPU) → localhost:11434
    ↑
WSL2: Scripts/Claude Code → HTTP API calls
```

### Post-Training Conversion Pipeline

Scripts created:
- `scripts/merge_lora.py` - Merge LoRA adapters into base model
- `scripts/convert_to_gguf.py` - Convert to GGUF format with multiple quantizations
- `scripts/create_ollama_model.py` - Generate Ollama Modelfile and import

Quantization targets:
- Q8_0: Highest quality (~8GB)
- Q5_K_M: Balanced (~5.5GB)
- Q4_K_M: Recommended for 8GB VRAM (~4.5GB)

---

## 2026-02-10: Training Data Pipeline Refinement

### Motivation

Benchmark results (2026-02-09) showed the fine-tuned Qwen2.5-Coder-7B scored 1.79-2.02/5 on review quality vs 2.63-3.59 for Claude baselines. Judge characterized outputs as "fabricated responses that don't engage with the actual diff" and "PR descriptions written from the author's perspective."

Root cause analysis of the v1 training data:
- 61% of SFT examples were issue_comments (no diff context, includes merge acks, CI reports, general discussion)
- 2,189 merge + 1,583 praise + 5,869 information comments were trained as "reviews"
- Only 5,199 review_comments were substantive (feedback_type in suggestion/requirement/question)
- Random 10% eval split caused data leakage — comments from the same PR appeared in both train and eval
- DPO `export_dpo_dataset.py` hardcoded `<|system|>...<|end|>` tokens (wrong for Qwen's chat template)

### Changes Made

**Rewrote `export_sft_dataset.py`:**
- Filtered to substantive review_comments only: feedback_type in (suggestion, requirement, question), diff_hunk IS NOT NULL, in_reply_to_id IS NULL
- Dropped all issue_comments and reviews tables
- Added quality-weighted oversampling: has_code_suggestion (1.5x), is_pattern (1.2x), is_style_example (1.3x), weights stack multiplicatively
- Changed from random eval split to PR-based split: entire PRs assigned to train or eval (10% of PRs)
- Output: 7,532 train + 551 eval from 4,537 substantive comments

**New `export_pr_reviews.py`:**
- Aggregates PRs with 3+ substantive review_comments into single multi-comment training examples
- Teaches the model structured multi-issue reviews rather than isolated comments
- Output: 501 examples from 543 qualifying PRs (42 skipped as >30k chars)

**Rewrote `export_dpo_dataset.py`:**
- Replaced hardcoded `<|system|>...<|end|>` prompt format with messages-based list for TRL DPOTrainer
- 4 pair types targeting identified failure modes:
  - Role confusion (2,000): substantive review vs merge/praise/information
  - Specificity (1,500): comments with code suggestions vs without
  - Conciseness (synthetic via Claude CLI, optional): terse rewrites of verbose originals
  - Severity (1,198): blocking > suggestion > nitpick preference ordering
- Output (without conciseness): 4,698 pairs

**New `generate_synthetic_reviews.py`:**
- Generates (diff → review) training pairs via `claude -p` (Claude Code CLI, no API key needed)
- Selects PRs by diff complexity, builds prompts with dpgeorge style guide + 3 few-shot examples
- Checkpoint/resume support
- Not yet executed (~30min runtime)

**Updated `combine_datasets.py`:**
- Updated weights: reviews_sft (1.0), pr_reviews (2.0), synthetic_reviews (2.5), wiki_qa (1.2), codebase_qa (1.5), app_dev_qa (1.0)
- Current output: 15,460 combined examples (synthetic_reviews pending)

**New `validate_training_data.py`:**
- 8 automated quality checks run before training:
  1. No role confusion in assistant responses
  2. All SFT examples have diff context
  3. No train/eval PR leakage
  4. No raw special tokens in DPO prompts
  5. Response length sanity (3-5000 chars)
  6. Balanced domains (<40% each)
  7. No accidental duplicate source comments
  8. Correct message format [system, user, assistant]
- All 8 checks passing

### Validation Fixes During Development

Initial validation run exposed 4 issues that required fixes:
- Role confusion false positive: "Thanks for fixing this, but..." flagged as role confusion. Fixed regex to match standalone phrases only.
- Old DPO file had `<|system|>...<|end|>` tokens. Regenerated with new script.
- 67 terse dpgeorge reviews under 10 chars (e.g., "uint32_t?", "(void)", "`void`"). Lowered threshold to 3 chars.
- 3,620 apparent duplicates were intentional oversampling copies. Changed dedup check to verify comment_id consistency instead.

### Dataset Comparison: v1 vs v2

| Metric | v1 (2026-02-04) | v2 (2026-02-10) |
|--------|-----------------|-----------------|
| SFT review examples | 16,753 (mixed) | 7,532 (substantive only) |
| Issue comments included | 9,518 | 0 |
| Review verdicts included | 393 | 0 |
| PR-based eval split | No (random) | Yes (133 eval PRs) |
| Quality oversampling | No | Yes (weighted by code suggestion, pattern, style) |
| PR review aggregation | No | 501 multi-comment reviews |
| DPO pair types | 2 (severity, style) | 4 (role confusion, specificity, conciseness, severity) |
| DPO prompt format | Hardcoded tokens | Messages-based (model-agnostic) |
| Validation checks | None | 8 automated checks |
| Combined SFT total | 23,679 | 16,710 |

### Notes
- `claude -p` (Claude Code CLI) uses existing Claude Code authentication — no separate API key needed
- Synthetic reviews: 500/500 generated, 0 failures, ~80 min runtime (Claude Haiku)
- DPO conciseness: 276/276 generated, 0 failures, ~28 min runtime (Claude Haiku)
- Final totals: 16,710 SFT examples + 4,974 DPO pairs, 8/8 validation checks passing

### Status
**Phase: Training data v2 COMPLETE — ready for retraining**

---
