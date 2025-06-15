from __future__ import annotations

import json
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass

@dataclass
class ExpertPromptTemplate:
    """Expert-level prompt template with domain specialization"""
    persona: str
    context: str
    techniques: List[str]
    examples: List[str]
    requirements: List[str]
    validation_criteria: List[str]

class AdvancedPromptEngine:
    """World-class prompt engineering for expert-level content generation"""
    
    def __init__(self):
        self.domain_knowledge = self._load_domain_knowledge()
        self.expert_personas = self._load_expert_personas()
        self.few_shot_examples = self._load_few_shot_examples()
        self.advanced_techniques = self._load_advanced_techniques()
    
    def create_expert_prompt(self, agent_type: str, topic: str, context: Dict[str, Any]) -> str:
        """Generate PhD-level expert prompts with advanced techniques"""
        
        # Get domain-specific expert persona
        persona = self._get_expert_persona(agent_type, topic)
        
        # Advanced prompting techniques
        techniques = self._get_advanced_techniques(agent_type, topic)
        
        # Domain-specific few-shot examples
        examples = self._get_few_shot_examples(agent_type, topic)
        
        # Chain-of-thought reasoning
        cot_structure = self._get_chain_of_thought_structure(agent_type)
        
        # Domain knowledge integration
        domain_context = self._get_domain_context(topic)
        
        prompt = f"""
{persona}

DOMAIN EXPERTISE CONTEXT:
{domain_context}

ADVANCED CONTENT GENERATION TECHNIQUES:
{techniques}

CHAIN-OF-THOUGHT REASONING STRUCTURE:
{cot_structure}

EXPERT-LEVEL EXAMPLES:
{examples}

SPECIFIC TASK:
{context.get('task', '')}

CONTEXT FROM PREVIOUS WORK:
{self._format_context(context)}

EXPERT REQUIREMENTS:
- Demonstrate deep domain mastery equivalent to 10+ years experience
- Include cutting-edge industry practices and emerging trends
- Provide detailed technical explanations with real-world applications
- Use authoritative sources and cite recent research (2020+)
- Include practical implementation details and code examples where relevant
- Address common misconceptions and advanced edge cases
- Show comparative analysis with alternative approaches
- Include performance considerations and optimization strategies
- Provide troubleshooting guides and debugging approaches
- Use progressive complexity building from fundamentals to advanced concepts

{self._get_template_requirements(agent_type, context)}

VALIDATION CRITERIA:
- Content must pass peer review by domain experts
- Technical accuracy verified against authoritative sources
- Practical examples must be production-ready
- Explanations clear enough for target audience yet comprehensive
- Must include current industry standards and best practices

Generate content that would be suitable for publication in top-tier technical journals and professional reference books.
"""
        return prompt.strip()
    
    def _get_expert_persona(self, agent_type: str, topic: str) -> str:
        """Create PhD-level expert persona based on agent type and domain"""
        
        domain_expertise = self._get_domain_specific_credentials(topic)
        
        personas = {
            "outline": f"""
You are a distinguished academic and industry expert in {topic} with:
- PhD in relevant field with 15+ years research experience
- Published 50+ peer-reviewed papers in top-tier journals
- Author of 3 bestselling technical books in the domain
- Former CTO at leading {topic} companies
- Keynote speaker at major international {topic} conferences
- {domain_expertise}

You excel at creating comprehensive, pedagogically sound book outlines that build knowledge systematically from fundamentals to cutting-edge applications.
""",
            
            "writer": f"""
You are a world-renowned expert in {topic} with:
- 20+ years of hands-on industry experience
- Lead architect on systems handling millions of users/transactions
- Recognized thought leader with 100K+ professional followers
- Contributor to major open-source projects in the field
- Technical advisor to Fortune 500 companies
- {domain_expertise}

Your writing is known for combining theoretical depth with practical wisdom, making complex concepts accessible without sacrificing accuracy.
""",
            
            "chapter": f"""
You are a master educator and {topic} expert with:
- Professor at top-tier university teaching advanced {topic} courses
- 25+ years experience training professionals and PhD students
- Creator of curricula used by leading technology companies
- Expert consultant for complex {topic} implementations
- {domain_expertise}

You have the rare ability to break down the most complex {topic} concepts into digestible, actionable knowledge while maintaining technical rigor.
""",
            
            "reviewer": f"""
You are a senior technical editor and {topic} expert with:
- Chief Editor at premier {topic} publications for 10+ years
- Reviewer for top computer science and engineering journals
- PhD in {topic} with expertise in quality assessment methodologies
- Consultant for technical accuracy in major {topic} publications
- {domain_expertise}

You maintain the highest standards of technical accuracy, clarity, and pedagogical effectiveness in {topic} content.
""",
            
            "enhancer": f"""
You are an expert instructional designer and {topic} practitioner with:
- MS in Instructional Design + Advanced {topic} certifications
- 15+ years creating engaging technical training for Fortune 500
- Expert in cognitive load theory and adult learning principles
- Specialist in creating hands-on {topic} exercises and assessments
- {domain_expertise}

You excel at creating compelling examples, case studies, and exercises that reinforce learning and build practical skills.
"""
        }
        
        return personas.get(agent_type, f"You are a world-class expert in {topic} with decades of experience.")
    
    def _get_domain_specific_credentials(self, topic: str) -> str:
        """Get domain-specific credentials and expertise markers"""
        
        credentials = {
            "machine learning": "Certified TensorFlow Expert, AWS ML Specialty, published research in NeurIPS/ICML",
            "data science": "Kaggle Grandmaster, certified in advanced statistics, expert in MLOps and production ML",
            "software engineering": "Principal Engineer at FAANG companies, architect of distributed systems, expert in system design",
            "cybersecurity": "CISSP, CISM, penetration testing expert, security researcher with CVEs discovered",
            "artificial intelligence": "Research scientist at leading AI labs, contributor to breakthrough AI papers",
            "cloud computing": "AWS/Azure/GCP certified architect, expert in cloud-native architectures",
            "blockchain": "Early Bitcoin contributor, smart contract security expert, DeFi protocol architect",
            "devops": "Kubernetes CKA/CKS certified, SRE at scale, infrastructure-as-code expert"
        }
        
        # Find closest match
        topic_lower = topic.lower()
        for domain, creds in credentials.items():
            if domain in topic_lower or any(word in topic_lower for word in domain.split()):
                return creds
        
        return "Industry-recognized expert with advanced certifications and practical experience"
    
    def _get_advanced_techniques(self, agent_type: str, topic: str) -> str:
        """Advanced content generation techniques for each agent type"""
        
        techniques = {
            "outline": f"""
1. COGNITIVE LOAD THEORY: Structure chapters to optimize learning progression
2. BLOOM'S TAXONOMY: Ensure objectives progress from remember→understand→apply→analyze→evaluate→create
3. SPIRAL CURRICULUM: Revisit key concepts with increasing complexity
4. CONSTRUCTIVIST APPROACH: Build new knowledge on existing foundations
5. JUST-IN-TIME LEARNING: Introduce concepts exactly when needed
6. PROBLEM-BASED LEARNING: Structure around real-world {topic} challenges
7. SCAFFOLDING TECHNIQUE: Provide support that gradually decreases
8. INTERLEAVING: Mix related topics to improve retention
""",
            
            "writer": f"""
1. FEYNMAN TECHNIQUE: Explain complex {topic} concepts in simple terms first
2. ANALOGICAL REASONING: Use familiar concepts to explain unfamiliar ones
3. WORKED EXAMPLES: Show complete problem-solving processes step-by-step
4. ELABORATIVE INTERROGATION: Answer "why" and "how" questions explicitly
5. CONCRETE-TO-ABSTRACT: Start with specific examples before general principles
6. DUAL CODING: Combine verbal explanations with visual representations
7. SPACED REPETITION: Reinforce key concepts throughout the content
8. METACOGNITIVE STRATEGIES: Explicitly teach thinking processes
""",
            
            "chapter": f"""
1. ADVANCE ORGANIZERS: Begin with clear learning objectives and concept maps
2. ELABORATION TECHNIQUE: Expand on ideas with detailed explanations and examples
3. QUESTIONING STRATEGY: Use Socratic method to guide reader thinking
4. CASE-BASED REASONING: Use detailed {topic} case studies for deep learning
5. PROCEDURAL KNOWLEDGE: Break complex {topic} processes into clear steps
6. DECLARATIVE KNOWLEDGE: Provide comprehensive conceptual understanding
7. CONDITIONAL KNOWLEDGE: Explain when and why to use specific {topic} approaches
8. EXPERT MODELING: Show how experts think about {topic} problems
"""
        }
        
        return techniques.get(agent_type, "Use evidence-based pedagogical techniques for effective learning.")
    
    def _get_chain_of_thought_structure(self, agent_type: str) -> str:
        """Chain-of-thought reasoning structure for systematic thinking"""
        
        structures = {
            "outline": """
1. ANALYZE: What are the core concepts and their relationships?
2. SEQUENCE: What's the optimal learning progression?
3. CHUNK: How can complex topics be broken into manageable sections?
4. CONNECT: How do concepts build upon each other?
5. VALIDATE: Does this structure support effective learning?
6. REFINE: How can the organization be improved?
""",
            
            "writer": """
1. CONTEXTUALIZE: Why is this concept important?
2. DEFINE: What exactly does this mean?
3. EXPLAIN: How does this work in detail?
4. EXEMPLIFY: What are concrete examples?
5. APPLY: How is this used in practice?
6. ANALYZE: What are the implications and limitations?
7. SYNTHESIZE: How does this connect to other concepts?
""",
            
            "chapter": """
1. ACTIVATE: What prior knowledge is needed?
2. ORIENT: What will readers learn and why?
3. DEVELOP: How can concepts be built systematically?
4. PRACTICE: What exercises reinforce learning?
5. ASSESS: How can understanding be verified?
6. EXTEND: What are advanced applications?
7. REFLECT: What are key takeaways?
"""
        }
        
        return structures.get(agent_type, "Use systematic reasoning to develop comprehensive content.")
    
    def _get_few_shot_examples(self, agent_type: str, topic: str) -> str:
        """High-quality few-shot examples for different agent types"""
        
        if agent_type == "writer" and "machine learning" in topic.lower():
            return """
EXAMPLE OF EXPERT-LEVEL TECHNICAL WRITING:

"Gradient descent optimization presents a fundamental trade-off between convergence speed and stability. While larger learning rates (α > 0.1) can accelerate initial training, they risk overshooting optimal minima in high-dimensional loss landscapes. This phenomenon becomes particularly problematic in deep networks with non-convex loss functions.

Consider a practical implementation scenario: training a ResNet-50 on ImageNet. Initial experiments with α = 0.1 showed rapid loss reduction for the first 10 epochs, but subsequently exhibited oscillatory behavior around local minima. By implementing a cosine annealing schedule starting at α = 0.01, we achieved both stable convergence and 2.3% accuracy improvement over fixed learning rates.

The mathematical intuition becomes clear when examining the Hessian matrix condition number. In regions where λmax/λmin > 100 (poorly conditioned), large learning rates cause instability along the most sensitive eigenvector directions. This explains why adaptive optimizers like Adam, which normalize gradients by their historical magnitudes, often outperform SGD in practice."

NOTE: This example demonstrates:
- Deep technical knowledge with specific parameters
- Real-world implementation details
- Mathematical reasoning
- Practical insights from experience
- Quantified results
"""
        
        return "Use expert-level examples that demonstrate deep domain knowledge and practical experience."
    
    def _get_domain_context(self, topic: str) -> str:
        """Comprehensive domain context with current trends and practices"""
        
        domain_contexts = {
            "machine learning": """
CURRENT STATE OF MACHINE LEARNING (2024):

**Cutting-Edge Developments:**
- Large Language Models: GPT-4, Claude-3, Gemini Ultra transforming NLP
- Multimodal AI: Vision-language models (CLIP, DALL-E 3) enabling cross-modal reasoning
- Foundation Models: Pre-trained models as universal starting points
- MLOps Maturation: Production ML pipelines with monitoring and governance

**Industry Standards & Best Practices:**
- Model Cards for transparency and documentation
- Responsible AI frameworks for bias detection and mitigation
- Edge deployment optimizations (quantization, pruning, distillation)
- Federated learning for privacy-preserving training

**Current Challenges:**
- Hallucination and factual accuracy in LLMs
- Computational sustainability and green AI
- Model interpretability and explainability
- Data privacy and regulatory compliance (GDPR, AI Act)

**Tools & Frameworks (2024):**
- PyTorch 2.0+ with improved compilation
- Hugging Face Transformers ecosystem
- MLflow, Weights & Biases for experiment tracking
- Kubernetes-native ML platforms (Kubeflow, Seldon)
""",
            
            "software engineering": """
CURRENT SOFTWARE ENGINEERING LANDSCAPE (2024):

**Architecture Trends:**
- Microservices evolution to modular monoliths
- Event-driven architectures with Apache Kafka, Pulsar
- Serverless-first development with AWS Lambda, Vercel Functions
- Platform engineering and developer experience focus

**Development Practices:**
- Shift-left security with DevSecOps integration
- Observability-driven development (OpenTelemetry standard)
- Chaos engineering for resilience testing
- Infrastructure as Code with Terraform, Pulumi

**Current Technologies:**
- Container orchestration: Kubernetes 1.28+, Docker alternatives (Podman)
- Service mesh: Istio, Linkerd for microservices communication
- CI/CD evolution: GitHub Actions, GitLab CI, Tekton pipelines
- Database trends: PostgreSQL extensions, distributed SQL (CockroachDB)

**Quality & Performance:**
- SRE practices: SLI/SLO-driven reliability
- Performance engineering: Core Web Vitals, real user monitoring
- Testing strategies: Shift-left testing, contract testing
- Code quality: Static analysis integration (SonarQube, CodeClimate)
"""
        }
        
        topic_lower = topic.lower()
        for domain, context in domain_contexts.items():
            if domain in topic_lower or any(word in topic_lower for word in domain.split()):
                return context
        
        return f"Current industry trends, best practices, and cutting-edge developments in {topic}"
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context information for prompt inclusion"""
        formatted = []
        
        if context.get('previous_chapters'):
            formatted.append(f"Previous chapters covered: {', '.join(context['previous_chapters'])}")
        
        if context.get('target_audience'):
            formatted.append(f"Target audience: {context['target_audience']}")
        
        if context.get('book_style'):
            formatted.append(f"Book style: {context['book_style']}")
        
        if context.get('current_chapter'):
            formatted.append(f"Current chapter: {context['current_chapter']}")
        
        return '\n'.join(formatted) if formatted else "No additional context provided"
    
    def _get_template_requirements(self, agent_type: str, context: Dict[str, Any]) -> str:
        """Get specific template requirements based on agent type"""
        
        if agent_type == "chapter" or context.get('template_requirements'):
            return """
