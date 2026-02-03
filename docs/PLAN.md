# Fine-Tuned MicroPython Expert Model

## Goal
Create a self-contained fine-tuned model (no RAG) that provides:
1. **Code review** in dpgeorge's style and standards
2. **Architectural guidance** for MicroPython core development
3. **Application development guidance** for end-users building on MicroPython
4. **Intimate knowledge** of the entire MicroPython codebase (all 22 ports)

## Project Setup

**New Project Location:** `/home/anl/mpy/micropython-expert/`

**Copy from dpgeorge-review-db:**
```
data/dpgeorge_reviews.db    → data/raw/dpgeorge_reviews.db  (28MB SQLite)
schema.sql                  → reference/schema.sql          (for documentation)
rag/config.py               → reference/                    (configuration patterns)
```

**The existing dpgeorge-review-db remains intact** - this is a fork/evolution, not a replacement. The RAG system continues to work independently.

## Hardware Available
- **Training**: RTX 8000 (48GB VRAM) on remote machine via SSH
  - Access scheduled - will be provided later
  - Training runs in tmux/screen for detachment
  - All resources must be self-contained and copied over
- **Deployment**: Multiple targets
  - Cloud/hosted (large model)
  - Local GPU (medium model)
  - AMD NPU (small quantized model)

## Training Data Sources

### 1. Real Review Data (18,614 examples)
From dpgeorge-review-db:
- 6,842 inline code reviews with diff context
- 11,379 PR discussion comments
- 13-field categorization (domain, severity, component, etc.)
- 74% marked as good style examples

### 2. GitHub Wiki (~80 pages)
https://github.com/micropython/micropython/wiki
- Getting started guides
- Board-specific documentation (STM32, ESP32, Teensy, Arduino)
- Build troubleshooting
- Performance optimization (Viper, floating-point)
- Advanced topics (porting guides, interrupt handling, driver APIs)
- Community-maintained practical guidance

