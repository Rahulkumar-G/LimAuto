"""
Domain Expert Knowledge Integration System
DEPRECATED: Replaced by intelligent_knowledge_system.py
This file is kept for backward compatibility
"""

import json
import requests
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import wikipedia
import arxiv
from datetime import datetime, timedelta

from ..utils.logger import get_logger

@dataclass
class KnowledgeSource:
    """Represents a knowledge source with metadata"""
    content: str
    source_type: str  # wikipedia, arxiv, web, expert_knowledge
    url: str
    credibility_score: float
    last_updated: datetime
    domain_relevance: float

@dataclass
class ExpertInsight:
    """Expert-level insight or best practice"""
    topic: str
    insight: str
    category: str  # best_practice, common_pitfall, optimization, architecture
    confidence: float
    source: str
    examples: List[str]

class DomainKnowledgeBase:
    """Comprehensive domain-specific knowledge repository"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.knowledge_cache = {}
        self.expert_insights = self._load_expert_insights()
        self.domain_concepts = self._load_domain_concepts()
        
    def _load_expert_insights(self) -> Dict[str, List[ExpertInsight]]:
        """Load curated expert insights by domain"""
        return {
            'machine_learning': [
                ExpertInsight(
                    topic='gradient_descent_optimization',
                    insight='Learning rate scheduling is crucial for convergence. Start with 0.001 and use cosine annealing or exponential decay. Monitor loss curves and reduce learning rate when plateau detected.',
                    category='best_practice',
                    confidence=0.95,
                    source='Production ML at scale',
                    examples=['ResNet training on ImageNet', 'BERT fine-tuning strategies']
                ),
                ExpertInsight(
                    topic='model_validation',
                    insight='Never trust a single validation metric. Use k-fold cross-validation, stratified sampling for imbalanced datasets, and time-based splits for temporal data.',
                    category='common_pitfall',
                    confidence=0.98,
                    source='MLOps best practices',
                    examples=['Financial time series prediction', 'Medical diagnosis models']
                ),
                ExpertInsight(
                    topic='feature_engineering',
                    insight='Domain knowledge trumps algorithmic sophistication. Spend 80% of time understanding data and creating meaningful features rather than tuning hyperparameters.',
                    category='best_practice',
                    confidence=0.92,
                    source='Kaggle competition strategies',
                    examples=['Customer churn prediction', 'Fraud detection systems']
                )
            ],
            'software_engineering': [
                ExpertInsight(
                    topic='microservices_architecture',
                    insight='Start with a modular monolith and extract microservices only when you have clear service boundaries and team ownership. Premature microservices lead to distributed monoliths.',
                    category='architecture',
                    confidence=0.94,
                    source='Production systems at scale',
                    examples=['Netflix evolution', 'Uber service decomposition']
                ),
                ExpertInsight(
                    topic='database_optimization',
                    insight='Index strategy should be driven by query patterns, not table structure. Use EXPLAIN ANALYZE to understand query execution plans before adding indexes.',
                    category='optimization',
                    confidence=0.96,
                    source='Database performance engineering',
                    examples=['PostgreSQL query optimization', 'MongoDB index strategies']
                ),
                ExpertInsight(
                    topic='error_handling',
                    insight='Fail fast, fail safely. Implement circuit breakers, exponential backoff, and bulkhead isolation. Log errors with sufficient context for debugging but never expose internal details to users.',
                    category='best_practice',
                    confidence=0.97,
                    source='Reliability engineering',
                    examples=['AWS service outages', 'Payment processing systems']
                )
            ],
            'data_science': [
                ExpertInsight(
                    topic='statistical_significance',
                    insight='Statistical significance != practical significance. Always report effect sizes and confidence intervals. Be wary of p-hacking and multiple comparison problems.',
                    category='common_pitfall',
                    confidence=0.95,
                    source='Statistical best practices',
                    examples=['A/B testing interpretation', 'Clinical trial analysis']
                ),
                ExpertInsight(
                    topic='data_visualization',
                    insight='Choose chart types based on data relationships, not aesthetics. Bar charts for comparisons, line charts for trends, scatter plots for correlations. Always include uncertainty measures.',
                    category='best_practice',
                    confidence=0.93,
                    source='Information design principles',
                    examples=['Financial dashboard design', 'Scientific publication plots']
                )
            ]
        }
    
    def _load_domain_concepts(self) -> Dict[str, Dict[str, Any]]:
        """Load domain-specific concept hierarchies"""
        return {
            'machine_learning': {
                'supervised_learning': {
                    'prerequisites': ['statistics', 'linear_algebra'],
                    'subtopics': ['regression', 'classification', 'regularization'],
                    'complexity_level': 'intermediate',
                    'practical_applications': ['prediction', 'forecasting', 'pattern_recognition']
                },
                'deep_learning': {
                    'prerequisites': ['supervised_learning', 'calculus', 'optimization'],
                    'subtopics': ['neural_networks', 'backpropagation', 'architectures'],
                    'complexity_level': 'advanced',
                    'practical_applications': ['computer_vision', 'nlp', 'speech_recognition']
                }
            },
            'software_engineering': {
                'system_design': {
                    'prerequisites': ['algorithms', 'databases', 'networking'],
                    'subtopics': ['scalability', 'reliability', 'consistency'],
                    'complexity_level': 'advanced',
                    'practical_applications': ['distributed_systems', 'microservices', 'cloud_architecture']
                }
            }
        }

class ExternalKnowledgeRetriever:
    """Retrieve and validate knowledge from external sources"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.cache_duration = timedelta(hours=24)
        self.knowledge_cache = {}
    
    async def get_comprehensive_knowledge(self, topic: str, domain: str) -> List[KnowledgeSource]:
        """Retrieve comprehensive knowledge from multiple sources"""
        
        cache_key = f"{domain}_{topic}"
        if cache_key in self.knowledge_cache:
            cached_data, timestamp = self.knowledge_cache[cache_key]
            if datetime.now() - timestamp < self.cache_duration:
                return cached_data

        knowledge_sources = []

        # Retrieve from multiple sources in parallel
        tasks = [
            self._get_wikipedia_knowledge(topic),
            self._get_arxiv_papers(topic, domain),
            self._get_expert_curated_content(topic, domain)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if not isinstance(result, Exception) and result:
                knowledge_sources.extend(result)

        # Cache results
        self.knowledge_cache[cache_key] = (knowledge_sources, datetime.now())

        return knowledge_sources

    async def _get_wikipedia_knowledge(self, topic: str) -> List[KnowledgeSource]:
        """Retrieve relevant Wikipedia articles"""
        try:
            # Search for relevant pages
            search_results = wikipedia.search(topic, results=3)
            sources = []

            for title in search_results:
                try:
                    page = wikipedia.page(title)
                    source = KnowledgeSource(
                        content=page.summary[:2000],  # Limit content length
                        source_type='wikipedia',
                        url=page.url,
                        credibility_score=0.7,  # Wikipedia generally reliable
                        last_updated=datetime.now(),
                        domain_relevance=self._calculate_relevance(topic, page.summary)
                    )
                    sources.append(source)
                except wikipedia.exceptions.DisambiguationError as e:
                    # Try the first disambiguation option
                    try:
                        page = wikipedia.page(e.options[0])
                        source = KnowledgeSource(
                            content=page.summary[:2000],
                            source_type='wikipedia',
                            url=page.url,
                            credibility_score=0.7,
                            last_updated=datetime.now(),
                            domain_relevance=self._calculate_relevance(topic, page.summary)
                        )
                        sources.append(source)
                    except:
                        continue
                except:
                    continue

            return sources

        except Exception as e:
            self.logger.warning(f"Wikipedia retrieval failed for {topic}: {e}")
            return []

    async def _get_arxiv_papers(self, topic: str, domain: str) -> List[KnowledgeSource]:
        """Retrieve relevant arXiv papers for technical topics"""
        try:
            # Search arXiv for recent papers
            search = arxiv.Search(
                query=f"{topic} {domain}",
                max_results=5,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )

            sources = []
            for paper in search.results():
                source = KnowledgeSource(
                    content=paper.summary[:2000],
                    source_type='arxiv',
                    url=paper.entry_id,
                    credibility_score=0.85,  # arXiv papers generally high quality
                    last_updated=paper.updated,
                    domain_relevance=self._calculate_relevance(topic, paper.summary)
                )
                sources.append(source)

            return sources

        except Exception as e:
            self.logger.warning(f"arXiv retrieval failed for {topic}: {e}")
            return []

    async def _get_expert_curated_content(self, topic: str, domain: str) -> List[KnowledgeSource]:
        """Get expert-curated content and best practices"""
        # This would integrate with curated knowledge bases
        # For now, return domain-specific expert insights

        domain_kb = DomainKnowledgeBase()
        insights = domain_kb.expert_insights.get(domain.lower().replace(' ', '_'), [])

        sources = []
        for insight in insights:
            if topic.lower() in insight.topic.lower() or any(topic.lower() in example.lower() for example in insight.examples):
                source = KnowledgeSource(
                    content=f"{insight.insight}\n\nExamples: {'; '.join(insight.examples)}",
                    source_type='expert_knowledge',
                    url=f"expert_insights_{insight.category}",
                    credibility_score=insight.confidence,
                    last_updated=datetime.now(),
                    domain_relevance=0.95  # Expert insights highly relevant
                )
                sources.append(source)

        return sources

    def _calculate_relevance(self, topic: str, content: str) -> float:
        """Calculate domain relevance score based on content overlap"""
        topic_words = set(topic.lower().split())
        content_words = set(content.lower().split())

        if not topic_words:
            return 0.0

        overlap = len(topic_words.intersection(content_words))
        relevance = overlap / len(topic_words)

        return min(relevance, 1.0)

class DomainExpertSystem:
    """Comprehensive domain expertise integration system"""
    
    def __init__(self):
        self.knowledge_base = DomainKnowledgeBase()
        self.knowledge_retriever = ExternalKnowledgeRetriever()
        self.logger = get_logger(__name__)

    async def enhance_content_with_expertise(self, content: str, topic: str, domain: str) -> str:
        """Enhance content with domain expertise and external knowledge"""

        # Get comprehensive knowledge
        knowledge_sources = await self.knowledge_retriever.get_comprehensive_knowledge(topic, domain)

        # Extract relevant insights
        relevant_insights = self._extract_relevant_insights(content, topic, domain)

        # Generate enhancement suggestions
        enhancements = self._generate_enhancements(content, knowledge_sources, relevant_insights)

        # Apply enhancements
        enhanced_content = self._apply_enhancements(content, enhancements)

        return enhanced_content

    def _extract_relevant_insights(self, content: str, topic: str, domain: str) -> List[ExpertInsight]:
        """Extract relevant expert insights for the content"""

        domain_insights = self.knowledge_base.expert_insights.get(domain.lower().replace(' ', '_'), [])
        relevant_insights = []

        content_lower = content.lower()

        for insight in domain_insights:
            # Check if insight is relevant to content
            if (insight.topic.lower() in content_lower or 
                any(keyword in content_lower for keyword in insight.topic.split('_')) or
                any(example.lower() in content_lower for example in insight.examples)):
                relevant_insights.append(insight)

        return relevant_insights

    def _generate_enhancements(self, content: str, knowledge_sources: List[KnowledgeSource], 
                             insights: List[ExpertInsight]) -> List[str]:
        """Generate specific content enhancements"""

        enhancements = []

        # Add expert insights
        for insight in insights:
            if insight.category == 'best_practice':
                enhancement = f"\n\n**Expert Best Practice**: {insight.insight}"
                if insight.examples:
                    enhancement += f"\n\n*Real-world examples*: {', '.join(insight.examples[:2])}"
                enhancements.append(enhancement)

            elif insight.category == 'common_pitfall':
                enhancement = f"\n\n⚠️ **Common Pitfall**: {insight.insight}"
                enhancements.append(enhancement)

            elif insight.category == 'optimization':
                enhancement = f"\n\n🚀 **Performance Optimization**: {insight.insight}"
                enhancements.append(enhancement)

        # Add high-credibility external knowledge
        high_credibility_sources = [s for s in knowledge_sources if s.credibility_score > 0.8]
        for source in high_credibility_sources[:2]:  # Limit to top 2
            if source.source_type == 'arxiv':
                enhancement = f"\n\n**Recent Research**: {source.content[:300]}...\n\n*Source*: [Latest Research]({source.url})"
                enhancements.append(enhancement)

        return enhancements

    def _apply_enhancements(self, content: str, enhancements: List[str]) -> str:
        """Apply enhancements to content intelligently"""

        if not enhancements:
            return content

        # Find good insertion points (end of sections, before conclusions)
        paragraphs = content.split('\n\n')
        enhanced_paragraphs = []

        enhancement_idx = 0

        for i, paragraph in enumerate(paragraphs):
            enhanced_paragraphs.append(paragraph)

            # Insert enhancements at strategic points
            if (enhancement_idx < len(enhancements) and 
                (i == len(paragraphs) // 2 or  # Middle of content
                 'example' in paragraph.lower() or  # After examples
                 paragraph.endswith('.') and len(paragraph) > 100)):  # End of substantial paragraphs

                enhanced_paragraphs.append(enhancements[enhancement_idx])
                enhancement_idx += 1

        # Add remaining enhancements at the end
        while enhancement_idx < len(enhancements):
            enhanced_paragraphs.append(enhancements[enhancement_idx])
            enhancement_idx += 1

        return '\n\n'.join(enhanced_paragraphs)

    def get_domain_learning_path(self, domain: str, target_audience: str) -> Dict[str, Any]:
        """Generate optimal learning path for domain"""

        domain_concepts = self.knowledge_base.domain_concepts.get(domain.lower().replace(' ', '_'), {})

        learning_path = {
            'prerequisites': [],
            'core_topics': [],
            'advanced_topics': [],
            'practical_projects': [],
            'assessment_criteria': []
        }

        # Build learning progression based on complexity
        for concept, details in domain_concepts.items():
            if details.get('complexity_level') == 'beginner':
                learning_path['prerequisites'].extend(details.get('prerequisites', []))
            elif details.get('complexity_level') == 'intermediate':
                learning_path['core_topics'].append(concept)
            else:
                learning_path['advanced_topics'].append(concept)

            learning_path['practical_projects'].extend(details.get('practical_applications', []))

        return learning_path