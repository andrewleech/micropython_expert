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
