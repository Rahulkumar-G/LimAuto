from ...models.agent_type import AgentType
from ...models.state import BookState
from ..base import BaseAgent


class CodeSampleAgent(BaseAgent):
    """Generate and enhance code samples"""

    def __init__(self, llm, agent_type: AgentType = AgentType.ENHANCER):
        super().__init__(llm, agent_type)

    def _execute_logic(self, state: BookState) -> BookState:
        for chapter_title, content in state.chapter_map.items():
            if self._needs_code_samples(content):
                self._generate_chapter_code_samples(state, chapter_title, content)
        return state

    def _needs_code_samples(self, content: str) -> bool:
        """Check if content would benefit from code samples"""
        technical_indicators = [
            "code",
            "programming",
            "implementation",
            "function",
            "class",
            "algorithm",
            "example",
            "demonstration",
            "snippet",
        ]
        return any(indicator in content.lower() for indicator in technical_indicators)

    def _generate_chapter_code_samples(
        self, state: BookState, chapter_title: str, content: str
    ):
        """Generate code samples for a specific chapter"""
        prompt = f"""
        Create practical code examples for chapter "{chapter_title}".
        
        Context:
        - Topic: {state.topic}
        - Audience: {state.target_audience}
        - Chapter content: {content[:1000]}...
        
        Requirements:
        1. Include setup/installation if needed
        2. Add detailed comments explaining each part
        3. Follow best practices
        4. Show practical use cases
        5. Include error handling
        6. Add usage examples
        
        Return response as valid Python code with markdown formatting.
        Use ```python blocks for code sections.
        """

        try:
            code_sample, _ = self.llm.call_llm(prompt)
            state.code_samples[chapter_title] = self._post_process_code(code_sample)
            self.logger.info(f"Generated code samples for {chapter_title}")
        except Exception as e:
            self.logger.error(
                f"Failed to generate code sample for {chapter_title}: {e}"
            )
            state.errors.append(f"Code sample generation failed for {chapter_title}")

    def _post_process_code(self, code: str) -> str:
        """Clean and format code samples"""
        # Remove extra whitespace
        code = code.strip()

        # Ensure proper markdown code block formatting
        if not code.startswith("```python"):
            code = "```python\n" + code
        if not code.endswith("```"):
            code = code + "\n```"

        # Add standard header comment
        header = (
            "# This code sample is generated for educational purposes\n"
            "# Follow best practices and adapt to your specific needs\n\n"
        )

        # Insert header after ```python marker
        code_parts = code.split("\n", 1)
        if len(code_parts) > 1:
            code = code_parts[0] + "\n" + header + code_parts[1]

        return code
