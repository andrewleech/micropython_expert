#!/usr/bin/env python3
"""
Evaluation script for MicroPython Expert model.

Runs evaluation benchmarks and computes metrics for:
1. Style fidelity (vocabulary, length, formatting)
2. Technical accuracy (factual Q&A)
3. Review quality (held-out review comparison)
4. Codebase knowledge (port-specific questions)

Usage:
    python training/evaluate.py --model ./models/micropython-expert-8b
    python training/evaluate.py --model Qwen/Qwen3-Coder-8B-Instruct  # baseline
"""

import json
import logging
import re
import sys
from argparse import ArgumentParser
from collections import defaultdict
from pathlib import Path

import torch
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
EVAL_DIR = PROJECT_ROOT / "data" / "eval"


def load_model_and_tokenizer(model_path: str):
    """Load model and tokenizer."""
    logger.info(f"Loading model: {model_path}")
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    return model, tokenizer


def generate_response(model, tokenizer, messages: list, max_new_tokens: int = 512) -> str:
    """Generate a response given a conversation."""
    # Apply chat template
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,  # Greedy for evaluation
            pad_token_id=tokenizer.pad_token_id,
        )

    # Decode only the generated part
    response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    return response.strip()


def compute_style_metrics(generated: str, reference: str) -> dict:
    """Compute style similarity metrics."""
    # Word count comparison
    gen_words = len(generated.split())
    ref_words = len(reference.split())

    # Sentence count
    gen_sentences = len(re.split(r'[.!?]+', generated))
    ref_sentences = len(re.split(r'[.!?]+', reference))

    # Code block usage
    gen_code_blocks = generated.count('```')
    ref_code_blocks = reference.count('```')

    # Backtick usage (inline code)
    gen_backticks = generated.count('`') - gen_code_blocks * 6
    ref_backticks = reference.count('`') - ref_code_blocks * 6

    return {
        "gen_word_count": gen_words,
        "ref_word_count": ref_words,
        "word_ratio": gen_words / max(ref_words, 1),
        "gen_sentence_count": gen_sentences,
        "ref_sentence_count": ref_sentences,
        "gen_code_blocks": gen_code_blocks // 2,  # Count pairs
        "ref_code_blocks": ref_code_blocks // 2,
        "gen_inline_code": gen_backticks // 2,
        "ref_inline_code": ref_backticks // 2,
    }


def evaluate_held_out_reviews(model, tokenizer, limit: int = 100) -> dict:
    """Evaluate on held-out review dataset."""
    eval_path = EVAL_DIR / "held_out_reviews.jsonl"
    if not eval_path.exists():
        logger.warning(f"Held-out reviews not found: {eval_path}")
        return {}

    examples = []
    with open(eval_path) as f:
        for line in f:
            examples.append(json.loads(line))

    if limit:
        examples = examples[:limit]

    logger.info(f"Evaluating on {len(examples)} held-out reviews...")

    all_metrics = []
    for ex in tqdm(examples, desc="Generating reviews"):
        messages = ex["messages"]
        # Generate response using system + user, compare to assistant
        input_messages = [m for m in messages if m["role"] != "assistant"]
        reference = [m for m in messages if m["role"] == "assistant"][0]["content"]

        generated = generate_response(model, tokenizer, input_messages)
        metrics = compute_style_metrics(generated, reference)
        all_metrics.append(metrics)

    # Aggregate metrics
    agg = defaultdict(list)
    for m in all_metrics:
        for k, v in m.items():
            agg[k].append(v)

    results = {
        "num_samples": len(examples),
        "avg_gen_word_count": sum(agg["gen_word_count"]) / len(agg["gen_word_count"]),
        "avg_ref_word_count": sum(agg["ref_word_count"]) / len(agg["ref_word_count"]),
        "avg_word_ratio": sum(agg["word_ratio"]) / len(agg["word_ratio"]),
        "avg_gen_sentence_count": sum(agg["gen_sentence_count"]) / len(agg["gen_sentence_count"]),
        "avg_ref_sentence_count": sum(agg["ref_sentence_count"]) / len(agg["ref_sentence_count"]),
    }

    return results


