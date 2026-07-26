"""Assemble a system prompt from versioned section files.

A system prompt is an assembled, versioned artifact, not a textbox.
Accompanies Chapter 4, "Prompts as Code".
"""

from pathlib import Path

SECTIONS = ["role", "constraints", "tool_guidance", "output_contract"]
WORD_BUDGET = 800


def load_prompt(prompt_dir: str | Path) -> str:
    """Concatenate the required section files, failing loudly on any gap."""
    parts = []
    for name in SECTIONS:
        path = Path(prompt_dir) / f"{name}.md"
        if not path.exists():
            raise FileNotFoundError(f"required prompt section missing: {name}")
        parts.append(path.read_text(encoding="utf-8").strip())
    return "\n\n".join(parts)


if __name__ == "__main__":
    prompt = load_prompt(Path(__file__).parent / "prompts" / "northwind_agent")
    words = len(prompt.split())
    print(prompt)
    print(f"\n--- {words} words (budget: {WORD_BUDGET}) ---")