### 3. MicroPython Codebase (grounded synthetic)
Generate Q&A and explanations directly from source - **ALL 22 ports**:
- **py/** core: Object model, GC, compiler, VM, bytecode
- **extmod/**: Hardware abstraction patterns
- **ports/**: ALL platform-specific implementations
  - stm32 (86K lines), esp32 (16K), rp2 (12K), unix (7K)
  - nrf, samd, renesas-ra, mimxrt, zephyr, webassembly, windows, etc.
- **docs/develop/**: Architectural documentation
- **CODECONVENTIONS.md**: Style and standards

### 4. Application Development Guidance (grounded synthetic)
Tutorials/explanations for practical MicroPython usage:
- Using machine module across ports
- Memory management best practices
- Freezing modules, native modules
- Debugging techniques
- Common pitfalls and solutions

## Base Model

### Selected: Qwen3-Coder-8B-Instruct (Dense)
- **Architecture**: Dense 8B parameters
- **Context**: 256K native
- **Strengths**: Latest agentic coding model, simpler fine-tuning than MoE
- **Source**: https://huggingface.co/Qwen/Qwen3-Coder-8B-Instruct

**Why dense over MoE for this use case:**
- All parameters active = consistent behavior across MicroPython domains
- Simpler fine-tuning dynamics (no router instability)
- No risk of expert specialization mismatch
- Easier to debug and understand model behavior
- Fits comfortably in 48GB VRAM for full fine-tuning

## Training Pipeline

### Phase 1: Data Preparation

**Step 1.1: Export Review SFT Dataset**
```
scripts/export_sft_dataset.py
```
Convert 18,614 reviews to instruction format with metadata context.

**Step 1.2: Scrape and Process GitHub Wiki**
```
scripts/scrape_wiki.py
```
Extract ~80 wiki pages, convert to Q&A pairs and tutorial format.

**Step 1.3: Generate Codebase Knowledge Dataset**
```
scripts/generate_codebase_qa.py
```
Target: 10,000-20,000 grounded Q&A pairs covering:
- Object system, GC, compiler, VM, bytecode
- QSTR interning, native code emitters
- ALL 22 ports with unique characteristics
- Build system across platforms

**Step 1.4: Generate Application Development Dataset**
```
scripts/generate_app_dev_qa.py
```
Target: 3,000-5,000 practical Q&A pairs.

**Step 1.5: Create DPO Preference Dataset**
```
scripts/export_dpo_dataset.py
```
~5,000-8,000 preference pairs from severity rankings.

### Phase 2: Optional Continued Pretraining
Curate full MicroPython codebase (~545K lines C) for deeper knowledge injection.

### Phase 3: Supervised Fine-Tuning on RTX 8000

**Training Configuration:**
```yaml
# training/sft_config.yaml
model_name: Qwen/Qwen3-Coder-8B-Instruct
output_dir: ./models/micropython-expert-8b

# Training params
num_train_epochs: 3
per_device_train_batch_size: 4
gradient_accumulation_steps: 8    # Effective batch: 32
learning_rate: 2e-5
lr_scheduler_type: cosine
warmup_ratio: 0.1

# Memory optimization
gradient_checkpointing: true
bf16: true

# Checkpointing (for resume capability)
save_strategy: steps
save_steps: 500
save_total_limit: 3
resume_from_checkpoint: true      # Auto-resume from latest
```

**Combined Dataset (~40,000 examples):**
1. Review generation (18,614) - weight: 1.0
2. Wiki content (2,000-3,000) - weight: 1.2
3. Codebase knowledge (10,000-20,000) - weight: 1.5
4. Application guidance (3,000-5,000) - weight: 1.0

**Time Estimate:**
- SFT (3 epochs): ~8-12 hours
- Can run overnight, resume if interrupted

### Phase 4: DPO Alignment

**Time Estimate:** ~1-2 hours on RTX 8000

After SFT, align preferences:
```yaml
# training/dpo_config.yaml
model_name: ./models/micropython-expert-8b
beta: 0.1
num_train_epochs: 1
```

### Phase 5: Model Variants
- **Primary**: Qwen3-Coder-8B fine-tuned (full precision, 16GB)
- **Medium**: 4-bit quantized (GPTQ/AWQ, ~4GB)
- **Small**: GGUF Q4_K_M for llama.cpp / NPU (~3GB)

**Resume Capability:**
Training can be stopped (Ctrl+C, system restart) and resumed:
```bash
# Auto-resume from latest checkpoint
python training/train_sft.py

# Or specify checkpoint
python training/train_sft.py --resume_from_checkpoint ./models/micropython-expert-8b/checkpoint-1500
```

Checkpoints save: model weights, optimizer state, scheduler state, step counter, RNG states.

## Remote Training Setup

**Workflow:**
1. Prepare everything locally (data, scripts, configs)
2. Package as self-contained bundle
3. Copy to remote RTX 8000 machine via SSH
4. Run training in tmux (detachable)
5. Monitor progress remotely
6. Copy results back

**Files to Copy to Remote:**
```
micropython-expert/
├── data/training/*.jsonl        # Training datasets (~500MB-1GB)
├── data/eval/*.jsonl            # Evaluation benchmarks
├── training/                    # Training scripts and configs
├── scripts/                     # Utility scripts
├── requirements.txt             # Python dependencies
└── setup_remote.sh              # One-command setup script
```

**NOT copied (downloaded on remote):**
- Base model (~16GB) - faster to download from HuggingFace
- Large dependencies - installed via pip

**Remote Setup Script (setup_remote.sh):**
```bash
#!/bin/bash
# Run once on remote machine

# Create venv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Pre-download model (can run in background)
python -c "from transformers import AutoModelForCausalLM; AutoModelForCausalLM.from_pretrained('Qwen/Qwen3-Coder-8B-Instruct')"
```

**Training Launch (in tmux):**
```bash
ssh remote-machine
tmux new -s training
cd micropython-expert
source venv/bin/activate
python training/train_sft.py 2>&1 | tee logs/training_$(date +%Y%m%d_%H%M%S).log

# Detach: Ctrl+B, D
# Reattach: tmux attach -t training
```

**Monitoring Options:**
```bash
# Watch training progress
tail -f logs/training_*.log

# Check GPU usage
watch -n 1 nvidia-smi

# View tensorboard (forward port)
ssh -L 6006:localhost:6006 remote-machine
tensorboard --logdir ./models/micropython-expert-8b/runs
```

**Copy Results Back:**
```bash
# After training completes
rsync -avz --progress remote-machine:micropython-expert/models/ ./models/
rsync -avz --progress remote-machine:micropython-expert/logs/ ./logs/
```

## Project Structure

```
/home/anl/mpy/micropython-expert/
├── data/
│   ├── raw/
│   │   └── dpgeorge_reviews.db      # Copied from dpgeorge-review-db
│   ├── wiki/
│   │   └── *.md                     # Scraped GitHub wiki pages
│   ├── codebase/
│   │   └── curated_source.txt       # Curated MicroPython source for pretraining
│   ├── training/
│   │   ├── reviews_sft.jsonl        # Review instruction pairs
│   │   ├── wiki_qa.jsonl            # Wiki-derived Q&A
│   │   ├── codebase_qa.jsonl        # Architecture Q&A
│   │   ├── app_dev_qa.jsonl         # Application guidance
│   │   ├── combined_sft.jsonl       # Merged SFT dataset
│   │   └── dpo_preferences.jsonl    # Preference pairs
│   └── eval/
│       ├── factual_qa.jsonl         # Verifiable Q&A benchmark
│       ├── held_out_reviews.jsonl   # 10% reserved reviews
│       ├── port_knowledge.jsonl     # Port-specific Q&A
│       └── style_benchmark.jsonl    # Style comparison pairs
├── scripts/
│   ├── export_sft_dataset.py        # Convert reviews to SFT format
│   ├── scrape_wiki.py               # Download GitHub wiki
│   ├── generate_codebase_qa.py      # Generate architecture Q&A
│   ├── generate_app_dev_qa.py       # Generate practical guidance
│   ├── generate_eval_benchmark.py   # Create evaluation datasets
│   ├── export_dpo_dataset.py        # Create preference pairs
│   ├── prepare_pretrain_corpus.py   # Curate codebase for pretraining
│   └── convert_to_gguf.py           # Model quantization
├── training/
│   ├── sft_config.yaml              # SFT hyperparameters
│   ├── dpo_config.yaml              # DPO hyperparameters
│   ├── train_sft.py                 # SFT training script
│   ├── train_dpo.py                 # DPO training script
│   └── evaluate.py                  # Evaluation metrics
├── models/                          # Trained model outputs
│   ├── micropython-expert-8b/       # Primary: Qwen3-Coder-8B fine-tuned
│   ├── micropython-expert-8b-4bit/  # GPTQ/AWQ quantized
│   └── micropython-expert-gguf/     # GGUF for llama.cpp / NPU
├── inference/
│   ├── serve.py                     # API server
│   └── cli.py                       # Local CLI interface
├── reference/
│   └── schema.sql                   # Copied from dpgeorge-review-db
├── docs/
│   ├── PLAN.md                      # This plan document
│   ├── JOURNAL.md                   # Running log of process
│   ├── DATA_PREPARATION.md          # Dataset creation details
│   ├── TRAINING_LOG.md              # Training runs and metrics
│   ├── EVALUATION_RESULTS.md        # Benchmark results
│   └── LESSONS_LEARNED.md           # Retrospective notes
├── pyproject.toml
├── requirements.txt
└── CLAUDE.md
```

---

## Evaluation Strategy (Detailed)

Evaluation is critical for fine-tuned models because unlike RAG, you can't easily debug or fix errors post-training. We need multiple complementary approaches.

### Dimension 1: Style Fidelity
**Question**: Does the model write like dpgeorge?

**Automatic Metrics:**
- **Vocabulary overlap**: Calculate Jaccard similarity of n-grams between generated and real reviews
- **Sentence length distribution**: dpgeorge tends toward concise, direct feedback
- **Sentiment analysis**: Reviews should be technical, not effusive or harsh
- **Formatting patterns**: Use of backticks, line references, code suggestions

**Human Evaluation:**
- Blind A/B test: Show pairs of reviews (model vs dpgeorge), ask "which sounds more like dpgeorge?"
- Target: >70% indistinguishable in blind tests

**Red-team tests:**
- Ask model to be encouraging/verbose → should resist and stay terse
- Ask for praise → should give measured, technical acknowledgment

### Dimension 2: Technical Accuracy
**Question**: Are the facts correct?

**Automatic Metrics:**
- **Factual recall**: Create Q&A test set with verifiable answers
  - "What file contains the garbage collector?" → "py/gc.c"
  - "What macro is used for memory allocation?" → "m_new"
- **Code reference accuracy**: When model cites a function/file, verify it exists
- **Consistency**: Same question asked multiple ways should give same answer

**Benchmark Dataset (create manually):**
- 200-500 factual questions about MicroPython internals
- Ground truth answers derived from source code
- Categories: object model, GC, compiler, ports, build system

**Human Evaluation:**
- MicroPython contributors verify random sample of generated content
- Flag factual errors, grade severity (minor/major/critical)

### Dimension 3: Review Quality
**Question**: Would this feedback improve the code?

**Held-out Test Set:**
- Reserve 10% of reviews (~1,800) as test set
- Generate model reviews for same diffs
- Compare: Does model identify same issues? Different issues? Miss issues?

**Metrics:**
- **Issue detection rate**: % of issues dpgeorge flagged that model also flags
- **False positive rate**: Issues model raises that dpgeorge didn't (may be good or bad)
- **Severity calibration**: Does model correctly distinguish blocking vs nitpick?

**Gold Standard Evaluation:**
- Take 50 recent PRs not in training set
- Generate reviews with model
- Have dpgeorge (or trusted contributors) rate quality 1-5
- Track: Actionability, correctness, completeness

### Dimension 4: Codebase Knowledge Depth
**Question**: Does the model know the entire codebase?

**Port Coverage Test:**
- Create 10 questions per port (22 ports × 10 = 220 questions)
- Test unique aspects: "How does ESP32 handle WiFi?" vs "How does STM32 handle USB?"
- Measure accuracy per port

**Architecture Questions:**
- Deep questions about internals that require understanding multiple files
- "Trace the execution path from Python import to loaded module"
- "Explain how native code generation differs between ARM and Xtensa"

**Regression Detection:**
- After training, test if basic knowledge was forgotten
- "What is MicroPython?" should still work

### Dimension 5: Helpfulness
**Question**: Is the guidance actionable?

**User Simulation:**
- Create scenarios: "I want to add a new board to the STM32 port"
- Rate: Does model give step-by-step guidance? Are steps correct? Complete?

**Task Completion:**
- Give model a task description, have it generate implementation guidance
- Attempt to follow guidance → does it work?

### Evaluation Dataset Creation

**Approach**: Generate benchmarks using Claude against source code and existing review database.

The review database is a goldmine: dpgeorge has already explained many internals in his 18,614 comments. Extract these as ground truth:
```python
# Example: Extract factual statements from reviews
"The QSTR pool is initialized in mp_init()" → Q: Where is QSTR pool initialized? A: mp_init()
"Use m_new_obj() for allocating objects" → Q: What macro allocates objects? A: m_new_obj()
```

**Generation Pipeline:**
```
scripts/generate_eval_benchmark.py
```
1. Parse review comments for factual statements about code
2. Generate questions that verify those facts
3. Cross-reference against actual source code for accuracy
4. Generate port-specific questions from port code
5. Generate architecture questions from docs/develop/

### Evaluation Dataset Structure

```
data/eval/
├── style_benchmark.jsonl          # Style comparison pairs
├── factual_qa.jsonl               # Verifiable Q&A (300-500)
├── held_out_reviews.jsonl         # 10% reserved reviews
├── port_knowledge.jsonl           # Port-specific Q&A (220+)
├── architecture_deep_dive.jsonl   # Complex multi-file questions
├── helpfulness_scenarios.jsonl    # Task-based evaluation
└── golden_reviews.jsonl           # Expert-rated review examples
```

### Evaluation Checkpoints

**During Training:**
- Monitor validation loss per data category
- Run factual_qa every N steps to catch knowledge degradation
- Track style metrics on held_out_reviews

**Post-Training:**
- Full evaluation suite before deployment
- Compare against baseline (untuned model)
- Compare against RAG system

**Ongoing:**
- Log production queries and responses
- Periodic human review of samples
- Track user feedback/corrections

### Success Criteria (High Bar - >90% Deployment Threshold)

| Dimension | Metric | Target | Blocking? |
|-----------|--------|--------|-----------|
| Style | Blind A/B win rate | >70% | No |
| Factual | Q&A accuracy | **>90%** | **Yes** |
| Reviews | Issue detection rate | >85% | Yes |
| Reviews | Severity calibration | >90% | Yes |
| Port knowledge | Per-port accuracy | >90% all ports | Yes |
| Architecture | Deep question accuracy | >80% | No |

**Deployment gate**: All "Blocking" metrics must pass before deployment. Style and architecture can improve iteratively.

### Failure Modes to Watch

1. **Hallucination**: Model confidently states wrong facts
   - Mitigation: Factual benchmark, citation verification

2. **Catastrophic forgetting**: Loses base model capabilities
   - Mitigation: Include general coding questions in eval

3. **Style collapse**: Becomes generic, loses dpgeorge voice
   - Mitigation: Style metrics throughout training

4. **Port bias**: Better at STM32 (most data) than others
   - Mitigation: Per-port evaluation, balanced sampling

5. **Verbosity drift**: Becomes more verbose than dpgeorge
   - Mitigation: Length distribution monitoring

---

## Implementation Order

### Phase A: Local Preparation (Now - before remote access)

1. **Create new project** at `/home/anl/mpy/micropython-expert/`
   - Initialize folder structure
   - Copy `dpgeorge_reviews.db` from dpgeorge-review-db
   - Set up pyproject.toml, requirements.txt
   - Copy this plan to `docs/PLAN.md`
   - Initialize `docs/JOURNAL.md` for ongoing documentation

2. **Create evaluation datasets first** (factual Q&A, held-out reviews)
   - Generate from source code + review database using Claude
   - Reserve 10% of reviews as held-out test set

3. **Export review SFT dataset** from existing database

4. **Scrape and process GitHub wiki** (~80 pages)

5. **Generate codebase Q&A** using Claude with real source code (10K-20K pairs)

6. **Generate app dev Q&A** for practical guidance (3K-5K pairs)

7. **Create DPO preferences** from severity rankings

8. **Prepare training scripts** and configuration files

9. **Create remote deployment bundle**
   - setup_remote.sh script
   - All data files packaged
   - Training scripts ready

### Phase B: Remote Training (When SSH access scheduled)

10. **Copy bundle to remote** via SSH/rsync

11. **Run setup_remote.sh** to prepare environment

12. **Baseline evaluation** (untuned model on eval sets)

13. **Train SFT model** in tmux (~8-12 hours)

14. **Run DPO alignment** (~1-2 hours)

15. **Full evaluation** against baseline - must pass >90% thresholds

16. **Copy results back** to local machine

### Phase C: Post-Training (Local)

17. **Create smaller variants** (quantized, GGUF for NPU)

18. **Build inference tooling** (API, CLI)

19. **Final documentation** and lessons learned

## Documentation Strategy

**Goal**: Document the entire process from start to finish as raw data for a blog/walkthrough later.

**Documentation files to maintain:**

```
/home/anl/mpy/micropython-expert/
├── docs/
│   ├── PLAN.md                      # This plan (copy of plan file)
│   ├── JOURNAL.md                   # Running log of what was done, decisions, issues
│   ├── DATA_PREPARATION.md          # Details of dataset creation process
│   ├── TRAINING_LOG.md              # Training runs, hyperparameters, metrics
│   ├── EVALUATION_RESULTS.md        # Benchmark results, comparisons
│   └── LESSONS_LEARNED.md           # What worked, what didn't, recommendations
```

**Journaling approach:**
- Timestamp each significant step
- Record decisions and rationale
- Document any issues encountered and how resolved
- Include commands run and their outputs
- Capture metrics at each stage

This raw documentation will serve as source material for a polished blog post.

## Open Items

- [ ] Determine if continued pretraining is needed based on initial SFT results
- [ ] Decide on AMD NPU deployment approach (GGUF format vs other)
