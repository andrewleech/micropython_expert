#!/usr/bin/env python3
"""
Combine all training datasets into a single weighted dataset.

Merges:
- reviews_sft.jsonl (18K) - weight 1.0
- pr_reviews.jsonl - weight 2.0
- synthetic_reviews.jsonl - weight 2.5
- wiki_qa.jsonl (400+) - weight 1.2
- codebase_qa.jsonl (10K-20K) - weight 1.5
- app_dev_qa.jsonl (3K-5K) - weight 1.0

Weighting is implemented by oversampling - examples with higher weights
appear more frequently in the combined dataset.

Usage:
    python scripts/combine_datasets.py
"""

import json
import random
from pathlib import Path
from datetime import datetime
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "training"

RANDOM_SEED = 42

# Dataset weights (relative sampling frequency)
DATASET_WEIGHTS = {
    "reviews_sft.jsonl": 1.0,
    "pr_reviews.jsonl": 2.0,
    "synthetic_reviews.jsonl": 2.5,
    "wiki_qa.jsonl": 1.2,
    "codebase_qa.jsonl": 1.5,
    "app_dev_qa.jsonl": 1.0,
}


def load_jsonl(path: Path) -> list:
    """Load JSONL file."""
    examples = []
    with open(path) as f:
        for line in f:
            examples.append(json.loads(line))
    return examples


def combine_datasets():
    """Combine all datasets with weighting."""
    random.seed(RANDOM_SEED)

    all_examples = []
    stats = {}

    for filename, weight in DATASET_WEIGHTS.items():
        path = DATA_DIR / filename
        if not path.exists():
            print(f"Skipping {filename} (not found)")
            continue

        examples = load_jsonl(path)
        original_count = len(examples)

        # Apply weighting by oversampling
        if weight > 1.0:
            # Oversample: duplicate some examples
            extra_samples = int(len(examples) * (weight - 1.0))
            extra = random.choices(examples, k=extra_samples)
            examples = examples + extra
        elif weight < 1.0:
            # Undersample: keep only a fraction
            keep_count = int(len(examples) * weight)
            examples = random.sample(examples, keep_count)

        # Add source tag to metadata
        for ex in examples:
            if "metadata" not in ex:
                ex["metadata"] = {}
            ex["metadata"]["dataset"] = filename

        all_examples.extend(examples)
        stats[filename] = {
            "original": original_count,
            "weight": weight,
            "after_weighting": len(examples),
        }
        print(f"Loaded {filename}: {original_count} -> {len(examples)} (weight {weight})")

    # Shuffle
    random.shuffle(all_examples)

    print(f"\nTotal combined examples: {len(all_examples)}")

    # Write combined dataset
    output_path = DATA_DIR / "combined_sft.jsonl"
    with open(output_path, "w") as f:
        for ex in all_examples:
            f.write(json.dumps(ex) + "\n")

    print(f"Wrote to {output_path}")

    # Write summary
    summary = {
        "combined_at": datetime.now().isoformat(),
        "total_examples": len(all_examples),
        "random_seed": RANDOM_SEED,
        "datasets": stats,
        "weights": DATASET_WEIGHTS,
    }

    summary_path = DATA_DIR / "combined_sft_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Summary saved to {summary_path}")

    # Distribution check
    print("\nDataset distribution in combined set:")
    dist = defaultdict(int)
    for ex in all_examples:
        ds = ex.get("metadata", {}).get("dataset", "unknown")
        dist[ds] += 1

    for ds, count in sorted(dist.items()):
        pct = 100.0 * count / len(all_examples)
        print(f"  {ds}: {count} ({pct:.1f}%)")


if __name__ == "__main__":
    combine_datasets()
