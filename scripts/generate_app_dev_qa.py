#!/usr/bin/env python3
"""
Generate application development Q&A dataset for MicroPython Expert model.

Creates 3,000-5,000 Q&A pairs about practical MicroPython usage:
- Using machine module across ports
- Memory management best practices
- Freezing modules, native modules
- Debugging techniques
- Common pitfalls and solutions
- Peripheral programming patterns

Uses Claude CLI with examples from official docs and tutorials.

Usage:
    python scripts/generate_app_dev_qa.py
    python scripts/generate_app_dev_qa.py --topic gpio
"""

import json
import subprocess
import re
import sys
import time
from argparse import ArgumentParser
from pathlib import Path
from datetime import datetime

# Unbuffered output for real-time logging
sys.stdout.reconfigure(line_buffering=True)

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "training"
WIKI_DIR = PROJECT_ROOT / "data" / "wiki"
MPY_ROOT = Path(__file__).parent.parent / "micropython"

DELAY_BETWEEN_CALLS = 1.0

# Topics for application development guidance
TOPICS = {
    "gpio": {
        "title": "GPIO and Pin Control",
        "subtopics": [
            "Basic pin input/output",
            "Pull-up and pull-down resistors",
            "Pin interrupts and callbacks",
            "Open-drain outputs",
            "Pin.init() configuration options",
            "Port-specific pin naming",
        ],
        "target": 400,
    },
    "i2c_spi": {
        "title": "I2C and SPI Communication",
        "subtopics": [
            "I2C device scanning",
            "I2C read/write operations",
            "I2C with DMA",
            "SPI master mode",
            "SPI slave mode",
            "SPI with CS control",
            "Interfacing common sensors",
        ],
        "target": 500,
    },
    "uart_serial": {
        "title": "UART and Serial Communication",
        "subtopics": [
            "UART initialization",
            "Buffered serial read/write",
            "UART with interrupts",
            "RS485 and half-duplex",
            "USB CDC serial",
            "Debugging over UART",
        ],
        "target": 300,
    },
    "timers_pwm": {
        "title": "Timers and PWM",
        "subtopics": [
            "Timer callbacks",
            "One-shot vs periodic timers",
            "PWM frequency and duty cycle",
            "Servo control with PWM",
            "LED dimming",
            "Timer capture mode",
        ],
        "target": 350,
    },
    "memory": {
        "title": "Memory Management",
        "subtopics": [
            "Understanding gc.mem_free() and gc.mem_alloc()",
            "Triggering garbage collection",
            "Memory fragmentation",
            "Pre-allocating buffers",
            "memoryview for zero-copy",
            "Avoiding memory leaks",
            "Debugging out-of-memory errors",
        ],
        "target": 450,
    },
    "freezing": {
        "title": "Freezing and Deploying Code",
        "subtopics": [
            "Frozen modules vs filesystem modules",
            "Creating a manifest file",
            "Freezing bytecode vs source",
            "mpy-cross compilation",
            "Building custom firmware",
            "Packaging applications",
        ],
        "target": 350,
    },
    "networking": {
        "title": "WiFi and Networking",
        "subtopics": [
            "WiFi connection on ESP32",
            "Static IP configuration",
            "Socket programming basics",
            "HTTP requests with urequests",
            "MQTT client",
            "WebSocket client",
            "mDNS and service discovery",
        ],
        "target": 450,
    },
    "asyncio": {
        "title": "Async Programming",
        "subtopics": [
            "uasyncio basics",
            "Creating async tasks",
            "Event loops and scheduling",
            "StreamReader/StreamWriter",
            "Async I/O with hardware",
            "Common pitfalls with async",
        ],
        "target": 400,
    },
    "filesystem": {
        "title": "Filesystem and Storage",
        "subtopics": [
            "Using internal flash filesystem",
            "SD card with FAT",
            "LittleFS for reliability",
            "File operations",
            "Binary vs text files",
            "Filesystem corruption recovery",
        ],
        "target": 300,
    },
    "debugging": {
        "title": "Debugging Techniques",
        "subtopics": [
            "Using print() effectively",
            "REPL debugging",
            "Exception handling patterns",
            "Watchdog timers",
            "Stack overflow detection",
            "Remote debugging",
            "Logic analyzer integration",
        ],
        "target": 400,
    },
    "power": {
        "title": "Power Management",
        "subtopics": [
            "Light sleep vs deep sleep",
            "Wake-up sources",
            "Power consumption optimization",
            "Battery-powered applications",
            "Low-power sensor reading",
        ],
        "target": 300,
    },
    "peripherals": {
        "title": "Common Peripheral Patterns",
        "subtopics": [
            "ADC reading and calibration",
            "DAC output",
            "Capacitive touch sensing",
            "Rotary encoders",
            "Keypad matrix scanning",
            "Display drivers",
            "NeoPixel and WS2812",
        ],
        "target": 500,
    },
}

SYSTEM_PROMPT = """You are an expert MicroPython developer providing practical guidance. Give clear, working code examples when appropriate. Focus on real-world usage patterns."""


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


