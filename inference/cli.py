#!/usr/bin/env python3
"""
CLI for interacting with the MicroPython Expert model.

Usage:
    mpy-expert chat                      # Interactive chat mode
    mpy-expert review --diff file.diff   # Review a diff file
    mpy-expert review --pr 12345         # Review a GitHub PR
    mpy-expert ask "How does the GC work?"  # Single question
"""

import sys
from pathlib import Path

import click
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Default model path
DEFAULT_MODEL = Path(__file__).parent.parent / "models" / "micropython-expert-8b"

# System prompts
SYSTEM_PROMPTS = {
    "general": """You are an expert MicroPython developer with deep knowledge of the codebase and all 22 ports. You provide accurate, practical guidance on both core development and application programming.""",

    "review": """You are an expert MicroPython code reviewer with deep knowledge of the codebase. Your reviews are concise, technically precise, and focus on correctness, performance, and maintainability. You write in a direct, no-nonsense style.""",

    "architecture": """You are a MicroPython core developer explaining the internal architecture. Provide detailed, accurate explanations grounded in the actual codebase structure.""",
}


def load_model(model_path: str):
    """Load the model and tokenizer."""
    click.echo(f"Loading model from {model_path}...")

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


def generate_response(
    model,
    tokenizer,
    messages: list,
    max_new_tokens: int = 1024,
    temperature: float = 0.7,
    stream: bool = True,
) -> str:
    """Generate a response from the model."""
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)

    if stream:
        # Streaming generation
        from transformers import TextIteratorStreamer
        from threading import Thread

        streamer = TextIteratorStreamer(tokenizer, skip_special_tokens=True)
        generation_kwargs = dict(
            inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=temperature > 0,
            streamer=streamer,
            pad_token_id=tokenizer.pad_token_id,
        )

        thread = Thread(target=model.generate, kwargs=generation_kwargs)
        thread.start()

        generated_text = ""
        for new_text in streamer:
            click.echo(new_text, nl=False)
            generated_text += new_text

        thread.join()
        click.echo()  # Newline at end
        return generated_text
    else:
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                pad_token_id=tokenizer.pad_token_id,
            )
        response = tokenizer.decode(
            outputs[0][inputs.input_ids.shape[1]:],
            skip_special_tokens=True
        )
        return response.strip()


@click.group()
@click.option("--model", "-m", default=None, help="Path to model directory")
@click.pass_context
def main(ctx, model):
    """MicroPython Expert CLI - AI assistant for MicroPython development."""
    ctx.ensure_object(dict)
    ctx.obj["model_path"] = model or str(DEFAULT_MODEL)


@main.command()
@click.pass_context
def chat(ctx):
    """Interactive chat mode."""
    model_path = ctx.obj["model_path"]

    if not Path(model_path).exists():
        click.echo(f"Model not found at {model_path}")
        click.echo("Train the model first or specify --model path")
        sys.exit(1)

    model, tokenizer = load_model(model_path)

    messages = [{"role": "system", "content": SYSTEM_PROMPTS["general"]}]

    click.echo("MicroPython Expert - Interactive Mode")
    click.echo("Type 'quit' to exit, 'clear' to reset conversation")
    click.echo("-" * 40)

    while True:
        try:
            user_input = click.prompt("\nYou", type=str)
        except (KeyboardInterrupt, EOFError):
            click.echo("\nGoodbye!")
            break

        if user_input.lower() == "quit":
            break
        elif user_input.lower() == "clear":
            messages = [{"role": "system", "content": SYSTEM_PROMPTS["general"]}]
            click.echo("Conversation cleared.")
            continue

        messages.append({"role": "user", "content": user_input})

        click.echo("\nAssistant: ", nl=False)
        response = generate_response(model, tokenizer, messages)
        messages.append({"role": "assistant", "content": response})


@main.command()
@click.option("--diff", "-d", type=click.Path(exists=True), help="Path to diff file")
@click.option("--pr", "-p", type=int, help="GitHub PR number to review")
@click.option("--stdin", is_flag=True, help="Read diff from stdin")
@click.pass_context
def review(ctx, diff, pr, stdin):
    """Review code changes."""
    model_path = ctx.obj["model_path"]

    if not Path(model_path).exists():
        click.echo(f"Model not found at {model_path}")
        sys.exit(1)

    # Get diff content
    if stdin:
        diff_content = sys.stdin.read()
    elif diff:
        with open(diff) as f:
            diff_content = f.read()
    elif pr:
        import subprocess
        result = subprocess.run(
            ["gh", "pr", "diff", str(pr), "--repo", "micropython/micropython"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            click.echo(f"Error fetching PR: {result.stderr}")
            sys.exit(1)
        diff_content = result.stdout
    else:
        click.echo("Specify --diff, --pr, or --stdin")
        sys.exit(1)

    model, tokenizer = load_model(model_path)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPTS["review"]},
        {"role": "user", "content": f"Review the following code changes:\n\n```diff\n{diff_content}\n```\n\nProvide specific, actionable feedback."},
    ]

    click.echo("Review:\n")
    generate_response(model, tokenizer, messages)


@main.command()
@click.argument("question")
@click.option("--mode", "-m", type=click.Choice(["general", "review", "architecture"]), default="general")
@click.pass_context
def ask(ctx, question, mode):
    """Ask a single question."""
    model_path = ctx.obj["model_path"]

    if not Path(model_path).exists():
        click.echo(f"Model not found at {model_path}")
        sys.exit(1)

    model, tokenizer = load_model(model_path)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPTS[mode]},
        {"role": "user", "content": question},
    ]

    generate_response(model, tokenizer, messages)


if __name__ == "__main__":
    main()
