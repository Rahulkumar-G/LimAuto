import json
import re
from typing import List, Optional

from ...models.agent_type import AgentType
from ...models.state import BookState
from ..base import BaseAgent


class OutlineAgent(BaseAgent):
    """Generates book outline and chapter structure"""

    def __init__(self, llm, agent_type: AgentType = AgentType.CONTENT_CREATOR):
        super().__init__(llm, agent_type)

    def _execute_logic(self, state: BookState) -> BookState:
        prompt = f"""
        Create a comprehensive book outline for "{state.topic}" targeting {state.target_audience}.
        
        Requirements:
        - 8-12 main chapters
        - Each chapter should build upon previous knowledge
        - Include practical examples and real-world applications
        - Ensure logical flow and progression
        - Consider {state.estimated_pages} pages total length
        
        Return as JSON array of chapter titles.
        """

        response, _ = self.llm.call_llm(prompt, json_mode=True)

        try:
            parsed = json.loads(response)
        except json.JSONDecodeError:
            json_content = self._extract_json_block(response)
            if json_content:
                parsed = json.loads(json_content)
            else:
                parsed = None

        if parsed is not None:
            raw_outline_data = self._extract_outline_data(parsed)
            processed_outline_list = self._process_outline_data(raw_outline_data)

            state.outline = processed_outline_list
            state.chapters = processed_outline_list.copy()
        else:
            # Fallback parsing for non-JSON responses
            state.outline = self._fallback_parsing(response)
            state.chapters = state.outline.copy()

        self.logger.info(f"Generated outline with {len(state.outline)} chapters")
        return state

    def _extract_outline_data(self, parsed_data: dict) -> List[str]:
        """Extract outline data from parsed JSON"""
        if isinstance(parsed_data, list):
            return parsed_data
        elif isinstance(parsed_data, dict):
            return parsed_data.get("bookOutline", list(parsed_data.values()))
        return []

    def _process_outline_data(self, raw_data: List) -> List[str]:
        """Process and sanitize outline data"""
        processed_list = []
        for item in raw_data:
            if isinstance(item, str):
                processed_list.append(item)
            else:
                try:
                    processed_list.append(str(item))
                except Exception:
                    continue
        return processed_list

    def _extract_json_block(self, response: str) -> Optional[str]:
        """Attempt to extract a JSON block from an LLM response."""
        code_block = re.search(r"```(?:json)?\n(.*?)```", response, re.DOTALL)
        if code_block:
            return code_block.group(1)
        match = re.search(r"({.*})", response, re.DOTALL)
        return match.group(1) if match else None

    def _fallback_parsing(self, response: str) -> List[str]:
        """Fallback parsing for non-JSON responses"""
        lines = [line.strip() for line in response.split("\n") if line.strip()]
        cleaned = [
            line
            for line in lines
            if not line.startswith("```") and line not in {"{", "}", "[", "]"}
        ]
        return [line.lstrip("0123456789.- ").strip() for line in cleaned if line]
