#!/usr/bin/env python3
"""
Create Ollama model from GGUF file.

Generates a Modelfile with appropriate system prompt and imports into Ollama.

Usage:
    python scripts/create_ollama_model.py
    python scripts/create_ollama_model.py --gguf ./models/gguf/micropython-expert-7b-q4_k_m.gguf
    python scripts/create_ollama_model.py --name micropython-expert:q4
"""

import argparse
import logging
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
DEFAULT_GGUF_DIR = PROJECT_ROOT / "models" / "gguf"

SYSTEM_PROMPT = """You are MicroPython Expert, a specialized AI assistant for MicroPython development and code review.

Your expertise includes:
- MicroPython core implementation (py/, extmod/)
- Port-specific code (ESP32, STM32, RP2, Unix, etc.)
- Hardware abstraction (machine module, GPIO, I2C, SPI, UART, etc.)
- Memory management and optimization for embedded systems
- MicroPython coding style and conventions
- Build system (Makefiles, CMake, board configurations)

When reviewing code:
- Focus on correctness, memory safety, and portability
- Follow MicroPython coding conventions (underscore_case, CAPS for macros)
- Consider resource constraints of embedded targets
- Provide specific, actionable feedback
- Reference relevant MicroPython patterns when applicable

When answering questions:
- Be concise and technically precise
- Provide code examples when helpful
- Explain trade-offs for embedded systems
- Reference MicroPython documentation and source when relevant"""

MODELFILE_TEMPLATE = """FROM {gguf_path}

SYSTEM "{system_prompt}"

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_ctx 4096
PARAMETER repeat_penalty 1.1

TEMPLATE \"\"\"{{{{ if .System }}}}<|im_start|>system
{{{{ .System }}}}<|im_end|>
{{{{ end }}}}{{{{ if .Prompt }}}}<|im_start|>user
{{{{ .Prompt }}}}<|im_end|>
{{{{ end }}}}<|im_start|>assistant
{{{{ .Response }}}}<|im_end|>
\"\"\"
"""


def find_gguf_files(gguf_dir: Path) -> list[Path]:
    """Find all GGUF files in directory."""
    return sorted(gguf_dir.glob("*.gguf"))


def get_quant_from_filename(filename: str) -> str:
    """Extract quantization type from filename."""
    # micropython-expert-7b-q4_k_m.gguf -> q4_k_m
    parts = filename.replace(".gguf", "").split("-")
    for part in reversed(parts):
        if part.startswith("q") or part == "f16":
            return part
    return "unknown"


def create_modelfile(gguf_path: Path, output_path: Path) -> Path:
    """Create Ollama Modelfile for a GGUF file."""
    # Escape system prompt for inclusion in Modelfile
    escaped_prompt = SYSTEM_PROMPT.replace('"', '\\"').replace("\n", "\\n")

    content = MODELFILE_TEMPLATE.format(
        gguf_path=str(gguf_path.absolute()),
        system_prompt=escaped_prompt,
    )

    modelfile_path = output_path / f"Modelfile.{get_quant_from_filename(gguf_path.name)}"
    modelfile_path.write_text(content)
    logger.info(f"Created: {modelfile_path}")
    return modelfile_path


def import_to_ollama(modelfile_path: Path, model_name: str) -> bool:
    """Import model into Ollama."""
    logger.info(f"Importing to Ollama as: {model_name}")

    cmd = ["ollama", "create", model_name, "-f", str(modelfile_path)]
    logger.info(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            logger.info(f"Successfully imported: {model_name}")
            return True
        else:
            logger.error(f"Import failed: {result.stderr}")
            return False
    except FileNotFoundError:
        logger.warning("Ollama not found. Modelfile created but not imported.")
        logger.info(f"To import manually: ollama create {model_name} -f {modelfile_path}")
        return False
    except subprocess.TimeoutExpired:
        logger.error("Import timed out")
        return False


def main():
    parser = argparse.ArgumentParser(description="Create Ollama model from GGUF")
    parser.add_argument(
        "--gguf",
        type=Path,
        default=None,
        help="Specific GGUF file to import (default: all in gguf dir)",
    )
    parser.add_argument(
        "--gguf-dir",
        type=Path,
        default=DEFAULT_GGUF_DIR,
        help="Directory containing GGUF files",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="micropython-expert",
        help="Base model name for Ollama",
    )
    parser.add_argument(
        "--no-import",
        action="store_true",
        help="Only create Modelfiles, don't import to Ollama",
    )
    parser.add_argument(
        "--quant",
        type=str,
        default="q4_k_m",
        help="Quantization to import (when --gguf not specified)",
    )
    args = parser.parse_args()

    # Determine which GGUF files to process
    if args.gguf:
        if not args.gguf.exists():
            logger.error(f"GGUF file not found: {args.gguf}")
            sys.exit(1)
        gguf_files = [args.gguf]
    else:
        gguf_files = find_gguf_files(args.gguf_dir)
        if not gguf_files:
            logger.error(f"No GGUF files found in: {args.gguf_dir}")
            logger.error("Run scripts/convert_to_gguf.py first")
            sys.exit(1)

    # Create output directory for Modelfiles
    modelfile_dir = args.gguf_dir / "modelfiles"
    modelfile_dir.mkdir(exist_ok=True)

    # Process each GGUF file
    created = []
    for gguf_file in gguf_files:
        quant = get_quant_from_filename(gguf_file.name)
        logger.info(f"\nProcessing: {gguf_file.name} ({quant})")

        modelfile_path = create_modelfile(gguf_file, modelfile_dir)
        created.append((gguf_file, modelfile_path, quant))

    # Import to Ollama if requested
    if not args.no_import:
        # Import only the requested quantization by default
        for gguf_file, modelfile_path, quant in created:
            if args.gguf or quant == args.quant:
                model_name = f"{args.name}:{quant.replace('_', '-')}"
                import_to_ollama(modelfile_path, model_name)

    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("Created Modelfiles:")
    for gguf_file, modelfile_path, quant in created:
        logger.info(f"  {modelfile_path.name}")

    logger.info("\nTo import a model manually:")
    logger.info(f"  ollama create micropython-expert:TAG -f {modelfile_dir}/Modelfile.TAG")

    logger.info("\nTo test after import:")
    logger.info(f"  ollama run {args.name}:q4-k-m 'Explain how MicroPython gc works'")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
