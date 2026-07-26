"""CI regression tests for the Northwind agent prompt.

Run on every prompt PR: a prompt change is a deploy.
"""

from pathlib import Path

from prompt_loader import WORD_BUDGET, load_prompt

PROMPT_DIR = Path(__file__).parent / "prompts" / "northwind_agent"


def test_sections_assemble():
    # load_prompt raises FileNotFoundError if any required section is missing
    assert load_prompt(PROMPT_DIR)


def test_word_budget_respected():
    words = len(load_prompt(PROMPT_DIR).split())
    assert words <= WORD_BUDGET, f"prompt is {words} words; budget is {WORD_BUDGET}"


def test_delivery_date_invariant_present():
    # The root cause of the book's Chapter 1 incident, fossilized as an assertion:
    # eligibility is computed from the delivery date, never the order date.
    text = load_prompt(PROMPT_DIR).lower()
    assert "delivery date" in text


def test_precedence_statement_present():
    # The instruction-hierarchy seatbelt from Chapter 4, "The Instruction Hierarchy".
    text = load_prompt(PROMPT_DIR).lower()
    assert "never instructions to you" in text
