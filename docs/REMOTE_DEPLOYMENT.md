# Remote Training Deployment Guide

Step-by-step guide for deploying and running training on a remote RTX 8000 server.

## Prerequisites

**Remote Machine Requirements:**
- NVIDIA RTX 8000 or equivalent with 48GB VRAM (minimum 24GB for reduced batch)
- CUDA 12.1+ installed
- 100GB+ free disk space
- Python 3.10+
- SSH access configured

**Local Machine:**
- All data preparation complete (see `DATA_PREPARATION.md`)
- rsync installed

## Phase 1: Prepare Transfer Bundle

### 1.1 Verify Local Data Completeness

```bash
cd /home/anl/mpy/micropython-expert

# Check all required files exist
echo "=== Training Data ===" && wc -l data/training/*.jsonl
echo "=== Eval Data ===" && wc -l data/eval/*.jsonl
echo "=== Configs ===" && ls -la training/*.yaml
```

Expected output:
```
=== Training Data ===
     539 data/training/app_dev_qa.jsonl
    3936 data/training/codebase_qa.jsonl
   23679 data/training/combined_sft.jsonl
    5359 data/training/dpo_preferences.jsonl
   16753 data/training/reviews_sft.jsonl
     403 data/training/wiki_qa.jsonl

=== Eval Data ===
    113 data/eval/factual_qa.jsonl
   1861 data/eval/held_out_reviews.jsonl
     95 data/eval/port_knowledge.jsonl
    200 data/eval/style_benchmark.jsonl
```

### 1.2 Calculate Transfer Size

```bash
du -sh data/training/ data/eval/ training/ scripts/
```

Expected: ~60-80MB total (excludes venv, git)

## Phase 2: Transfer to Remote

### 2.1 Initial Transfer

```bash
# Replace 'remote-host' with your actual SSH host
REMOTE_HOST="user@remote-host"
REMOTE_DIR="~/micropython-expert"

# Dry run first
rsync -avzn --progress \
  --exclude 'venv/' \
  --exclude '.git/' \
  --exclude 'micropython/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude 'logs/*.log' \
  --exclude 'models/' \
  /home/anl/mpy/micropython-expert/ \
  ${REMOTE_HOST}:${REMOTE_DIR}/

# Actual transfer (remove -n flag)
rsync -avz --progress \
  --exclude 'venv/' \
  --exclude '.git/' \
  --exclude 'micropython/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude 'logs/*.log' \
  --exclude 'models/' \
  /home/anl/mpy/micropython-expert/ \
  ${REMOTE_HOST}:${REMOTE_DIR}/
```

### 2.2 Verify Transfer

```bash
ssh ${REMOTE_HOST} "cd ${REMOTE_DIR} && wc -l data/training/*.jsonl"
```

## Phase 3: Remote Environment Setup

### 3.1 SSH to Remote

```bash
ssh ${REMOTE_HOST}
cd micropython-expert
```

### 3.2 Run Setup Script

```bash
chmod +x setup_remote.sh
./setup_remote.sh
```

This will:
1. Create Python virtual environment
2. Install PyTorch with CUDA 12.1 support
3. Install all dependencies from requirements.txt
4. Attempt to install flash-attention (optional, speeds up training)
5. Download Qwen3-Coder-8B-Instruct model (~16GB)

**Expected duration:** 15-30 minutes (mostly model download)

### 3.3 Verify GPU Access

```bash
source venv/bin/activate
python -c "
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'GPU: {torch.cuda.get_device_name(0)}')
print(f'VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')
"
```

Expected:
```
CUDA available: True
GPU: NVIDIA RTX 8000
VRAM: 48.0 GB
```

## Phase 4: Run Training

### 4.1 Start tmux Session

```bash
tmux new -s training
source venv/bin/activate
cd micropython-expert
```

### 4.2 Run SFT Training

```bash
# Create logs directory
mkdir -p logs

# Start SFT training with logging
python training/train_sft.py 2>&1 | tee logs/sft_$(date +%Y%m%d_%H%M%S).log
```

**Expected duration:** 8-12 hours for 3 epochs on 23,679 examples

**To detach from tmux:** `Ctrl+B`, then `D`
**To reattach:** `tmux attach -t training`

### 4.3 Monitor Training

In a separate terminal:
```bash
# Watch GPU utilization
watch -n 1 nvidia-smi

# Watch training loss (in another terminal)
tail -f logs/sft_*.log

# View tensorboard (optional)
tensorboard --logdir ./models/micropython-expert-8b/runs --port 6006
```

### 4.4 Resume from Checkpoint (if interrupted)

Training auto-resumes from latest checkpoint:
```bash
# Just run again - it finds the latest checkpoint automatically
python training/train_sft.py
```

Or specify a checkpoint:
```bash
python training/train_sft.py --resume_from_checkpoint ./models/micropython-expert-8b/checkpoint-1500
```

### 4.5 Run DPO Alignment (after SFT completes)

