#!/usr/bin/env python3
"""
Merge LoRA adapters into base model for deployment.

Usage:
    python scripts/merge_lora.py
    python scripts/merge_lora.py --checkpoint ./models/micropython-expert-7b/checkpoint-2220
    python scripts/merge_lora.py --output ./models/merged
"""

import argparse
import logging
import sys
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_CHECKPOINT = PROJECT_ROOT / "models" / "micropython-expert-7b"
DEFAULT_OUTPUT = PROJECT_ROOT / "models" / "micropython-expert-7b-merged"
BASE_MODEL = "Qwen/Qwen2.5-Coder-7B-Instruct"


def find_latest_checkpoint(model_dir: Path) -> Path:
    """Find the latest checkpoint in model directory."""
    checkpoints = list(model_dir.glob("checkpoint-*"))
    if checkpoints:
        # Sort by step number and return latest
        latest = max(checkpoints, key=lambda p: int(p.name.split("-")[1]))
        logger.info(f"Found checkpoint: {latest}")
        return latest
    # If no checkpoints, assume model_dir contains the final model
    if (model_dir / "adapter_config.json").exists():
        return model_dir
    raise ValueError(f"No checkpoint or adapter found in {model_dir}")


def merge_lora(checkpoint_path: Path, output_path: Path):
    """Merge LoRA adapters into base model."""
    logger.info(f"Loading base model: {BASE_MODEL}")

    # Load base model in fp16 for merging
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=torch.float16,
        trust_remote_code=True,
        device_map="auto",
    )

    logger.info(f"Loading LoRA adapters from: {checkpoint_path}")
    model = PeftModel.from_pretrained(base_model, str(checkpoint_path))

    logger.info("Merging adapters into base model...")
    model = model.merge_and_unload()

    # Save merged model
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Saving merged model to: {output_path}")
    model.save_pretrained(output_path, safe_serialization=True)

    # Save tokenizer
    logger.info("Saving tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    tokenizer.save_pretrained(output_path)

    logger.info("Merge complete!")
    logger.info(f"Merged model saved to: {output_path}")

    # Print size info
    total_size = sum(f.stat().st_size for f in output_path.glob("*.safetensors"))
    logger.info(f"Total model size: {total_size / 1e9:.2f} GB")


def main():
    parser = argparse.ArgumentParser(description="Merge LoRA adapters into base model")
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=DEFAULT_CHECKPOINT,
        help="Path to checkpoint directory or model with adapters",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output directory for merged model",
    )
    args = parser.parse_args()

    checkpoint_path = find_latest_checkpoint(args.checkpoint)
    merge_lora(checkpoint_path, args.output)


if __name__ == "__main__":
    main()
