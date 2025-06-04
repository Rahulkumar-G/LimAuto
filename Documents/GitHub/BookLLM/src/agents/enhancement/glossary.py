from typing import Dict
from ..base import BaseAgent
from ...models.state import BookState
from ...models.agent_type import AgentType
import json

class GlossaryAgent(BaseAgent):
    """Generate comprehensive glossary terms and definitions"""
    
    def __init__(self, llm, agent_type: AgentType = AgentType.ENHANCER):
        super().__init__(llm, agent_type)

    def _execute_logic(self, state: BookState) -> BookState:
        all_content = "\n\n".join(state.chapter_map.values())
        
        prompt = f"""
        Extract and define technical terms from this {state.topic} content.
        Content preview: {all_content[:2000]}...
        
        Generate JSON with:
        - Key: technical term
        - Value: clear definition (30-50 words)
        Focus on {state.target_audience} comprehension level.
        Include common industry terms and concepts.
        """
        
        try:
            response, _ = self.llm.call_llm(prompt, json_mode=True)
            state.glossary = json.loads(response)
            self.logger.info(f"Generated glossary with {len(state.glossary)} terms")
        except Exception as e:
            self.logger.warning(f"Glossary generation failed: {e}")
            state.warnings.append(f"Glossary incomplete: {str(e)}")
        return state


class AcronymAgent(BaseAgent):
    """Extract and expand acronyms from content"""
    
    def __init__(self, llm, agent_type: AgentType = AgentType.ENHANCER):
        super().__init__(llm, agent_type)

    def _execute_logic(self, state: BookState) -> BookState:
        content_sample = "\n\n".join(list(state.chapter_map.values())[:3])
        
        prompt = f"""
        Extract acronyms and abbreviations from:
        {content_sample[:1500]}...
        
        Return JSON:
        - Key: acronym/abbreviation
        - Value: full expansion
        Include standard {state.topic} terminology.
        """
        
        try:
            response, _ = self.llm.call_llm(prompt, json_mode=True)
            state.acronyms = json.loads(response)
            self.logger.info(f"Extracted {len(state.acronyms)} acronyms")
        except Exception as e:
            self.logger.warning(f"Acronym extraction failed: {e}")
            state.warnings.append("Acronym processing incomplete")
        return state