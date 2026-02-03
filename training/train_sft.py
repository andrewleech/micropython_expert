#!/usr/bin/env python3
"""
Supervised Fine-Tuning script for MicroPython Expert model.

Trains on combined dataset of:
- Review comments (18K+ examples)
- Wiki Q&A (400+ examples)
- Codebase Q&A (to be generated)
- Application guidance (to be generated)

Usage:
    python training/train_sft.py
    python training/train_sft.py --resume_from_checkpoint ./models/.../checkpoint-1000
"""

import json
import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import torch
import yaml
from datasets import Dataset, concatenate_datasets
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    HfArgumentParser,
    TrainingArguments,
    set_seed,
)
from trl import SFTTrainer, SFTConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / "training" / "sft_config.yaml"
DATA_DIR = PROJECT_ROOT / "data" / "training"
EVAL_DIR = PROJECT_ROOT / "data" / "eval"


@dataclass
class ScriptArguments:
    """Additional script arguments beyond TrainingArguments."""

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


def load_jsonl_dataset(path: Path, weight: float = 1.0) -> Dataset:
    """Load a JSONL dataset file."""
    examples = []
    with open(path) as f:
        for line in f:
            ex = json.loads(line)
            # Convert to format expected by SFTTrainer
            examples.append({
                "messages": ex["messages"],
                "weight": weight,
            })
    logger.info(f"Loaded {len(examples)} examples from {path}")
    return Dataset.from_list(examples)


def load_all_datasets(config: dict) -> tuple[Dataset, Dataset]:
    """Load and combine all training datasets."""
    weights = config.get("dataset_weights", {})

    train_datasets = []
    eval_datasets = []

    # Load review SFT dataset
    reviews_path = DATA_DIR / "reviews_sft.jsonl"
    if reviews_path.exists():
        ds = load_jsonl_dataset(reviews_path, weights.get("reviews_sft", 1.0))
        train_datasets.append(ds)

    # Load wiki Q&A
    wiki_path = DATA_DIR / "wiki_qa.jsonl"
    if wiki_path.exists():
        ds = load_jsonl_dataset(wiki_path, weights.get("wiki_qa", 1.2))
        train_datasets.append(ds)

    # Load codebase Q&A (when available)
    codebase_path = DATA_DIR / "codebase_qa.jsonl"
    if codebase_path.exists():
        ds = load_jsonl_dataset(codebase_path, weights.get("codebase_qa", 1.5))
        train_datasets.append(ds)

    # Load app dev Q&A (when available)
    app_dev_path = DATA_DIR / "app_dev_qa.jsonl"
    if app_dev_path.exists():
        ds = load_jsonl_dataset(app_dev_path, weights.get("app_dev_qa", 1.0))
        train_datasets.append(ds)

    # Load combined dataset if it exists (overrides individual files)
    combined_path = DATA_DIR / "combined_sft.jsonl"
    if combined_path.exists():
        logger.info("Using pre-combined dataset")
        train_ds = load_jsonl_dataset(combined_path)
    elif train_datasets:
        train_ds = concatenate_datasets(train_datasets)
        logger.info(f"Combined {len(train_datasets)} datasets: {len(train_ds)} total examples")
    else:
        raise ValueError("No training data found!")

    # Load held-out evaluation set
    eval_path = EVAL_DIR / "held_out_reviews.jsonl"
    if eval_path.exists():
        eval_ds = load_jsonl_dataset(eval_path)
    else:
        # Use a small fraction of training data for eval
        logger.warning("No held-out eval set found, using 5% of training data")
        split = train_ds.train_test_split(test_size=0.05, seed=42)
        train_ds = split["train"]
        eval_ds = split["test"]

    return train_ds, eval_ds


