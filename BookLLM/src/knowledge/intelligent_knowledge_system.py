"""
Intelligent Knowledge System with Dynamic Search and Curation
Replaces static knowledge storage with intelligent real-time knowledge retrieval and curation
"""

import asyncio
import json
import hashlib
import sqlite3
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import re

import wikipedia
import arxiv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from ..utils.logger import get_logger

@dataclass
class KnowledgeItem:
    """Represents a curated knowledge item"""
    id: str
    content: str
    source_type: str
    source_url: str
    domain: str
    relevance_score: float
    credibility_score: float
    last_updated: datetime
    keywords: List[str]
    summary: str
    citations: List[str]

@dataclass
class SearchResult:
    """Search result with ranking and metadata"""
    knowledge_item: KnowledgeItem
    relevance_score: float
    context_match: float
    freshness_score: float
    combined_score: float

class IntelligentKnowledgeDatabase:
    """SQLite-based knowledge database with intelligent indexing"""
    
    def __init__(self, db_path: str = "knowledge_cache.db"):
        self.db_path = db_path
        self.logger = get_logger(__name__)
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database with proper schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_items (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                source_type TEXT NOT NULL,
                source_url TEXT,
                domain TEXT NOT NULL,
                relevance_score REAL,
                credibility_score REAL,
                last_updated TEXT,
                keywords TEXT, -- JSON array
                summary TEXT,
                citations TEXT -- JSON array
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_domain ON knowledge_items(domain)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_relevance ON knowledge_items(relevance_score DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_updated ON knowledge_items(last_updated DESC)
        """)
        
        # Full-text search
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
                id, content, summary, keywords, content=knowledge_items, content_rowid=rowid
            )
        """)
        
        conn.commit()
        conn.close()
    
    def store_knowledge_item(self, item: KnowledgeItem):
        """Store knowledge item in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO knowledge_items 
            (id, content, source_type, source_url, domain, relevance_score, 
             credibility_score, last_updated, keywords, summary, citations)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item.id,
            item.content,
            item.source_type,
            item.source_url,
            item.domain,
            item.relevance_score,
            item.credibility_score,
            item.last_updated.isoformat(),
            json.dumps(item.keywords),
            item.summary,
            json.dumps(item.citations)
        ))
        
        # Update FTS index
        cursor.execute("""
            INSERT OR REPLACE INTO knowledge_fts (rowid, id, content, summary, keywords)
            SELECT rowid, id, content, summary, keywords FROM knowledge_items WHERE id = ?
        """, (item.id,))
        
        conn.commit()
        conn.close()
    
    def search_knowledge(self, query: str, domain: str = None, 
                        limit: int = 10, min_relevance: float = 0.3) -> List[KnowledgeItem]:
        """Search knowledge items with intelligent ranking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build search query
        search_conditions = ["relevance_score >= ?"]
        params = [min_relevance]
        
        if domain:
            search_conditions.append("domain = ?")
            params.append(domain)
        
        # Use FTS for text search
        fts_query = f"'{query}'"
        
        sql = f"""
            SELECT k.* FROM knowledge_items k
            INNER JOIN knowledge_fts fts ON k.rowid = fts.rowid
            WHERE fts MATCH ? AND {' AND '.join(search_conditions)}
            ORDER BY k.relevance_score DESC, k.last_updated DESC
            LIMIT ?
        """
        
        params = [fts_query] + params + [limit]
        cursor.execute(sql, params)
        
        results = []
        for row in cursor.fetchall():
            item = KnowledgeItem(
                id=row[0],
                content=row[1],
                source_type=row[2],
                source_url=row[3],
                domain=row[4],
                relevance_score=row[5],
                credibility_score=row[6],
                last_updated=datetime.fromisoformat(row[7]),
                keywords=json.loads(row[8]),
                summary=row[9],
                citations=json.loads(row[10])
            )
            results.append(item)
        
        conn.close()
        return results
    
    def get_domain_statistics(self, domain: str) -> Dict[str, Any]:
        """Get statistics for a domain"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_items,
                AVG(relevance_score) as avg_relevance,
                AVG(credibility_score) as avg_credibility,
                MAX(last_updated) as latest_update
            FROM knowledge_items 
            WHERE domain = ?
        """, (domain,))
        
        result = cursor.fetchone()
        conn.close()
        
        return {
            'total_items': result[0],
            'average_relevance': result[1],
            'average_credibility': result[2],
            'latest_update': result[3]
        }

