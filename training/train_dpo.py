#!/usr/bin/env python3
"""
Direct Preference Optimization (DPO) training for MicroPython Expert model.

Aligns the SFT model to prefer high-quality reviews (blocking/suggestion)
over lower-quality ones (nitpick) or incorrect patterns.

Usage:
    python training/train_dpo.py
    python training/train_dpo.py --resume_from_checkpoint ./models/.../checkpoint-200
"""

import json
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import torch
import yaml
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    HfArgumentParser,
    set_seed,
)
from trl import DPOConfig, DPOTrainer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / "training" / "dpo_config.yaml"
DATA_DIR = PROJECT_ROOT / "data" / "training"


@dataclass
class ScriptArguments:
    """Additional script arguments."""

    config_path: str = field(
        default=str(CONFIG_PATH),
        metadata={"help": "Path to YAML config file"},
    )
    resume_from_checkpoint: Optional[str] = field(
        default=None,
        metadata={"help": "Path to checkpoint to resume from"},
    )


def load_config(config_path: str) -> dict:
    """Load YAML configuration."""
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_dpo_dataset(path: Path) -> Dataset:
    """Load DPO preference dataset."""
    examples = []
    with open(path) as f:
        for line in f:
            ex = json.loads(line)
            # DPO format expects: prompt, chosen, rejected
            examples.append({
                "prompt": ex["prompt"],
                "chosen": ex["chosen"],
                "rejected": ex["rejected"],
            })
    logger.info(f"Loaded {len(examples)} preference pairs from {path}")
    return Dataset.from_list(examples)


def find_latest_checkpoint(output_dir: str) -> Optional[str]:
    """Find the latest checkpoint in output directory."""
    output_path = Path(output_dir)
    if not output_path.exists():
        return None

    checkpoints = list(output_path.glob("checkpoint-*"))
    if not checkpoints:
        return None

    def get_step(cp):
        try:
            return int(cp.name.split("-")[1])
        except (IndexError, ValueError):
            return 0

    latest = max(checkpoints, key=get_step)
    return str(latest)


def main():
    # Parse arguments
    parser = HfArgumentParser(ScriptArguments)
    script_args = parser.parse_args_into_dataclasses()[0]

    # Load config
    config = load_config(script_args.config_path)
    logger.info(f"Loaded config from {script_args.config_path}")

    set_seed(42)

    # Load preference dataset
    dpo_path = DATA_DIR / "dpo_preferences.jsonl"
    if not dpo_path.exists():
        logger.error(f"DPO dataset not found at {dpo_path}")
        logger.error("Run scripts/export_dpo_dataset.py first")
        sys.exit(1)

    train_ds = load_dpo_dataset(dpo_path)

    # Split into train/eval
    split = train_ds.train_test_split(test_size=0.1, seed=42)
    train_ds = split["train"]
    eval_ds = split["test"]

    # Determine checkpoint
    resume_checkpoint = script_args.resume_from_checkpoint
    if resume_checkpoint is None and config.get("resume_from_checkpoint", True):
        resume_checkpoint = find_latest_checkpoint(config["output_dir"])
        if resume_checkpoint:
            logger.info(f"Auto-resuming from checkpoint: {resume_checkpoint}")

    # Load model (from SFT checkpoint)
    model_path = config["model_name"]
    logger.info(f"Loading model: {model_path}")

    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.bfloat16 if config.get("bf16", True) else torch.float32,
        trust_remote_code=True,
        attn_implementation="flash_attention_2",
    )

    # Load reference model (same as base, frozen)
    ref_model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.bfloat16 if config.get("bf16", True) else torch.float32,
        trust_remote_code=True,
        attn_implementation="flash_attention_2",
    )

    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        trust_remote_code=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Create output directory
    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    # Setup DPO training arguments
    training_args = DPOConfig(
        output_dir=str(output_dir),
        beta=config.get("beta", 0.1),
        loss_type=config.get("loss_type", "sigmoid"),
        num_train_epochs=config.get("num_train_epochs", 1),
        per_device_train_batch_size=config.get("per_device_train_batch_size", 2),
        gradient_accumulation_steps=config.get("gradient_accumulation_steps", 8),
        learning_rate=config.get("learning_rate", 5e-7),
        lr_scheduler_type=config.get("lr_scheduler_type", "cosine"),
        warmup_ratio=config.get("warmup_ratio", 0.1),
        weight_decay=config.get("weight_decay", 0.01),
        max_grad_norm=config.get("max_grad_norm", 1.0),
        bf16=config.get("bf16", True),
        tf32=config.get("tf32", True),
        gradient_checkpointing=config.get("gradient_checkpointing", True),
        save_strategy=config.get("save_strategy", "steps"),
        save_steps=config.get("save_steps", 200),
        save_total_limit=config.get("save_total_limit", 2),
        logging_steps=config.get("logging_steps", 10),
        report_to=config.get("report_to", "tensorboard"),
        max_length=config.get("max_length", 4096),
        max_prompt_length=config.get("max_prompt_length", 2048),
        seed=42,
    )

    # Create DPO trainer
    trainer = DPOTrainer(
        model=model,
        ref_model=ref_model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        processing_class=tokenizer,
    )

    # Train
    logger.info("Starting DPO training...")
    trainer.train(resume_from_checkpoint=resume_checkpoint)

    # Save final model
    logger.info("Saving final model...")
    trainer.save_model()
    tokenizer.save_pretrained(str(output_dir))

    logger.info("DPO training complete!")
    logger.info(f"Model saved to {output_dir}")


if __name__ == "__main__":
    main()
