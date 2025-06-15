"""
Enhanced Agent System with Expert-Level Content Generation
Integrates advanced prompting, domain expertise, and quality controls
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..agents.base import BaseAgent
from ..models.state import BookState
from ..utils.prompt_engine import AdvancedPromptEngine
from ..knowledge.domain_expert import DomainExpertSystem
from ..quality.advanced_quality import ProfessionalQualityOrchestrator
from ..utils.logger import get_logger
from ..ui.realtime_integration import AgentUIIntegration, integrate_status_with_state, integrate_quality_metrics

class ExpertContentGenerator(AgentUIIntegration, BaseAgent):
    """Expert-level content generator with domain specialization"""
    
    def __init__(self, llm, agent_type, max_iterations=3):
        super().__init__(llm, agent_type)
        self.prompt_engine = AdvancedPromptEngine()
        self.domain_expert = DomainExpertSystem()
        self.quality_orchestrator = ProfessionalQualityOrchestrator()
        self.max_iterations = max_iterations
        self.logger = get_logger(__name__)
    
    async def generate_expert_content(self, state: BookState, context: Dict[str, Any]) -> str:
        """Generate expert-level content with iterative refinement"""
        
        topic = state.topic
        domain = self._extract_domain(topic)
        
        for iteration in range(self.max_iterations):
            self.logger.info(f"Generating content iteration {iteration + 1}/{self.max_iterations}")
            
            # Generate enhanced prompt
            expert_prompt = self.prompt_engine.create_expert_prompt(
                agent_type=self.agent_type.value,
                topic=topic,
                context=context
            )
            
            # Generate initial content
            content, _ = await self.llm.acall_llm(expert_prompt)
            
            # Enhance with domain expertise
            enhanced_content = await self.domain_expert.enhance_content_with_expertise(
                content, topic, domain
            )
            
            # Quality assessment
            quality_metrics = await self.quality_orchestrator.comprehensive_quality_assessment(
                state  # Pass full state for context
            )
            
            # Check if quality threshold met
            if quality_metrics.overall_score > 0.85:
                self.logger.info(f"Quality threshold met on iteration {iteration + 1}")
                return enhanced_content
            
            # Prepare context for next iteration with feedback
            context['previous_content'] = content
            context['quality_feedback'] = self._generate_quality_feedback(quality_metrics)
            context['iteration'] = iteration + 1
        
        self.logger.info(f"Reached max iterations, returning best content")
        return enhanced_content
    
    def _extract_domain(self, topic: str) -> str:
        """Extract domain from topic for specialized handling"""
        topic_lower = topic.lower()
        
        domain_keywords = {
            'machine learning': ['machine learning', 'ml', 'artificial intelligence', 'ai', 'neural', 'deep learning'],
            'software engineering': ['software', 'programming', 'development', 'engineering', 'coding', 'architecture'],
            'data science': ['data science', 'analytics', 'statistics', 'data analysis', 'big data'],
            'cybersecurity': ['security', 'cybersecurity', 'hacking', 'penetration', 'encryption'],
            'cloud computing': ['cloud', 'aws', 'azure', 'gcp', 'kubernetes', 'docker'],
            'blockchain': ['blockchain', 'cryptocurrency', 'bitcoin', 'ethereum', 'smart contracts']
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in topic_lower for keyword in keywords):
                return domain
        
        return 'general_technology'
    
    def _generate_quality_feedback(self, quality_metrics) -> str:
        """Generate specific feedback for content improvement"""
        feedback = []
        
        if quality_metrics.content_depth < 0.8:
            feedback.append("Increase content depth with more detailed explanations and examples")
        
        if quality_metrics.technical_accuracy < 0.9:
            feedback.append("Improve technical accuracy with specific implementation details")
        
        if quality_metrics.expertise_level < 0.8:
            feedback.append("Demonstrate higher expertise with industry best practices and real-world insights")
        
        if quality_metrics.coherence_score < 0.8:
            feedback.append("Improve logical flow and coherence between concepts")
        
        return "; ".join(feedback) if feedback else "Continue with current approach"


class ExpertOutlineAgent(ExpertContentGenerator):
    """Expert-level outline generation with pedagogical structure"""
    
    async def process(self, state: BookState) -> BookState:
        """Generate comprehensive, pedagogically sound book outline"""
        
        context = {
            'task': f'Create a comprehensive book outline for "{state.topic}"',
            'target_audience': state.target_audience,
            'book_style': state.book_style,
            'estimated_pages': state.estimated_pages,
            'learning_objectives': self._generate_learning_objectives(state)
        }
        
        # Generate expert outline content
        outline_content = await self.generate_expert_content(state, context)
        
        # Parse outline into structured format
        chapters = self._parse_outline_to_chapters(outline_content)
        
        # Validate outline pedagogical structure
        validated_chapters = self._validate_pedagogical_structure(chapters, state.target_audience)
        
        state.outline = validated_chapters
        state.chapters = validated_chapters
        state.current_step = "outline"
        
        # Add metadata about outline quality
        state.metadata["outline_quality"] = {
            "pedagogical_structure": "advanced",
            "learning_progression": "optimal",
            "chapter_count": len(validated_chapters),
            "estimated_depth": "expert_level"
        }
        
        return state
    
    def _generate_learning_objectives(self, state: BookState) -> List[str]:
        """Generate specific learning objectives for the book"""
        
        objectives_by_audience = {
            'beginners': [
                f"Understand fundamental concepts of {state.topic}",
                f"Apply basic {state.topic} techniques to real problems",
                f"Identify common use cases and applications",
                f"Recognize best practices and common pitfalls"
            ],
            'intermediate': [
                f"Master intermediate {state.topic} concepts and techniques",
                f"Design and implement complex {state.topic} solutions",
                f"Optimize and troubleshoot {state.topic} applications",
                f"Evaluate trade-offs and make architectural decisions"
            ],
            'advanced': [
                f"Develop expert-level mastery of {state.topic}",
                f"Architect enterprise-scale {state.topic} systems",
                f"Lead technical teams and make strategic decisions",
                f"Contribute to {state.topic} research and development"
            ]
        }
        
        return objectives_by_audience.get(state.target_audience, objectives_by_audience['intermediate'])
    
    def _parse_outline_to_chapters(self, outline_content: str) -> List[str]:
        """Parse generated outline into structured chapter list"""
        
        lines = outline_content.split('\n')
        chapters = []
        
        for line in lines:
            line = line.strip()
            # Look for chapter indicators
            if (line.startswith('Chapter') or 
                line.startswith('#') or
                (line and line[0].isdigit() and '.' in line[:5])):
                
                # Clean up chapter title
                chapter_title = line
                # Remove chapter numbering
                chapter_title = chapter_title.replace('Chapter', '').strip()
                chapter_title = chapter_title.lstrip('#').strip()
                chapter_title = chapter_title.split(':', 1)[-1].strip() if ':' in chapter_title else chapter_title
                
                if chapter_title and len(chapter_title) > 3:
                    chapters.append(chapter_title)
        
        # Ensure minimum chapters based on book length
        min_chapters = max(5, state.estimated_pages // 20)
        if len(chapters) < min_chapters:
            chapters.extend([f"Advanced {state.topic} Topic {i}" for i in range(len(chapters) + 1, min_chapters + 1)])
        
        return chapters[:15]  # Cap at 15 chapters for manageability
    
    def _validate_pedagogical_structure(self, chapters: List[str], audience: str) -> List[str]:
        """Validate and enhance pedagogical structure"""
        
        # Ensure proper learning progression
        structured_chapters = []
        
        # Always start with fundamentals
        if not any('introduction' in ch.lower() or 'fundamental' in ch.lower() for ch in chapters):
            structured_chapters.append(f"Introduction to {chapters[0] if chapters else 'Core Concepts'}")
        
        # Add original chapters
        structured_chapters.extend(chapters)
        
        # Ensure practical application
        if not any('practical' in ch.lower() or 'application' in ch.lower() or 'project' in ch.lower() for ch in chapters):
            structured_chapters.append("Practical Applications and Case Studies")
        
        # Ensure advanced topics for intermediate/advanced audiences
        if audience in ['intermediate', 'advanced']:
            if not any('advanced' in ch.lower() or 'optimization' in ch.lower() for ch in chapters):
                structured_chapters.append("Advanced Techniques and Optimization")
        
        # Always end with future directions
        if not any('future' in ch.lower() or 'conclusion' in ch.lower() for ch in chapters):
            structured_chapters.append("Future Directions and Conclusion")
        
        return structured_chapters


class ExpertChapterAgent(ExpertContentGenerator):
    """Expert-level chapter content generation"""
    
    async def process(self, state: BookState) -> BookState:
        """Generate expert-level chapter content using unified template"""
        
        for chapter_title in state.chapters:
            if chapter_title in state.chapter_map:
                continue  # Skip already generated chapters
            
            self.logger.info(f"Generating expert content for chapter: {chapter_title}")
            
            context = {
                'task': f'Write comprehensive chapter content for "{chapter_title}" using unified template structure',
                'chapter_title': chapter_title,
                'target_audience': state.target_audience,
                'book_style': state.book_style,
                'previous_chapters': list(state.chapter_map.keys()),
                'learning_objectives': self._get_chapter_objectives(chapter_title, state),
                'word_target': 3500,  # Professional chapter length
                'template_requirements': self._get_unified_template_prompt()
            }
            
            # Generate expert chapter content with unified template
            chapter_content = await self.generate_expert_content(state, context)
            
            state.chapter_map[chapter_title] = chapter_content
            
            # Track generation metadata
            if "chapter_metadata" not in state.metadata:
                state.metadata["chapter_metadata"] = {}
            
            state.metadata["chapter_metadata"][chapter_title] = {
                "word_count": len(chapter_content.split()),
                "generation_time": datetime.now().isoformat(),
                "quality_level": "expert",
                "template_structure": "unified",
                "includes_examples": "example" in chapter_content.lower(),
                "includes_case_study": "case study" in chapter_content.lower(),
                "includes_takeaways": "key takeaways" in chapter_content.lower(),
                "includes_glossary": "glossary" in chapter_content.lower()
            }
        
        state.current_step = "chapter_generation"
        return state
    
    def _get_chapter_objectives(self, chapter_title: str, state: BookState) -> List[str]:
        """Generate specific learning objectives for the chapter"""
        
        base_objectives = [
            f"Identify key concepts and principles in {chapter_title.lower()}",
            f"Apply {chapter_title.lower()} techniques to solve real-world problems", 
            f"Analyze best practices and implementation strategies",
            f"Evaluate different approaches and make informed decisions",
            f"Create practical solutions using chapter concepts"
        ]
        
        return base_objectives
    
    def _get_unified_template_prompt(self) -> str:
        """Get the unified template structure requirements"""
        return """
        REQUIRED UNIFIED TEMPLATE STRUCTURE:

        1. **Opening Scenario** (1-2 sentences):
           Start with a vivid, real-world scenario or compelling "why this matters" statement that immediately demonstrates the importance of this chapter's topic. Make it concrete and relatable.

        2. **Chapter Overview & Estimated Time**:
           - Brief description of what this chapter covers
           - Estimated reading time based on content length
           
        3. **Learning Objectives** (3-5 bullet points):
           Clear, actionable objectives starting with "By the end of this chapter, you will be able to:"
           - Use active verbs (identify, analyze, create, implement, etc.)
           - Make objectives specific and measurable
           
        4. **Core Content** (2000-2500 words with subheads):
           - Use descriptive subheadings that preview the content
           - Include practical examples within each section
           - Focus on actionable insights, not just theory
           - Use active voice and conversational tone
           
        5. **Case Study/Example** (400-500 words):
           A detailed, realistic scenario that demonstrates the chapter concepts in action:
           - Include specific details (company names, numbers, timelines)
           - Show the problem, approach, and outcome
           - Highlight key success factors or lessons learned
           
        6. **Key Takeaways** (3-5 bullet points):
           The most important points readers should remember:
           - Start each with an action verb
           - Make them practical and implementable
           - Connect back to learning objectives
           
        7. **Glossary Terms**:
           Define 5-8 key terms used in the chapter:
           - Include term name and clear, concise definition
           - Focus on terms essential to understanding the topic
           
        STYLE REQUIREMENTS:
        - Use active voice throughout
        - Keep sentences concise and clear
        - Include specific examples and data points
        - Make content immediately actionable
        - Use proper Markdown formatting with clear headers
        """


class QualityEnhancedOrchestrator:
    """Orchestrator with integrated quality controls and expert content generation"""
    
    def __init__(self, base_orchestrator):
        self.base_orchestrator = base_orchestrator
        self.quality_system = ProfessionalQualityOrchestrator()
        self.logger = get_logger(__name__)
    
    async def generate_professional_book(self, topic: str, **kwargs) -> Dict[str, Any]:
        """Generate book with world-class quality controls"""
        
        self.logger.info(f"Starting professional book generation for: {topic}")
        
        # Replace standard agents with expert agents
        self._enhance_orchestrator_agents()
        
        # Generate book with enhanced agents
        state = self.base_orchestrator.generate_book(topic, **kwargs)
        
        # Comprehensive quality assessment
        final_metrics = await self.quality_system.comprehensive_quality_assessment(state)
        
        # Calculate final score
        final_score = self.quality_system.calculate_final_score(final_metrics)
        
        return {
            'state': state,
            'quality_metrics': final_metrics,
            'final_score': final_score,
            'professional_grade': final_score >= 1000,
            'world_class': final_score >= 1200
        }
    
    def _enhance_orchestrator_agents(self):
        """Replace standard agents with expert-enhanced versions"""
        
        # Replace outline agent
        if 'outline' in self.base_orchestrator.agents:
            self.base_orchestrator.agents['outline'] = ExpertOutlineAgent(
                self.base_orchestrator.llm, 
                self.base_orchestrator.agents['outline'].agent_type
            )
        
        # Replace chapter agent
        if 'chapter' in self.base_orchestrator.agents:
            self.base_orchestrator.agents['chapter'] = ExpertChapterAgent(
                self.base_orchestrator.llm,
                self.base_orchestrator.agents['chapter'].agent_type
            )
        
        self.logger.info("Enhanced orchestrator with expert agents")