class IntelligentSearchEngine:
    """Advanced search engine with multiple knowledge sources"""
    
    def __init__(self, db: IntelligentKnowledgeDatabase):
        self.db = db
        self.logger = get_logger(__name__)
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        # Initialize search providers
        self.search_providers = {
            'wikipedia': self._search_wikipedia,
            'arxiv': self._search_arxiv,
            'github': self._search_github,
            'stackoverflow': self._search_stackoverflow,
            'documentation': self._search_documentation
        }
    
    async def intelligent_search(self, query: str, domain: str, 
                                context: str = "", max_results: int = 5) -> List[SearchResult]:
        """Perform intelligent multi-source search with ranking"""
        
        # First, search cached knowledge
        cached_results = self.db.search_knowledge(query, domain, limit=max_results)
        
        # If we have sufficient cached results, use them
        if len(cached_results) >= max_results // 2:
            search_results = [
                SearchResult(
                    knowledge_item=item,
                    relevance_score=item.relevance_score,
                    context_match=self._calculate_context_match(item.content, context),
                    freshness_score=self._calculate_freshness_score(item.last_updated),
                    combined_score=0.0  # Will be calculated
                )
                for item in cached_results[:max_results//2]
            ]
        else:
            search_results = []
        
        # Perform live searches for fresh content
        live_search_tasks = []
        remaining_results = max_results - len(search_results)
        
        if remaining_results > 0:
            for provider_name, search_func in self.search_providers.items():
                task = asyncio.create_task(
                    self._safe_search(search_func, query, domain, remaining_results // len(self.search_providers))
                )
                live_search_tasks.append((provider_name, task))
        
        # Collect live search results
        for provider_name, task in live_search_tasks:
            try:
                provider_results = await task
                for item in provider_results:
                    # Store in cache for future use
                    self.db.store_knowledge_item(item)
                    
                    # Create search result
                    result = SearchResult(
                        knowledge_item=item,
                        relevance_score=item.relevance_score,
                        context_match=self._calculate_context_match(item.content, context),
                        freshness_score=self._calculate_freshness_score(item.last_updated),
                        combined_score=0.0
                    )
                    search_results.append(result)
            except Exception as e:
                self.logger.warning(f"Search provider {provider_name} failed: {e}")
        
        # Calculate combined scores and rank
        for result in search_results:
            result.combined_score = (
                result.relevance_score * 0.4 +
                result.context_match * 0.3 +
                result.freshness_score * 0.2 +
                result.knowledge_item.credibility_score * 0.1
            )
        
        # Sort by combined score and return top results
        search_results.sort(key=lambda x: x.combined_score, reverse=True)
        return search_results[:max_results]
    
    async def _safe_search(self, search_func, query: str, domain: str, limit: int) -> List[KnowledgeItem]:
        """Safely execute search function with timeout"""
        try:
            return await asyncio.wait_for(search_func(query, domain, limit), timeout=10.0)
        except asyncio.TimeoutError:
            self.logger.warning(f"Search function {search_func.__name__} timed out")
            return []
        except Exception as e:
            self.logger.error(f"Search function {search_func.__name__} failed: {e}")
            return []
    
    async def _search_wikipedia(self, query: str, domain: str, limit: int) -> List[KnowledgeItem]:
        """Search Wikipedia with domain-specific filtering"""
        results = []
        
        try:
            # Enhanced query with domain context
            domain_query = f"{query} {domain}"
            search_results = wikipedia.search(domain_query, results=limit * 2)
            
            for title in search_results[:limit]:
                try:
                    page = wikipedia.page(title)
                    
                    # Calculate relevance score
                    relevance_score = self._calculate_relevance_score(
                        page.summary, query, domain
                    )
                    
                    if relevance_score > 0.3:  # Filter low-relevance results
                        # Extract keywords
                        keywords = self._extract_keywords(page.summary)
                        
                        # Create knowledge item
                        item = KnowledgeItem(
                            id=hashlib.md5(f"wikipedia_{page.url}".encode()).hexdigest(),
                            content=page.summary[:2000],  # Limit content length
                            source_type='wikipedia',
                            source_url=page.url,
                            domain=domain,
                            relevance_score=relevance_score,
                            credibility_score=0.75,  # Wikipedia baseline credibility
                            last_updated=datetime.now(),
                            keywords=keywords,
                            summary=page.summary[:300],
                            citations=[]
                        )
                        results.append(item)
                        
                except wikipedia.exceptions.DisambiguationError as e:
                    # Try first disambiguation option
                    if e.options:
                        try:
                            page = wikipedia.page(e.options[0])
                            relevance_score = self._calculate_relevance_score(
                                page.summary, query, domain
                            )
                            if relevance_score > 0.3:
                                keywords = self._extract_keywords(page.summary)
                                item = KnowledgeItem(
                                    id=hashlib.md5(f"wikipedia_{page.url}".encode()).hexdigest(),
                                    content=page.summary[:2000],
                                    source_type='wikipedia',
                                    source_url=page.url,
                                    domain=domain,
                                    relevance_score=relevance_score,
                                    credibility_score=0.75,
                                    last_updated=datetime.now(),
                                    keywords=keywords,
                                    summary=page.summary[:300],
                                    citations=[]
                                )
                                results.append(item)
                        except Exception:
                            continue
                except Exception:
                    continue
                    
        except Exception as e:
            self.logger.error(f"Wikipedia search failed: {e}")
        
        return results
    
    async def _search_arxiv(self, query: str, domain: str, limit: int) -> List[KnowledgeItem]:
        """Search arXiv for recent research papers"""
        results = []
        
        try:
            # Enhanced query for academic papers
            academic_query = f"{query} {domain}"
            
            search = arxiv.Search(
                query=academic_query,
                max_results=limit,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            for paper in search.results():
                relevance_score = self._calculate_relevance_score(
                    paper.summary, query, domain
                )
                
                if relevance_score > 0.4:  # Higher threshold for academic papers
                    keywords = self._extract_keywords(paper.summary)
                    
                    # Extract citations from references
                    citations = [author.name for author in paper.authors[:3]]
                    
                    item = KnowledgeItem(
                        id=hashlib.md5(f"arxiv_{paper.entry_id}".encode()).hexdigest(),
                        content=paper.summary[:2000],
                        source_type='arxiv',
                        source_url=paper.entry_id,
                        domain=domain,
                        relevance_score=relevance_score,
                        credibility_score=0.9,  # Academic papers have high credibility
                        last_updated=paper.updated,
                        keywords=keywords,
                        summary=paper.title + ": " + paper.summary[:200],
                        citations=citations
                    )
                    results.append(item)
                    
        except Exception as e:
            self.logger.error(f"arXiv search failed: {e}")
        
        return results
    
    async def _search_github(self, query: str, domain: str, limit: int) -> List[KnowledgeItem]:
        """Search GitHub for relevant repositories and documentation"""
        results = []
        
        try:
            # GitHub API search (requires token for higher rate limits)
            search_query = f"{query} {domain} language:markdown OR language:python"
            
            # This is a placeholder - in production you'd use GitHub API
            # For now, we'll return empty results
            self.logger.info(f"GitHub search not implemented yet for: {search_query}")
            
        except Exception as e:
            self.logger.error(f"GitHub search failed: {e}")
        
        return results
    
    async def _search_stackoverflow(self, query: str, domain: str, limit: int) -> List[KnowledgeItem]:
        """Search StackOverflow for practical solutions"""
        results = []
        
        try:
            # StackExchange API search
            # This is a placeholder - in production you'd use StackExchange API
            self.logger.info(f"StackOverflow search not implemented yet for: {query}")
            
        except Exception as e:
            self.logger.error(f"StackOverflow search failed: {e}")
        
        return results
    
    async def _search_documentation(self, query: str, domain: str, limit: int) -> List[KnowledgeItem]:
        """Search official documentation sites"""
        results = []
        
        try:
            # Search official docs (placeholder)
            self.logger.info(f"Documentation search not implemented yet for: {query}")
            
        except Exception as e:
            self.logger.error(f"Documentation search failed: {e}")
        
        return results
    
    def _calculate_relevance_score(self, content: str, query: str, domain: str) -> float:
        """Calculate relevance score using multiple factors"""
        content_lower = content.lower()
        query_lower = query.lower()
        domain_lower = domain.lower()
        
        # Query term frequency
        query_terms = query_lower.split()
        query_matches = sum(1 for term in query_terms if term in content_lower)
        query_score = query_matches / len(query_terms) if query_terms else 0
        
        # Domain relevance
        domain_terms = domain_lower.replace('_', ' ').split()
        domain_matches = sum(1 for term in domain_terms if term in content_lower)
        domain_score = domain_matches / len(domain_terms) if domain_terms else 0
        
        # Content quality indicators
        quality_indicators = [
            'research', 'study', 'analysis', 'implementation', 'example',
            'tutorial', 'guide', 'best practice', 'performance', 'optimization'
        ]
        quality_matches = sum(1 for indicator in quality_indicators if indicator in content_lower)
        quality_score = min(quality_matches / 3, 1.0)
        
        # Combine scores
        relevance_score = (
            query_score * 0.5 +
            domain_score * 0.3 +
            quality_score * 0.2
        )
        
        return min(relevance_score, 1.0)
    
    def _calculate_context_match(self, content: str, context: str) -> float:
        """Calculate how well content matches the given context"""
        if not context:
            return 0.5  # Neutral score when no context
        
        try:
            # Use TF-IDF similarity
            texts = [content, context]
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity)
        except Exception:
            return 0.5
    
    def _calculate_freshness_score(self, last_updated: datetime) -> float:
        """Calculate freshness score based on how recent the content is"""
        now = datetime.now()
        age = now - last_updated
        
        # Content fresher than 30 days gets full score
        if age.days <= 30:
            return 1.0
        # Linear decay over 2 years
        elif age.days <= 730:
            return 1.0 - (age.days - 30) / 700
        else:
            return 0.1  # Minimum score for very old content
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        # Simple keyword extraction using common patterns
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter out common words
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had',
            'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his',
            'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy',
            'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'
        }
        
        keywords = [word for word in words if word not in stop_words]
        
        # Return most frequent keywords
        word_freq = {}
        for word in keywords:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_keywords[:10]]