UNIFIED CHAPTER TEMPLATE STRUCTURE:

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
   
TEMPLATE STYLE REQUIREMENTS:
- Use active voice throughout
- Keep sentences concise and clear
- Include specific examples and data points
- Make content immediately actionable
- Use proper Markdown formatting with clear headers
"""
        
        return ""
    
    def _load_domain_knowledge(self) -> Dict[str, Any]:
        """Load domain-specific knowledge base"""
        # This would load from external knowledge sources
        return {}
    
    def _load_expert_personas(self) -> Dict[str, str]:
        """Load expert persona templates"""
        return {}
    
    def _load_few_shot_examples(self) -> Dict[str, List[str]]:
        """Load few-shot examples by domain and agent type"""
        return {}
    
    def _load_advanced_techniques(self) -> Dict[str, List[str]]:
        """Load advanced prompting techniques"""
        return {}

# Legacy functions for backward compatibility
def generate_question(section_heading: str, section_text: str) -> str:
    """Generate a simple comprehension question."""
    return f"What did you learn in {section_heading}?"

def generate_example(topic: str) -> str:
    """Generate a short illustrative example."""
    return f"For instance, {topic.lower()} can be applied in real-world situations."

# Initialize global prompt engine
prompt_engine = AdvancedPromptEngine()
