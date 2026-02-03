#!/usr/bin/env python3
"""
Scrape the MicroPython GitHub wiki and convert to training data.

The wiki contains practical guides, board-specific documentation, and
community-maintained content that complements the official docs.

Wiki URL: https://github.com/micropython/micropython/wiki
"""

import json
import re
import subprocess
import time
from pathlib import Path
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
WIKI_DIR = PROJECT_ROOT / "data" / "wiki"
OUTPUT_DIR = PROJECT_ROOT / "data" / "training"

WIKI_BASE_URL = "https://github.com/micropython/micropython/wiki"
WIKI_RAW_BASE = "https://raw.githubusercontent.com/wiki/micropython/micropython"

# Rate limiting
REQUEST_DELAY = 1.0  # seconds between requests


def get_wiki_page_list():
    """Get list of all wiki pages using gh CLI."""
    print("Fetching wiki page list via GitHub API...")

    # Use gh CLI to get wiki pages
    # The wiki is a separate git repo: micropython/micropython.wiki.git
    result = subprocess.run(
        [
            "gh", "api",
            "-H", "Accept: application/vnd.github+json",
            "/repos/micropython/micropython/pages"
        ],
        capture_output=True,
        text=True
    )

    # GitHub doesn't have a direct wiki API, so we'll scrape the sidebar
    print("Scraping wiki sidebar for page list...")
    response = requests.get(WIKI_BASE_URL)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Find wiki page links in the sidebar
    pages = set()

    # Look for wiki links in the page
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "/micropython/micropython/wiki/" in href:
            # Extract page name
            page_name = href.split("/wiki/")[-1]
            if page_name and not page_name.startswith("_"):
                pages.add(page_name)

    # Also add the home page
    pages.add("Home")

    return sorted(pages)


def fetch_wiki_page(page_name):
    """Fetch a single wiki page content."""
    # Try raw markdown first
    raw_url = f"{WIKI_RAW_BASE}/{page_name}.md"
    response = requests.get(raw_url)

    if response.status_code == 200:
        return response.text

    # Fall back to HTML and convert
    html_url = f"{WIKI_BASE_URL}/{page_name}"
    response = requests.get(html_url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Find the wiki content div
    content_div = soup.find("div", class_="markdown-body")
    if content_div:
        # Convert to markdown
        return md(str(content_div))

    return None


def parse_wiki_for_qa(content, page_name):
    """Parse wiki markdown content and generate Q&A pairs."""
    qa_pairs = []

    # Split by headers
    sections = re.split(r'^(#{1,3}\s+.+)$', content, flags=re.MULTILINE)

    current_header = page_name.replace("-", " ").title()
    current_content = []

    for i, section in enumerate(sections):
        if re.match(r'^#{1,3}\s+', section):
            # Process previous section
            if current_content:
                text = "\n".join(current_content).strip()
                if len(text) > 100:  # Skip very short sections
                    qa_pairs.append({
                        "header": current_header,
                        "content": text,
                        "page": page_name,
                    })
            current_header = section.strip("#").strip()
            current_content = []
        else:
            current_content.append(section)

    # Don't forget last section
    if current_content:
        text = "\n".join(current_content).strip()
        if len(text) > 100:
            qa_pairs.append({
                "header": current_header,
                "content": text,
                "page": page_name,
            })

    return qa_pairs


def format_wiki_sft(section):
    """Convert a wiki section to SFT format."""
    # Generate a question based on the header
    header = section["header"]
    content = section["content"]

    # Create natural-sounding questions
    question_templates = [
        f"How do I {header.lower()}?",
        f"Explain {header.lower()} in MicroPython.",
        f"What is the process for {header.lower()}?",
        f"Can you describe {header.lower()}?",
    ]

    # Pick template based on content type
    if any(word in header.lower() for word in ["build", "install", "setup", "compile"]):
        question = f"How do I {header.lower()} for MicroPython?"
    elif any(word in header.lower() for word in ["what", "about", "overview"]):
        question = f"Can you explain {header.lower()}?"
    elif any(word in header.lower() for word in ["troubleshoot", "debug", "error", "problem"]):
        question = f"How do I troubleshoot {header.lower()} in MicroPython?"
    else:
        question = f"Explain {header.lower()} in MicroPython."

    system_prompt = """You are an expert MicroPython developer helping users with practical questions about building, configuring, and using MicroPython. Provide clear, accurate guidance based on real experience with the codebase and various hardware platforms."""

    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
            {"role": "assistant", "content": content},
        ],
        "metadata": {
            "source": "wiki",
            "page": section["page"],
            "header": section["header"],
        },
    }


def scrape_wiki():
    """Main function to scrape wiki and generate training data."""
    WIKI_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Get page list
    pages = get_wiki_page_list()
    print(f"Found {len(pages)} wiki pages")

    # Fetch each page
    all_sections = []
    successful_pages = 0

    for i, page_name in enumerate(pages):
        print(f"[{i+1}/{len(pages)}] Fetching {page_name}...")

        try:
            content = fetch_wiki_page(page_name)
            if content:
                # Save raw markdown
                wiki_path = WIKI_DIR / f"{page_name}.md"
                with open(wiki_path, "w") as f:
                    f.write(content)

                # Parse into sections
                sections = parse_wiki_for_qa(content, page_name)
                all_sections.extend(sections)
                successful_pages += 1
                print(f"  -> {len(sections)} sections extracted")

            time.sleep(REQUEST_DELAY)

        except Exception as e:
            print(f"  -> Error: {e}")
            continue

    print(f"\nSuccessfully fetched {successful_pages}/{len(pages)} pages")
    print(f"Total sections: {len(all_sections)}")

    # Convert to SFT format
    sft_examples = [format_wiki_sft(section) for section in all_sections]

    # Write output
    output_path = OUTPUT_DIR / "wiki_qa.jsonl"
    with open(output_path, "w") as f:
        for ex in sft_examples:
            f.write(json.dumps(ex) + "\n")

    print(f"Wrote {len(sft_examples)} examples to {output_path}")

    # Write summary
    summary = {
        "scraped_at": datetime.now().isoformat(),
        "pages_found": len(pages),
        "pages_fetched": successful_pages,
        "sections_extracted": len(all_sections),
        "sft_examples": len(sft_examples),
    }
    summary_path = OUTPUT_DIR / "wiki_qa_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Wrote summary to {summary_path}")


if __name__ == "__main__":
    scrape_wiki()
