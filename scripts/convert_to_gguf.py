#!/usr/bin/env python3
"""
Convert merged model to GGUF format for llama.cpp/Ollama.

Requires llama.cpp to be cloned and built:
    git clone https://github.com/ggerganov/llama.cpp
    cd llama.cpp && make

Usage:
    python scripts/convert_to_gguf.py
    python scripts/convert_to_gguf.py --quantizations q4_k_m q5_k_m q8_0
    python scripts/convert_to_gguf.py --llama-cpp /path/to/llama.cpp
"""

import argparse
import logging
import shutil
import subprocess
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_INPUT = PROJECT_ROOT / "models" / "micropython-expert-7b-merged"
DEFAULT_OUTPUT = PROJECT_ROOT / "models" / "gguf"

# Quantization types and their approximate sizes for 7B model
QUANTIZATIONS = {
    "f16": {"size_gb": 14.0, "description": "Full fp16, highest quality"},
    "q8_0": {"size_gb": 7.5, "description": "8-bit, ~99% quality"},
    "q6_k": {"size_gb": 5.5, "description": "6-bit, ~98% quality"},
    "q5_k_m": {"size_gb": 4.8, "description": "5-bit medium, ~97% quality"},
    "q5_k_s": {"size_gb": 4.5, "description": "5-bit small, ~96% quality"},
    "q4_k_m": {"size_gb": 4.1, "description": "4-bit medium, ~95% quality, recommended"},
    "q4_k_s": {"size_gb": 3.8, "description": "4-bit small, ~94% quality"},
    "q4_0": {"size_gb": 3.5, "description": "4-bit legacy, ~93% quality"},
    "q3_k_m": {"size_gb": 3.1, "description": "3-bit medium, ~90% quality"},
    "q2_k": {"size_gb": 2.5, "description": "2-bit, ~85% quality, experimental"},
}

DEFAULT_QUANTS = ["q4_k_m", "q5_k_m", "q8_0"]


def find_llama_cpp() -> Path:
    """Find llama.cpp installation."""
    # Check common locations
    candidates = [
        Path.home() / "llama.cpp",
        Path("/opt/llama.cpp"),
        Path("./llama.cpp"),
        PROJECT_ROOT / "llama.cpp",
    ]

    for path in candidates:
        if (path / "convert_hf_to_gguf.py").exists():
            return path

    # Check if in PATH
    if shutil.which("llama-quantize"):
        # Find the directory
        result = subprocess.run(
            ["which", "llama-quantize"], capture_output=True, text=True
        )
        if result.returncode == 0:
            return Path(result.stdout.strip()).parent.parent

    return None


def convert_to_gguf_f16(input_dir: Path, output_dir: Path, llama_cpp: Path) -> Path:
    """Convert HuggingFace model to GGUF f16 format."""
    output_file = output_dir / "micropython-expert-7b-f16.gguf"

    if output_file.exists():
        logger.info(f"F16 GGUF already exists: {output_file}")
        return output_file

    logger.info("Converting to GGUF f16 format...")

    convert_script = llama_cpp / "convert_hf_to_gguf.py"
    cmd = [
        sys.executable,
        str(convert_script),
        str(input_dir),
        "--outfile",
        str(output_file),
        "--outtype",
        "f16",
    ]

    logger.info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"Conversion failed: {result.stderr}")
        raise RuntimeError("GGUF conversion failed")

    logger.info(f"Created: {output_file}")
    return output_file


def quantize_gguf(
    input_file: Path, output_dir: Path, quant_type: str, llama_cpp: Path
) -> Path:
    """Quantize GGUF file to specified quantization."""
    output_file = output_dir / f"micropython-expert-7b-{quant_type}.gguf"

    if output_file.exists():
        logger.info(f"Quantized file already exists: {output_file}")
        return output_file

    logger.info(f"Quantizing to {quant_type}...")

    # Find quantize binary
    quantize_bin = None
    for name in ["llama-quantize", "quantize"]:
        for search_dir in [llama_cpp, llama_cpp / "build" / "bin", llama_cpp / "build"]:
            candidate = search_dir / name
            if candidate.exists():
                quantize_bin = candidate
                break
        if quantize_bin:
            break

    if not quantize_bin:
        raise RuntimeError(
            "llama-quantize not found. Build llama.cpp with: cd llama.cpp && make"
        )

    cmd = [str(quantize_bin), str(input_file), str(output_file), quant_type.upper()]

    logger.info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"Quantization failed: {result.stderr}")
        raise RuntimeError(f"Quantization to {quant_type} failed")

    # Log file size
    size_gb = output_file.stat().st_size / 1e9
    logger.info(f"Created: {output_file} ({size_gb:.2f} GB)")

    return output_file


def main():
    parser = argparse.ArgumentParser(description="Convert model to GGUF format")
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Input merged model directory",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output directory for GGUF files",
    )
    parser.add_argument(
        "--llama-cpp",
        type=Path,
        default=None,
        help="Path to llama.cpp directory",
    )
    parser.add_argument(
        "--quantizations",
        nargs="+",
        default=DEFAULT_QUANTS,
        choices=list(QUANTIZATIONS.keys()),
        help="Quantization types to create",
    )
    parser.add_argument(
        "--list-quants",
        action="store_true",
        help="List available quantization types and exit",
    )
    args = parser.parse_args()

    if args.list_quants:
        print("\nAvailable quantizations:\n")
        for name, info in QUANTIZATIONS.items():
            print(f"  {name:10s} ~{info['size_gb']:.1f} GB  {info['description']}")
        print()
        return

    # Find llama.cpp
    llama_cpp = args.llama_cpp or find_llama_cpp()
    if not llama_cpp:
        logger.error(
            "llama.cpp not found. Please clone and build it:\n"
            "  git clone https://github.com/ggerganov/llama.cpp\n"
            "  cd llama.cpp && make\n"
            "Or specify path with --llama-cpp"
        )
        sys.exit(1)

    logger.info(f"Using llama.cpp at: {llama_cpp}")

    # Check input exists
    if not args.input.exists():
        logger.error(f"Input model not found: {args.input}")
        logger.error("Run scripts/merge_lora.py first to create merged model")
        sys.exit(1)

    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)

    # Convert to f16 GGUF first
    f16_file = convert_to_gguf_f16(args.input, args.output, llama_cpp)

    # Create requested quantizations
    created_files = []
    for quant in args.quantizations:
        if quant == "f16":
            created_files.append(f16_file)
            continue

        try:
            output_file = quantize_gguf(f16_file, args.output, quant, llama_cpp)
            created_files.append(output_file)
        except Exception as e:
            logger.error(f"Failed to create {quant}: {e}")

    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("Conversion complete! Created files:")
    for f in created_files:
        size_gb = f.stat().st_size / 1e9
        logger.info(f"  {f.name}: {size_gb:.2f} GB")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