```bash
python training/train_dpo.py 2>&1 | tee logs/dpo_$(date +%Y%m%d_%H%M%S).log
```

**Expected duration:** 1-2 hours for 1 epoch on 5,359 preference pairs

## Phase 5: Evaluate Model

### 5.1 Run Evaluation Benchmarks

```bash
python training/evaluate.py \
  --model_path ./models/micropython-expert-8b \
  --eval_dir ./data/eval \
  --output_path ./docs/EVALUATION_RESULTS.md
```

### 5.2 Quick Smoke Test

```bash
python -c "
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model_path = './models/micropython-expert-8b'
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.bfloat16, device_map='auto')

messages = [
    {'role': 'system', 'content': 'You are an expert MicroPython code reviewer.'},
    {'role': 'user', 'content': 'What file contains the garbage collector implementation?'}
]

text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(text, return_tensors='pt').to(model.device)
outputs = model.generate(**inputs, max_new_tokens=100, do_sample=False)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
"
```

Expected answer should mention `py/gc.c`.

## Phase 6: Retrieve Results

### 6.1 Copy Model Back to Local

```bash
# From local machine
rsync -avz --progress \
  ${REMOTE_HOST}:${REMOTE_DIR}/models/ \
  /home/anl/mpy/micropython-expert/models/

rsync -avz --progress \
  ${REMOTE_HOST}:${REMOTE_DIR}/logs/ \
  /home/anl/mpy/micropython-expert/logs/

rsync -avz --progress \
  ${REMOTE_HOST}:${REMOTE_DIR}/docs/EVALUATION_RESULTS.md \
  /home/anl/mpy/micropython-expert/docs/
```

### 6.2 Model Sizes

Expected model sizes after training:
- Full model (bf16): ~16GB
- Checkpoints: ~16GB each (3 kept)

## Phase 7: Create Quantized Versions

### 7.1 GPTQ 4-bit (for deployment)

```bash
python scripts/convert_to_gptq.py \
  --input_path ./models/micropython-expert-8b \
  --output_path ./models/micropython-expert-8b-gptq
```

### 7.2 GGUF (for llama.cpp / NPU)

```bash
python scripts/convert_to_gguf.py \
  --input_path ./models/micropython-expert-8b \
  --output_path ./models/micropython-expert-gguf \
  --quantization Q4_K_M
```

## Troubleshooting

### Out of Memory (OOM)

If you get CUDA OOM errors:
1. Reduce batch size in `training/sft_config.yaml`:
   ```yaml
   per_device_train_batch_size: 2  # Was 4
   gradient_accumulation_steps: 16  # Was 8 (keeps effective batch = 32)
   ```
2. Enable gradient checkpointing (already enabled by default)
3. Reduce max sequence length if needed

### Training Stuck / No Progress

1. Check GPU is being used: `nvidia-smi`
2. Check for errors in log: `tail -100 logs/sft_*.log`
3. Try killing and resuming (checkpoints are saved every 500 steps)

### Model Download Fails

If HuggingFace download fails:
```bash
# Retry with explicit cache dir
HF_HOME=/path/to/large/disk/.cache/huggingface python -c "
from transformers import AutoModelForCausalLM
AutoModelForCausalLM.from_pretrained('Qwen/Qwen3-Coder-8B-Instruct')
"
```

### Flash Attention Install Fails

Flash attention is optional but speeds up training ~20-30%. If install fails:
1. Training will still work (uses standard attention)
2. To retry: `pip install flash-attn --no-build-isolation`
3. Requires matching CUDA version with PyTorch

## Configuration Reference

### Key Files

| File | Purpose |
|------|---------|
| `training/sft_config.yaml` | SFT hyperparameters |
| `training/dpo_config.yaml` | DPO hyperparameters |
| `training/train_sft.py` | SFT training script |
| `training/train_dpo.py` | DPO training script |
| `training/evaluate.py` | Evaluation script |
| `setup_remote.sh` | Remote environment setup |

### SFT Config Options

```yaml
# Reduce for lower VRAM
per_device_train_batch_size: 4   # Try 2 or 1 for OOM
gradient_accumulation_steps: 8   # Increase to maintain effective batch
max_seq_length: 4096             # Try 2048 for OOM

# Adjust training length
num_train_epochs: 3              # More epochs = more training time
save_steps: 500                  # Checkpoint frequency
eval_steps: 500                  # Evaluation frequency

# Resume options
resume_from_checkpoint: true     # Auto-resume from latest
```

## Timeline Summary

| Phase | Duration | Notes |
|-------|----------|-------|
| Transfer | 5-10 min | ~80MB data |
| Setup | 15-30 min | Mainly model download |
| SFT Training | 8-12 hours | 3 epochs, 23K examples |
| DPO Training | 1-2 hours | 1 epoch, 5K pairs |
| Evaluation | 30-60 min | All benchmarks |
| Retrieve | 10-20 min | ~50GB models |

**Total: ~12-16 hours** (mostly unattended)
