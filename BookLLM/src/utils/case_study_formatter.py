class CaseStudyFormatter:
    """Render case studies inside a Markdown box."""

    @staticmethod
    def format(text: str) -> str:
        lines = text.strip().splitlines()
        block = ["> **Case Study**", ">"]
        for line in lines:
            block.append("> " + line.strip())
        return "\n".join(block)
