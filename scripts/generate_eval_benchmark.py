#!/usr/bin/env python3
"""
Generate evaluation benchmarks for MicroPython Expert model.

Creates:
1. Factual Q&A - verifiable questions about MicroPython internals
2. Port knowledge - questions specific to each of the 22 ports
3. Style benchmark - pairs for A/B testing style fidelity

Uses Claude CLI to generate questions from:
- Source code files
- Documentation
- Existing review comments (extract factual statements)

Usage:
    python scripts/generate_eval_benchmark.py --factual
    python scripts/generate_eval_benchmark.py --ports
    python scripts/generate_eval_benchmark.py --all
"""

import json
import subprocess
import sqlite3
import re
from argparse import ArgumentParser
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "raw" / "dpgeorge_reviews.db"
EVAL_DIR = PROJECT_ROOT / "data" / "eval"
MPY_ROOT = Path(__file__).parent.parent / "micropython"

# All 22 MicroPython ports
PORTS = [
    "cc3200", "esp32", "esp8266", "mimxrt", "nrf", "pic16bit",
    "powerpc", "qemu", "renesas-ra", "rp2", "samd", "stm32",
    "teensy", "unix", "webassembly", "windows", "zephyr",
    "bare-arm", "embed", "minimal", "alif", "psoc6"
]

# Core directories for factual Q&A
CORE_DIRS = ["py", "extmod", "shared", "lib"]