def find_latest_checkpoint(output_dir: str) -> Optional[str]:
    """Find the latest checkpoint in output directory."""
    output_path = Path(output_dir)
    if not output_path.exists():
        return None

    checkpoints = list(output_path.glob("checkpoint-*"))
    if not checkpoints:
        return None

    # Sort by step number
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

    # Set seed for reproducibility
    set_seed(42)

    # Determine checkpoint to resume from
    resume_checkpoint = script_args.resume_from_checkpoint
    if resume_checkpoint is None and config.get("resume_from_checkpoint", True):
        resume_checkpoint = find_latest_checkpoint(config["output_dir"])
        if resume_checkpoint:
            logger.info(f"Auto-resuming from checkpoint: {resume_checkpoint}")

    # Load tokenizer
    logger.info(f"Loading tokenizer: {config['model_name']}")
    tokenizer = AutoTokenizer.from_pretrained(
        config["model_name"],
        trust_remote_code=True,
    )

    # Ensure padding token is set
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load model
    logger.info(f"Loading model: {config['model_name']}")
    model = AutoModelForCausalLM.from_pretrained(
        config["model_name"],
        torch_dtype=torch.bfloat16 if config.get("bf16", True) else torch.float32,
        trust_remote_code=True,
        attn_implementation="flash_attention_2",  # Use Flash Attention if available
    )

    # Enable gradient checkpointing if configured
    if config.get("gradient_checkpointing", True):
        model.gradient_checkpointing_enable()

    # Load datasets
    train_ds, eval_ds = load_all_datasets(config)
    logger.info(f"Training on {len(train_ds)} examples, evaluating on {len(eval_ds)}")

    # Create output directory
    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    # Setup training arguments
    training_args = SFTConfig(
        output_dir=str(output_dir),
        num_train_epochs=config.get("num_train_epochs", 3),
        per_device_train_batch_size=config.get("per_device_train_batch_size", 4),
        per_device_eval_batch_size=config.get("per_device_eval_batch_size", 8),
        gradient_accumulation_steps=config.get("gradient_accumulation_steps", 8),
        learning_rate=config.get("learning_rate", 2e-5),
        lr_scheduler_type=config.get("lr_scheduler_type", "cosine"),
        warmup_ratio=config.get("warmup_ratio", 0.1),
        weight_decay=config.get("weight_decay", 0.01),
        max_grad_norm=config.get("max_grad_norm", 1.0),
        bf16=config.get("bf16", True),
        tf32=config.get("tf32", True),
        gradient_checkpointing=config.get("gradient_checkpointing", True),
        save_strategy=config.get("save_strategy", "steps"),
        save_steps=config.get("save_steps", 500),
        save_total_limit=config.get("save_total_limit", 3),
        eval_strategy=config.get("evaluation_strategy", "steps"),
        eval_steps=config.get("eval_steps", 500),
        logging_steps=config.get("logging_steps", 10),
        report_to=config.get("report_to", "tensorboard"),
        dataloader_num_workers=config.get("dataloader_num_workers", 4),
        dataloader_pin_memory=config.get("dataloader_pin_memory", True),
        max_seq_length=config.get("max_seq_length", 4096),
        packing=config.get("packing", False),
        remove_unused_columns=True,
        seed=42,
    )

    # Create trainer
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        processing_class=tokenizer,
    )

    # Train
    logger.info("Starting training...")
    trainer.train(resume_from_checkpoint=resume_checkpoint)

    # Save final model
    logger.info("Saving final model...")
    trainer.save_model()
    tokenizer.save_pretrained(str(output_dir))

    # Save training stats
    stats = {
        "train_samples": len(train_ds),
        "eval_samples": len(eval_ds),
        "final_loss": trainer.state.log_history[-1].get("loss"),
        "total_steps": trainer.state.global_step,
    }
    with open(output_dir / "training_stats.json", "w") as f:
        json.dump(stats, f, indent=2)

    logger.info("Training complete!")
    logger.info(f"Model saved to {output_dir}")


if __name__ == "__main__":
    main()