def load_wiki_content(topic: str) -> str:
    """Load relevant wiki content for context."""
    content_parts = []

    # Map topics to likely wiki pages
    wiki_mapping = {
        "gpio": ["Hardware-API.md", "Getting-Started.md"],
        "i2c_spi": ["Hardware-API.md", "Examples.md"],
        "memory": ["Memory-Manager.md", "Performance.md"],
        "freezing": ["Building-Micropython-Binaries.md"],
        "networking": ["PPP-on-ESP32.md"],
        "debugging": ["Developing-on-a-microcontroller.md", "ESP32-debugging.md"],
        "asyncio": ["Examples.md"],
        "timers_pwm": ["PWM-Timers.md", "Timer-Implementation.md"],
    }

    wiki_pages = wiki_mapping.get(topic, [])
    for page in wiki_pages:
        wiki_path = WIKI_DIR / page
        if wiki_path.exists():
            try:
                with open(wiki_path) as f:
                    content_parts.append(f"# From {page}:\n{f.read()[:2000]}")
            except Exception:
                pass

    return "\n\n".join(content_parts) if content_parts else ""


def generate_qa_for_subtopic(topic_key: str, topic_title: str, subtopic: str, wiki_context: str) -> list:
    """Generate Q&A pairs for a specific subtopic."""

    context_str = f"\n\nRelevant documentation:\n{wiki_context}" if wiki_context else ""

    prompt = f"""You are creating a training dataset for a MicroPython expert model.

Topic: {topic_title}
Subtopic: {subtopic}
{context_str}

Generate 5-8 practical Q&A pairs about "{subtopic}" in MicroPython.

Include:
1. Basic "how do I" questions with code examples
2. Common pitfalls and how to avoid them
3. Best practices and performance tips
4. Troubleshooting common issues

Format as JSON array:
[
  {{"question": "...", "answer": "..."}},
  ...
]

Requirements:
- Questions should be natural (like a developer would ask)
- Answers should include working MicroPython code when appropriate
- Answers should be practical and actionable (3-6 sentences or code + explanation)
- Cover both beginner and intermediate use cases

Only output the JSON array."""

    try:
        response = call_claude(prompt)
        json_match = re.search(r'\[[\s\S]*\]', response)
        if json_match:
            items = json.loads(json_match.group())
            for item in items:
                item["topic"] = topic_key
                item["subtopic"] = subtopic
            return items
    except Exception as e:
        print(f"  Error generating for {subtopic}: {e}")
        return []

    return []


def generate_app_dev_qa(topic_filter: str = None):
    """Main generation function."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_qa_pairs = []

    topics_to_process = [topic_filter] if topic_filter else list(TOPICS.keys())

    for topic_key in topics_to_process:
        if topic_key not in TOPICS:
            print(f"Unknown topic: {topic_key}")
            continue

        topic_config = TOPICS[topic_key]
        print(f"\n=== {topic_config['title']} ===")

        wiki_context = load_wiki_content(topic_key)
        if wiki_context:
            print(f"  Loaded wiki context ({len(wiki_context)} chars)")

        topic_pairs = []

        for subtopic in topic_config["subtopics"]:
            print(f"  Generating: {subtopic}")

            pairs = generate_qa_for_subtopic(
                topic_key,
                topic_config["title"],
                subtopic,
                wiki_context
            )

            if pairs:
                topic_pairs.extend(pairs)
                print(f"    +{len(pairs)} pairs")

            time.sleep(DELAY_BETWEEN_CALLS)

        all_qa_pairs.extend(topic_pairs)
        print(f"  Total for {topic_key}: {len(topic_pairs)} pairs")

    # Write output
    print(f"\n=== Saving {len(all_qa_pairs)} Q&A pairs ===")

    output_path = OUTPUT_DIR / "app_dev_qa.jsonl"
    with open(output_path, "w") as f:
        for pair in all_qa_pairs:
            sft_example = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": pair["question"]},
                    {"role": "assistant", "content": pair["answer"]},
                ],
                "metadata": {
                    "source": "app_dev",
                    "topic": pair.get("topic"),
                    "subtopic": pair.get("subtopic"),
                },
            }
            f.write(json.dumps(sft_example) + "\n")

    print(f"Wrote to {output_path}")

    # Summary
    topic_counts = {}
    for pair in all_qa_pairs:
        topic = pair.get("topic", "unknown")
        topic_counts[topic] = topic_counts.get(topic, 0) + 1

    summary = {
        "generated_at": datetime.now().isoformat(),
        "total_pairs": len(all_qa_pairs),
        "topic_counts": topic_counts,
    }

    summary_path = OUTPUT_DIR / "app_dev_qa_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Summary: {summary}")


def main():
    parser = ArgumentParser()
    parser.add_argument("--topic", type=str, help="Generate for specific topic only")
    args = parser.parse_args()

    generate_app_dev_qa(topic_filter=args.topic)


if __name__ == "__main__":
    main()
