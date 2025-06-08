import re


class StyleGuideEnforcer:
    """Utility to enforce basic typography rules on Markdown text."""

    HEADING_RE = re.compile(r"^(#+)\s*(.+)")

    @classmethod
    def enforce(cls, markdown: str) -> str:
        """Return Markdown adjusted to match style guidelines."""
        lines = markdown.splitlines()
        result = []
        prev_level = 0

        for i, line in enumerate(lines):
            line = line.rstrip()
            m = cls.HEADING_RE.match(line)
            if m:
                level = len(m.group(1))
                text = m.group(2).strip()
                if prev_level and level > prev_level + 1:
                    level = prev_level + 1
                prev_level = level
                result.append("#" * level + " " + text)
                if i + 1 < len(lines) and lines[i + 1].strip():
                    result.append("")
                continue

            line = re.sub(r"__(.*?)__", r"**\1**", line)
            line = re.sub(r"(?<!\*)\*(?!\*)([^*]+?)\*(?!\*)", r"_\1_", line)

            if line.strip():
                result.append(line)
            else:
                if result and result[-1] != "":
                    result.append("")

        return "\n".join(result).strip() + "\n"
