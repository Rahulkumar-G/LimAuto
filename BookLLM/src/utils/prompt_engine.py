from __future__ import annotations


def generate_question(section_heading: str, section_text: str) -> str:
    """Generate a simple comprehension question."""
    return f"What did you learn in {section_heading}?"


def generate_example(topic: str) -> str:
    """Generate a short illustrative example."""
    return f"For instance, {topic.lower()} can be applied in real-world situations."