class IntelligentDomainExpert:
    """High-level domain expert that coordinates intelligent knowledge retrieval"""
    
    def __init__(self, db_path: str = "intelligent_knowledge.db"):
        self.db = IntelligentKnowledgeDatabase(db_path)
        self.search_engine = IntelligentSearchEngine(self.db)
        self.logger = get_logger(__name__)
        
        # Knowledge curation thresholds
        self.min_relevance_threshold = 0.6
        self.min_credibility_threshold = 0.7
    
    async def get_expert_knowledge(self, topic: str, domain: str, 
                                  context: str = "", max_items: int = 5) -> List[KnowledgeItem]:
        """Get curated expert knowledge for a topic"""
        
        self.logger.info(f"Retrieving expert knowledge for: {topic} in domain: {domain}")
        
        # Perform intelligent search
        search_results = await self.search_engine.intelligent_search(
            query=topic,
            domain=domain,
            context=context,
            max_results=max_items * 2  # Get more results for filtering
        )
        
        # Filter and curate results
        curated_results = []
        for result in search_results:
            item = result.knowledge_item
            
            # Apply quality filters
            if (item.relevance_score >= self.min_relevance_threshold and
                item.credibility_score >= self.min_credibility_threshold):
                curated_results.append(item)
        
        # Ensure diversity in sources
        diverse_results = self._ensure_source_diversity(curated_results)
        
        return diverse_results[:max_items]
    
    async def enhance_content_with_intelligence(self, content: str, topic: str, 
                                              domain: str) -> str:
        """Enhance content with intelligently retrieved knowledge"""
        
        # Get relevant knowledge
        knowledge_items = await self.get_expert_knowledge(topic, domain, content)
        
        if not knowledge_items:
            return content
        
        # Create enhancement sections
        enhancements = []
        
        # Add expert insights
        high_credibility_items = [item for item in knowledge_items if item.credibility_score > 0.8]
        if high_credibility_items:
            enhancements.append(self._create_expert_insights_section(high_credibility_items))
        
        # Add recent research findings
        recent_items = [item for item in knowledge_items 
                       if item.source_type == 'arxiv' and 
                       (datetime.now() - item.last_updated).days < 365]
        if recent_items:
            enhancements.append(self._create_research_section(recent_items))
        
        # Add practical examples
        practical_items = [item for item in knowledge_items 
                          if any(keyword in item.keywords for keyword in 
                               ['example', 'implementation', 'tutorial', 'practice'])]
        if practical_items:
            enhancements.append(self._create_practical_section(practical_items))
        
        # Integrate enhancements into content
        enhanced_content = self._integrate_enhancements(content, enhancements)
        
        return enhanced_content
    
    def _ensure_source_diversity(self, results: List[KnowledgeItem]) -> List[KnowledgeItem]:
        """Ensure diversity in knowledge sources"""
        diverse_results = []
        source_counts = {}
        
        for item in results:
            source_type = item.source_type
            current_count = source_counts.get(source_type, 0)
            
            # Limit items per source type
            if current_count < 2 or len(diverse_results) < 3:
                diverse_results.append(item)
                source_counts[source_type] = current_count + 1
        
        return diverse_results
    
    def _create_expert_insights_section(self, items: List[KnowledgeItem]) -> str:
        """Create expert insights section from high-credibility sources"""
        insights = []
        
        for item in items[:2]:  # Limit to top 2 insights
            if item.source_type == 'wikipedia':
                insights.append(f"**Reference Knowledge**: {item.summary}")
            elif item.source_type == 'arxiv':
                insights.append(f"**Research Finding**: {item.summary}")
            else:
                insights.append(f"**Expert Source**: {item.summary}")
        
        if insights:
            return "\\n\\n### Expert Insights\\n\\n" + "\\n\\n".join(insights)
        return ""
    
    def _create_research_section(self, items: List[KnowledgeItem]) -> str:
        """Create research findings section"""
        if not items:
            return ""
        
        research_content = []
        for item in items[:2]:
            research_content.append(f"- {item.summary} ([Source]({item.source_url}))")
        
        return "\\n\\n### Recent Research\\n\\n" + "\\n".join(research_content)
    
    def _create_practical_section(self, items: List[KnowledgeItem]) -> str:
        """Create practical examples section"""
        if not items:
            return ""
        
        practical_content = []
        for item in items[:2]:
            practical_content.append(f"**Example**: {item.summary[:200]}...")
        
        return "\\n\\n### Practical Applications\\n\\n" + "\\n\\n".join(practical_content)
    
    def _integrate_enhancements(self, content: str, enhancements: List[str]) -> str:
        """Intelligently integrate enhancements into content"""
        if not enhancements:
            return content
        
        # Find good insertion points
        paragraphs = content.split('\\n\\n')
        
        # Insert enhancements after the first third of content
        insertion_point = len(paragraphs) // 3
        
        enhanced_paragraphs = (
            paragraphs[:insertion_point] + 
            enhancements + 
            paragraphs[insertion_point:]
        )
        
        return '\\n\\n'.join(enhanced_paragraphs)
    
    def get_domain_expertise_level(self, domain: str) -> Dict[str, Any]:
        """Get expertise level for a domain based on cached knowledge"""
        stats = self.db.get_domain_statistics(domain)
        
        # Calculate expertise level
        if stats['total_items'] >= 50 and stats['average_credibility'] >= 0.8:
            expertise_level = 'Expert'
        elif stats['total_items'] >= 20 and stats['average_credibility'] >= 0.7:
            expertise_level = 'Advanced'
        elif stats['total_items'] >= 10:
            expertise_level = 'Intermediate'
        else:
            expertise_level = 'Basic'
        
        return {
            'expertise_level': expertise_level,
            'knowledge_coverage': min(stats['total_items'] / 50, 1.0),
            'average_quality': stats['average_credibility'],
            'last_updated': stats['latest_update'],
            'recommendations': self._get_knowledge_recommendations(stats)
        }
    
    def _get_knowledge_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """Get recommendations for improving domain knowledge"""
        recommendations = []
        
        if stats['total_items'] < 20:
            recommendations.append("Expand knowledge base with more sources")
        
        if stats['average_credibility'] < 0.8:
            recommendations.append("Focus on higher-credibility sources")
        
        if stats['latest_update']:
            try:
                last_update = datetime.fromisoformat(stats['latest_update'])
                if (datetime.now() - last_update).days > 30:
                    recommendations.append("Update knowledge with recent information")
            except Exception:
                pass
        
        return recommendations

# Global intelligent domain expert instance
intelligent_expert = IntelligentDomainExpert()