from ...models.agent_type import AgentType
from ...models.state import BookState
from ..base import BaseAgent


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
            data = self._parse_json(response)

            # Normalize potential nested structures
            glossary = {}
            if isinstance(data, dict) and "technical_terms" in data:
                items = data.get("technical_terms", [])
                if isinstance(items, list):
                    for entry in items:
                        if isinstance(entry, dict):
                            term = entry.get("key") or entry.get("term")
                            definition = entry.get("value") or entry.get(
                                "definition"
                            )
                            if term and definition:
                                glossary[str(term)] = str(definition)
            elif isinstance(data, list):
                for entry in data:
                    if isinstance(entry, dict):
                        term = entry.get("key") or entry.get("term")
                        definition = entry.get("value") or entry.get(
                            "definition"
                        )
                        if term and definition:
                            glossary[str(term)] = str(definition)
                    elif isinstance(entry, list) and len(entry) == 2:
                        glossary[str(entry[0])] = str(entry[1])
            elif isinstance(data, dict):
                glossary = {str(k): str(v) for k, v in data.items() if isinstance(v, str)}

            if not glossary:
                raise ValueError("Invalid glossary format")

            state.glossary = glossary
            self.logger.info(
                f"Generated glossary with {len(state.glossary)} terms"
            )
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
            state.acronyms = self._parse_json(response)
            self.logger.info(f"Extracted {len(state.acronyms)} acronyms")
        except Exception as e:
            self.logger.warning(f"Acronym extraction failed: {e}")
            state.warnings.append("Acronym processing incomplete")
        return state
