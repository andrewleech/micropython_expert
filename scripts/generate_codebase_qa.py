#!/usr/bin/env python3
"""
Generate codebase Q&A dataset for MicroPython Expert model.

Creates 10,000-20,000 Q&A pairs about MicroPython internals, grounded in
actual source code. Covers:

1. py/ core - Object model, GC, compiler, VM, bytecode
2. extmod/ - Hardware abstraction, network, filesystem
3. All 22 ports - Platform-specific implementations
4. Build system - Makefiles, configuration
5. Architecture - Design patterns, module organization

Uses Claude CLI to generate Q&A pairs from source file contexts.

Usage:
    python scripts/generate_codebase_qa.py
    python scripts/generate_codebase_qa.py --resume  # Resume from checkpoint
    python scripts/generate_codebase_qa.py --category py_core
"""

import json
import subprocess
import re
import sys
import time
from argparse import ArgumentParser
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Unbuffered output for real-time logging
sys.stdout.reconfigure(line_buffering=True)

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "training"
CHECKPOINT_PATH = PROJECT_ROOT / "data" / "codebase_qa_checkpoint.json"
MPY_ROOT = Path(__file__).parent.parent / "micropython"

# Rate limiting
DELAY_BETWEEN_CALLS = 1.0  # seconds

# Categories and their source directories/files
CATEGORIES = {
    "py_core": {
        "description": "Core Python implementation",
        "files": [
            "py/gc.c", "py/gc.h",
            "py/vm.c", "py/bc.h",
            "py/compile.c", "py/compile.h",
            "py/parse.c", "py/parse.h",
            "py/lexer.c", "py/lexer.h",
            "py/runtime.c", "py/runtime.h",
            "py/obj.h", "py/objtype.c",
            "py/objstr.c", "py/objlist.c", "py/objdict.c",
            "py/objint.c", "py/objfloat.c",
            "py/objfun.c", "py/objgenerator.c",
            "py/objmodule.c", "py/objexcept.c",
            "py/qstr.c", "py/qstr.h",
            "py/mpstate.h", "py/mpconfig.h",
            "py/nlr.h", "py/nlr.c",
            "py/malloc.c", "py/mpz.c",
            "py/emitbc.c", "py/emitglue.c",
            "py/nativeglue.c", "py/asmthumb.c",
            "py/scheduler.c", "py/stream.c",
        ],
        "target_count": 4000,
    },
    "extmod": {
        "description": "Extended modules and hardware abstraction",
        "files": [
            "extmod/machine_pin.c", "extmod/machine_pin.h",
            "extmod/machine_i2c.c", "extmod/machine_spi.c",
            "extmod/machine_uart.c", "extmod/machine_pwm.c",
            "extmod/machine_adc.c", "extmod/machine_timer.c",
            "extmod/machine_mem.c",
            "extmod/vfs.c", "extmod/vfs.h",
            "extmod/vfs_fat.c", "extmod/vfs_lfs.c",
            "extmod/modbluetooth.c", "extmod/modbluetooth.h",
            "extmod/modnetwork.c", "extmod/modnetwork.h",
            "extmod/modusocket.c", "extmod/modussl_mbedtls.c",
            "extmod/modasyncio.c", "extmod/modselect.c",
            "extmod/modframebuf.c",
            "extmod/modlwip.c", "extmod/modwebrepl.c",
            "extmod/modjson.c", "extmod/modre.c",
            "extmod/moductypes.c", "extmod/modstruct.c",
            "extmod/modhashlib.c", "extmod/modcryptolib.c",
            "extmod/modrandom.c", "extmod/modtime.c",
        ],
        "target_count": 3000,
    },
    "ports": {
        "description": "Port-specific implementations",
        "dirs": [
            "ports/stm32", "ports/esp32", "ports/esp8266",
            "ports/rp2", "ports/nrf", "ports/unix",
            "ports/samd", "ports/mimxrt", "ports/renesas-ra",
            "ports/zephyr", "ports/webassembly", "ports/windows",
            "ports/teensy", "ports/cc3200", "ports/qemu",
            "ports/bare-arm", "ports/minimal", "ports/embed",
        ],
        "target_count": 5000,
    },
    "build_system": {
        "description": "Build system and configuration",
        "files": [
            "py/py.mk", "py/mkrules.mk",
            "ports/stm32/Makefile", "ports/esp32/Makefile",
            "ports/rp2/CMakeLists.txt",
            "tools/mpy-tool.py", "tools/makemanifest.py",
            "mpy-cross/main.c",
        ],
        "target_count": 1500,
    },
    "docs_develop": {
        "description": "Development documentation and conventions",
        "files": [
            "docs/develop/compiler.rst",
            "docs/develop/qstr.rst",
            "docs/develop/memorymgt.rst",
            "docs/develop/library.rst",
            "docs/develop/cmodules.rst",
            "docs/develop/natmod.rst",
            "docs/develop/porting.rst",
            "CODECONVENTIONS.md",
        ],
        "target_count": 1500,
    },
}

