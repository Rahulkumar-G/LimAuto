import json
from typing import List
from ..base import BaseAgent
from ...models.state import BookState
from ...models.agent_type import AgentType

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
            raw_outline_data = self._extract_outline_data(parsed)
            processed_outline_list = self._process_outline_data(raw_outline_data)
            
            state.outline = processed_outline_list
            state.chapters = processed_outline_list.copy()
            
        except json.JSONDecodeError:
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
    
    def _fallback_parsing(self, response: str) -> List[str]:
        """Fallback parsing for non-JSON responses"""
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        return [line.lstrip('0123456789.-').strip() for line in lines if line]