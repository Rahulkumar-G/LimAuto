from typing import Dict, List

from ...models.state import BookState
from ..base import BaseAgent


class ProofreaderAgent(BaseAgent):
    """Enhanced proofreading agent for content refinement"""

    def _execute_logic(self, state: BookState) -> BookState:
        """Detailed proofreading and corrections"""
        for chapter_title, content in state.chapter_map.items():
            try:
                corrected_content = self._proofread_chapter(
                    chapter_title, content, state
                )
                state.chapter_map[chapter_title] = corrected_content
            except Exception as e:
                self.logger.warning(f"Proofreading failed for {chapter_title}: {e}")

        return state

    def _proofread_chapter(self, title: str, content: str, state: BookState) -> str:
        """Proofread individual chapter content"""
        prompt = f"""
        Proofread and improve this chapter content.
        
        Check for:
        1. Grammar and spelling
        2. Punctuation and formatting
        3. Technical term consistency
        4. Sentence structure and flow
        5. Style consistency ({state.book_style})
        6. Audience appropriateness ({state.target_audience})
        
        Content to proofread:
        {content[:2000]}...
        
        Return the corrected version maintaining technical accuracy.
        """

        corrected_content, _ = self.llm.call_llm(prompt)
        return corrected_content

    def _check_technical_terms(
        self, content: str, glossary: Dict[str, str]
    ) -> List[str]:
        """Verify technical term usage consistency"""
        issues = []
        for term, definition in glossary.items():
            if term.lower() in content.lower():
                # Check for consistent usage
                term_count = content.lower().count(term.lower())
                if term_count > 1:
                    # Verify consistent capitalization and formatting
                    variations = self._find_term_variations(content, term)
                    if len(variations) > 1:
                        issues.append(
                            f"Inconsistent usage of term '{term}': {variations}"
                        )
        return issues

    def _find_term_variations(self, content: str, term: str) -> List[str]:
        """Find variations of term usage in content"""
        import re

        pattern = re.compile(f"{term}", re.IGNORECASE)
        return list(set(pattern.findall(content)))