# System prompt for Q&A generation
SYSTEM_PROMPT = """You are an expert MicroPython developer helping users understand the codebase. Provide clear, accurate explanations based on the source code."""


def call_claude(prompt: str) -> str:
    """Call Claude CLI and return response."""
    result = subprocess.run(
        ["claude", "-p", prompt, "--model", "haiku"],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Claude CLI error: {result.stderr}")
    return result.stdout.strip()


def read_source_file(path: Path, max_lines: int = 300) -> str:
    """Read source file content."""
    if not path.exists():
        return ""
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[:max_lines]
        return "".join(lines)
    except Exception:
        return ""


def find_c_files_in_dir(dir_path: Path, max_files: int = 20) -> list:
    """Find C source files in a directory."""
    if not dir_path.exists():
        return []
    c_files = list(dir_path.glob("*.c"))[:max_files]
    h_files = list(dir_path.glob("*.h"))[:max_files // 2]
    return c_files + h_files


def generate_qa_for_file(file_path: Path, category: str, qa_type: str = "explanation") -> list:
    """Generate Q&A pairs for a single source file."""
    content = read_source_file(file_path)
    if not content or len(content) < 100:
        return []

    rel_path = str(file_path.relative_to(MPY_ROOT)) if file_path.is_relative_to(MPY_ROOT) else str(file_path)

    # Different prompts for different types of Q&A
    if qa_type == "explanation":
        prompt = f"""You are creating a training dataset for a MicroPython expert model.

Given this source file ({rel_path}):

```
{content[:8000]}
```

Generate 3-5 Q&A pairs that would help someone understand this code.
Include questions about:
- What this file/module does
- Key functions and their purposes
- Important data structures
- How it fits into MicroPython's architecture

Format as JSON array:
[
  {{"question": "...", "answer": "..."}},
  ...
]

Questions should be natural (like a developer would ask).
Answers should be detailed (2-4 sentences) and accurate based on the code.
Only output the JSON array."""

    elif qa_type == "howto":
        prompt = f"""You are creating a training dataset for a MicroPython expert model.

Given this source file ({rel_path}):

```
{content[:8000]}
```

Generate 2-3 "how to" Q&A pairs about practical tasks related to this code.
Examples:
- How would I modify/extend this?
- How does this interact with other parts?
- What conventions should I follow?

Format as JSON array:
[
  {{"question": "...", "answer": "..."}},
  ...
]

Only output the JSON array."""

    elif qa_type == "debugging":
        prompt = f"""You are creating a training dataset for a MicroPython expert model.

Given this source file ({rel_path}):

```
{content[:8000]}
```

Generate 2-3 Q&A pairs about debugging or troubleshooting related to this code.
Examples:
- Common issues and how to diagnose them
- Debug strategies for this subsystem
- Error conditions and their causes

Format as JSON array:
[
  {{"question": "...", "answer": "..."}},
  ...
]

Only output the JSON array."""

    else:
        return []

    try:
        response = call_claude(prompt)
        json_match = re.search(r'\[[\s\S]*\]', response)
        if json_match:
            items = json.loads(json_match.group())
            for item in items:
                item["source_file"] = rel_path
                item["category"] = category
                item["qa_type"] = qa_type
            return items
    except Exception as e:
        print(f"  Error: {e}")
        return []

    return []


def save_checkpoint(data: dict):
    """Save progress checkpoint."""
    with open(CHECKPOINT_PATH, "w") as f:
        json.dump(data, f, indent=2)


def load_checkpoint() -> dict:
    """Load progress checkpoint."""
    if CHECKPOINT_PATH.exists():
        with open(CHECKPOINT_PATH) as f:
            return json.load(f)
    return {"processed_files": [], "qa_pairs": []}


def generate_codebase_qa(resume: bool = False, category_filter: str = None):
    """Main generation function."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if resume:
        checkpoint = load_checkpoint()
        processed_files = set(checkpoint.get("processed_files", []))
        all_qa_pairs = checkpoint.get("qa_pairs", [])
        print(f"Resuming from checkpoint: {len(all_qa_pairs)} pairs, {len(processed_files)} files processed")
    else:
        processed_files = set()
        all_qa_pairs = []

    categories_to_process = [category_filter] if category_filter else list(CATEGORIES.keys())

    for cat_name in categories_to_process:
        if cat_name not in CATEGORIES:
            print(f"Unknown category: {cat_name}")
            continue

        cat_config = CATEGORIES[cat_name]
        print(f"\n=== Processing {cat_name}: {cat_config['description']} ===")

        # Collect files to process
        files_to_process = []

        if "files" in cat_config:
            for f in cat_config["files"]:
                path = MPY_ROOT / f
                if path.exists():
                    files_to_process.append(path)

        if "dirs" in cat_config:
            for d in cat_config["dirs"]:
                dir_path = MPY_ROOT / d
                files_to_process.extend(find_c_files_in_dir(dir_path))

        print(f"Found {len(files_to_process)} files")

        # Filter already processed
        files_to_process = [f for f in files_to_process if str(f) not in processed_files]
        print(f"After filtering: {len(files_to_process)} files to process")

        target_count = cat_config.get("target_count", 1000)
        category_count = len([p for p in all_qa_pairs if p.get("category") == cat_name])

        for file_path in files_to_process:
            if category_count >= target_count:
                print(f"Reached target count for {cat_name}")
                break

            print(f"Processing: {file_path.name}")

            # Generate different types of Q&A
            for qa_type in ["explanation", "howto", "debugging"]:
                qa_pairs = generate_qa_for_file(file_path, cat_name, qa_type)
                if qa_pairs:
                    all_qa_pairs.extend(qa_pairs)
                    category_count += len(qa_pairs)
                    print(f"  +{len(qa_pairs)} {qa_type} pairs (category total: {category_count})")

                time.sleep(DELAY_BETWEEN_CALLS)

            processed_files.add(str(file_path))

            # Save checkpoint periodically
            if len(processed_files) % 10 == 0:
                save_checkpoint({
                    "processed_files": list(processed_files),
                    "qa_pairs": all_qa_pairs,
                })
                print(f"  Checkpoint saved ({len(all_qa_pairs)} total pairs)")

    # Final save
    print(f"\n=== Saving {len(all_qa_pairs)} Q&A pairs ===")

    # Write JSONL output
    output_path = OUTPUT_DIR / "codebase_qa.jsonl"
    with open(output_path, "w") as f:
        for pair in all_qa_pairs:
            # Format for SFT
            sft_example = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": pair["question"]},
                    {"role": "assistant", "content": pair["answer"]},
                ],
                "metadata": {
                    "source": "codebase",
                    "source_file": pair.get("source_file"),
                    "category": pair.get("category"),
                    "qa_type": pair.get("qa_type"),
                },
            }
            f.write(json.dumps(sft_example) + "\n")

    print(f"Wrote to {output_path}")

    # Write summary
    category_counts = defaultdict(int)
    for pair in all_qa_pairs:
        category_counts[pair.get("category", "unknown")] += 1

    summary = {
        "generated_at": datetime.now().isoformat(),
        "total_pairs": len(all_qa_pairs),
        "files_processed": len(processed_files),
        "category_counts": dict(category_counts),
    }

    summary_path = OUTPUT_DIR / "codebase_qa_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Summary: {summary}")

    # Clean up checkpoint
    if CHECKPOINT_PATH.exists():
        CHECKPOINT_PATH.unlink()
        print("Checkpoint cleaned up")


def main():
    parser = ArgumentParser()
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument("--category", type=str, help="Process only specific category")
    args = parser.parse_args()

    generate_codebase_qa(resume=args.resume, category_filter=args.category)


if __name__ == "__main__":
    main()