def evaluate_factual_qa(model, tokenizer, limit: int = None) -> dict:
    """Evaluate factual Q&A accuracy."""
    eval_path = EVAL_DIR / "factual_qa.jsonl"
    if not eval_path.exists():
        logger.warning(f"Factual Q&A not found: {eval_path}")
        return {}

    examples = []
    with open(eval_path) as f:
        for line in f:
            examples.append(json.loads(line))

    if limit:
        examples = examples[:limit]

    logger.info(f"Evaluating on {len(examples)} factual Q&A examples...")

    correct = 0
    total = 0

    for ex in tqdm(examples, desc="Factual Q&A"):
        question = ex["question"]
        expected = ex["answer"]
        keywords = ex.get("keywords", [])

        messages = [
            {"role": "system", "content": "You are a MicroPython expert. Answer concisely."},
            {"role": "user", "content": question},
        ]

        response = generate_response(model, tokenizer, messages, max_new_tokens=256)

        # Check if response contains expected answer or keywords
        response_lower = response.lower()
        expected_lower = expected.lower()

        match = expected_lower in response_lower
        if not match and keywords:
            match = any(kw.lower() in response_lower for kw in keywords)

        if match:
            correct += 1
        total += 1

    accuracy = correct / total if total > 0 else 0

    return {
        "num_samples": total,
        "correct": correct,
        "accuracy": accuracy,
    }


def evaluate_port_knowledge(model, tokenizer, limit: int = None) -> dict:
    """Evaluate port-specific knowledge."""
    eval_path = EVAL_DIR / "port_knowledge.jsonl"
    if not eval_path.exists():
        logger.warning(f"Port knowledge not found: {eval_path}")
        return {}

    examples = []
    with open(eval_path) as f:
        for line in f:
            examples.append(json.loads(line))

    if limit:
        examples = examples[:limit]

    logger.info(f"Evaluating on {len(examples)} port knowledge examples...")

    port_results = defaultdict(lambda: {"correct": 0, "total": 0})

    for ex in tqdm(examples, desc="Port knowledge"):
        port = ex.get("port", "unknown")
        question = ex["question"]
        expected = ex["answer"]
        keywords = ex.get("keywords", [])

        messages = [
            {"role": "system", "content": "You are a MicroPython expert. Answer concisely."},
            {"role": "user", "content": question},
        ]

        response = generate_response(model, tokenizer, messages, max_new_tokens=256)

        response_lower = response.lower()
        expected_lower = expected.lower()

        match = expected_lower in response_lower
        if not match and keywords:
            match = any(kw.lower() in response_lower for kw in keywords)

        port_results[port]["total"] += 1
        if match:
            port_results[port]["correct"] += 1

    # Compute per-port accuracy
    results = {"per_port": {}}
    total_correct = 0
    total_count = 0

    for port, counts in port_results.items():
        acc = counts["correct"] / counts["total"] if counts["total"] > 0 else 0
        results["per_port"][port] = {
            "accuracy": acc,
            "correct": counts["correct"],
            "total": counts["total"],
        }
        total_correct += counts["correct"]
        total_count += counts["total"]

    results["overall_accuracy"] = total_correct / total_count if total_count > 0 else 0
    results["num_ports"] = len(port_results)

    return results


def main():
    parser = ArgumentParser()
    parser.add_argument("--model", required=True, help="Model path or HF model ID")
    parser.add_argument("--output", default=None, help="Output JSON file for results")
    parser.add_argument("--limit", type=int, default=100, help="Limit examples per benchmark")
    args = parser.parse_args()

    model, tokenizer = load_model_and_tokenizer(args.model)

    results = {
        "model": args.model,
        "benchmarks": {},
    }

    # Run evaluations
    logger.info("\n=== Held-out Reviews ===")
    results["benchmarks"]["held_out_reviews"] = evaluate_held_out_reviews(
        model, tokenizer, limit=args.limit
    )
    for k, v in results["benchmarks"]["held_out_reviews"].items():
        logger.info(f"  {k}: {v:.3f}" if isinstance(v, float) else f"  {k}: {v}")

    logger.info("\n=== Factual Q&A ===")
    results["benchmarks"]["factual_qa"] = evaluate_factual_qa(model, tokenizer, limit=args.limit)
    for k, v in results["benchmarks"]["factual_qa"].items():
        logger.info(f"  {k}: {v:.3f}" if isinstance(v, float) else f"  {k}: {v}")

    logger.info("\n=== Port Knowledge ===")
    results["benchmarks"]["port_knowledge"] = evaluate_port_knowledge(
        model, tokenizer, limit=args.limit
    )
    pk = results["benchmarks"]["port_knowledge"]
    if pk:
        logger.info(f"  Overall accuracy: {pk.get('overall_accuracy', 0):.3f}")
        logger.info(f"  Ports evaluated: {pk.get('num_ports', 0)}")

    # Save results
    output_path = args.output or PROJECT_ROOT / "docs" / "EVALUATION_RESULTS.json"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
