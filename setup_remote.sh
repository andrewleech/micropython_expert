#!/bin/bash
# Setup script for remote RTX 8000 training machine
# Run this once after copying the project bundle to the remote machine
#
# Usage: ./setup_remote.sh

set -e

echo "=== MicroPython Expert Model - Remote Setup ==="
echo ""

# Check for CUDA
if ! command -v nvidia-smi &> /dev/null; then
    echo "WARNING: nvidia-smi not found. CUDA may not be available."
else
    echo "GPU Info:"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    echo ""
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists"
fi

# Activate venv
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install PyTorch with CUDA support
echo "Installing PyTorch with CUDA..."
pip install torch --index-url https://download.pytorch.org/whl/cu121

# Install other dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install flash-attention (optional, for faster training)
echo "Attempting to install flash-attention..."
pip install flash-attn --no-build-isolation || echo "flash-attn install failed (optional)"

# Pre-download the base model
echo ""
echo "Pre-downloading base model (this may take a while)..."
python3 -c "
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model_name = 'Qwen/Qwen3-Coder-8B-Instruct'
print(f'Downloading {model_name}...')

# Download tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
print('✓ Tokenizer downloaded')

# Download model (this is the big download)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,
    trust_remote_code=True,
)
print('✓ Model downloaded')
print('Model size:', sum(p.numel() for p in model.parameters()) / 1e9, 'B parameters')
"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "To start training:"
echo "  1. Start a tmux session: tmux new -s training"
echo "  2. Activate venv: source venv/bin/activate"
echo "  3. Run training: python training/train_sft.py 2>&1 | tee logs/training_\$(date +%Y%m%d_%H%M%S).log"
echo ""
echo "To detach from tmux: Ctrl+B, D"
echo "To reattach: tmux attach -t training"