def call_claude(prompt: str, max_tokens: int = 4096) -> str:
    """Call Claude CLI and return response."""
    result = subprocess.run(
        ["claude", "-p", prompt, "--max-tokens", str(max_tokens)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Claude CLI error: {result.stderr}")
    return result.stdout.strip()


def read_source_file(path: Path, max_lines: int = 200) -> str:
    """Read source file, truncated for context window."""
    if not path.exists():
        return ""
    try:
        with open(path) as f:
            lines = f.readlines()[:max_lines]
        return "".join(lines)
    except Exception:
        return ""


def extract_factual_from_reviews():
    """Extract factual statements from review comments."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # Get reviews that mention specific code locations
    cursor = conn.execute("""
        SELECT rc.body, rc.path
        FROM review_comments rc
        JOIN comment_categories cc ON rc.id = cc.comment_id AND cc.comment_type = 'review_comment'
        WHERE cc.severity = 'blocking'
            AND rc.path IS NOT NULL
            AND (rc.body LIKE '%should%' OR rc.body LIKE '%must%' OR rc.body LIKE '%use%'
                 OR rc.body LIKE '%is%' OR rc.body LIKE '%are%')
        LIMIT 500
    """)

    factual_candidates = []
    for row in cursor:
        factual_candidates.append({
            "body": row["body"],
            "path": row["path"],
        })

    conn.close()
    return factual_candidates


def generate_factual_qa_from_source():
    """Generate factual Q&A from core source files."""
    qa_pairs = []

    # Key files to generate questions about
    key_files = [
        ("py/gc.c", "garbage collector"),
        ("py/vm.c", "virtual machine"),
        ("py/compile.c", "compiler"),
        ("py/parse.c", "parser"),
        ("py/lexer.c", "lexer"),
        ("py/objstr.c", "string objects"),
        ("py/objlist.c", "list objects"),
        ("py/objdict.c", "dict objects"),
        ("py/qstr.c", "QSTR interning"),
        ("py/mpstate.h", "interpreter state"),
        ("py/runtime.c", "runtime"),
        ("extmod/machine_pin.c", "GPIO pin abstraction"),
        ("extmod/machine_i2c.c", "I2C abstraction"),
        ("extmod/machine_spi.c", "SPI abstraction"),
        ("extmod/vfs.c", "virtual filesystem"),
    ]

    for rel_path, description in key_files:
        full_path = MPY_ROOT / rel_path
        if not full_path.exists():
            continue

        content = read_source_file(full_path, max_lines=150)
        if not content:
            continue

        prompt = f"""You are helping create a factual Q&A benchmark for a MicroPython expert model.

Given this source file ({rel_path}) which implements the {description}:

```c
{content}
```

Generate 5-10 factual questions with short, verifiable answers about this code.
Questions should test knowledge of:
- Key function names and their purposes
- Data structures used
- Important macros or constants
- Design patterns or conventions

Format as JSON array:
[
  {{"question": "...", "answer": "...", "keywords": ["key1", "key2"]}},
  ...
]

The "answer" should be concise (1-2 sentences). "keywords" are alternative terms that would indicate a correct answer.
Only output the JSON array, no other text."""

        try:
            response = call_claude(prompt)
            # Extract JSON from response
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                items = json.loads(json_match.group())
                for item in items:
                    item["source_file"] = rel_path
                    item["category"] = "core"
                    qa_pairs.append(item)
                print(f"Generated {len(items)} Q&A pairs from {rel_path}")
        except Exception as e:
            print(f"Error processing {rel_path}: {e}")

    return qa_pairs


def generate_port_knowledge():
    """Generate port-specific Q&A for each of the 22 ports."""
    qa_pairs = []

    for port in PORTS:
        port_dir = MPY_ROOT / "ports" / port
        if not port_dir.exists():
            print(f"Port not found: {port}")
            continue

        # Find key files in the port
        main_c = port_dir / "main.c"
        mpconfigport = port_dir / "mpconfigport.h"
        makefile = port_dir / "Makefile"

        # Read available files
        content_parts = []
        if main_c.exists():
            content_parts.append(f"main.c:\n```c\n{read_source_file(main_c, 100)}\n```")
        if mpconfigport.exists():
            content_parts.append(f"mpconfigport.h:\n```c\n{read_source_file(mpconfigport, 100)}\n```")

        if not content_parts:
            continue

        content = "\n\n".join(content_parts)

        prompt = f"""You are helping create a port-specific Q&A benchmark for a MicroPython expert model.

The {port} port of MicroPython has these key files:

{content}

Generate 3-5 factual questions specific to the {port} port with short, verifiable answers.
Questions should test knowledge of:
- Port-specific features or limitations
- Hardware/platform characteristics
- Configuration options
- Build requirements

Format as JSON array:
[
  {{"question": "...", "answer": "...", "keywords": ["key1", "key2"]}},
  ...
]

Only output the JSON array, no other text."""

        try:
            response = call_claude(prompt)
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                items = json.loads(json_match.group())
                for item in items:
                    item["port"] = port
                    item["category"] = "port_knowledge"
                    qa_pairs.append(item)
                print(f"Generated {len(items)} Q&A pairs for {port}")
        except Exception as e:
            print(f"Error processing {port}: {e}")

    return qa_pairs


def generate_style_benchmark():
    """Create style comparison pairs from review database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # Get highly-rated style examples
    cursor = conn.execute("""
        SELECT rc.body, rc.path, rc.diff_hunk
        FROM review_comments rc
        JOIN comment_categories cc ON rc.id = cc.comment_id AND cc.comment_type = 'review_comment'
        WHERE cc.is_style_example = 1
            AND cc.severity IN ('blocking', 'suggestion')
            AND length(rc.body) BETWEEN 50 AND 500
        ORDER BY RANDOM()
        LIMIT 200
    """)

    style_examples = []
    for row in cursor:
        style_examples.append({
            "body": row["body"],
            "path": row["path"],
            "diff_hunk": row["diff_hunk"],
            "is_dpgeorge": True,
        })

    conn.close()

    # Save as style benchmark (will be used for A/B testing)
    return style_examples


def main():
    parser = ArgumentParser()
    parser.add_argument("--factual", action="store_true", help="Generate factual Q&A")
    parser.add_argument("--ports", action="store_true", help="Generate port-specific Q&A")
    parser.add_argument("--style", action="store_true", help="Generate style benchmark")
    parser.add_argument("--all", action="store_true", help="Generate all benchmarks")
    args = parser.parse_args()

    if args.all:
        args.factual = args.ports = args.style = True

    if not (args.factual or args.ports or args.style):
        print("Specify --factual, --ports, --style, or --all")
        return

    EVAL_DIR.mkdir(parents=True, exist_ok=True)

    if args.factual:
        print("\n=== Generating Factual Q&A ===")
        factual_qa = generate_factual_qa_from_source()

        output_path = EVAL_DIR / "factual_qa.jsonl"
        with open(output_path, "w") as f:
            for item in factual_qa:
                f.write(json.dumps(item) + "\n")
        print(f"Wrote {len(factual_qa)} factual Q&A pairs to {output_path}")

    if args.ports:
        print("\n=== Generating Port Knowledge Q&A ===")
        port_qa = generate_port_knowledge()

        output_path = EVAL_DIR / "port_knowledge.jsonl"
        with open(output_path, "w") as f:
            for item in port_qa:
                f.write(json.dumps(item) + "\n")
        print(f"Wrote {len(port_qa)} port Q&A pairs to {output_path}")

    if args.style:
        print("\n=== Generating Style Benchmark ===")
        style_examples = generate_style_benchmark()

        output_path = EVAL_DIR / "style_benchmark.jsonl"
        with open(output_path, "w") as f:
            for item in style_examples:
                f.write(json.dumps(item) + "\n")
        print(f"Wrote {len(style_examples)} style examples to {output_path}")

    # Write summary
    summary = {
        "generated_at": datetime.now().isoformat(),
        "benchmarks": {
            "factual_qa": (EVAL_DIR / "factual_qa.jsonl").exists(),
            "port_knowledge": (EVAL_DIR / "port_knowledge.jsonl").exists(),
            "style_benchmark": (EVAL_DIR / "style_benchmark.jsonl").exists(),
        },
    }
    with open(EVAL_DIR / "benchmark_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("\nDone!")


if __name__ == "__main__":
    main()
