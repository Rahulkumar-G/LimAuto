from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class BookState(BaseModel):
    """State management for book generation process"""

    # Core metadata
    topic: str
    target_audience: str = "beginners"
    book_style: str = "professional"
    estimated_pages: int = 100
    language: str = "en"
    isbn: Optional[str] = None
    edition: str = "1st Edition"
    publication_date: Optional[datetime] = None
    copyright_info: Optional[str] = None
    series_name: Optional[str] = None
    series_number: Optional[int] = None
    keywords: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)

    # Quality metrics
    technical_accuracy_score: Optional[float] = None
    engagement_score: Optional[float] = None
    consistency_score: Optional[float] = None
    completeness_score: Optional[float] = None

    # Content structure
    outline: List[str] = Field(default_factory=list)
    title_page: Optional[str] = None
    foreword: Optional[str] = None
    dedication: Optional[str] = None
    epigraph: Optional[str] = None
    preface: Optional[str] = None
    prologue: Optional[str] = None
    table_of_contents: Optional[str] = None
    chapters: List[str] = Field(default_factory=list)
    chapter_map: Dict[str, str] = Field(default_factory=dict)
    chapter_summaries: Dict[str, str] = Field(default_factory=dict)

    # Enhanced content
    glossary: Dict[str, str] = Field(default_factory=dict)
    acronyms: Dict[str, str] = Field(default_factory=dict)
    references: List[str] = Field(default_factory=list)
    code_samples: Dict[str, str] = Field(default_factory=dict)
    exercises: Dict[str, List[str]] = Field(default_factory=dict)
    case_studies: Dict[str, str] = Field(default_factory=dict)

    # Visual elements
    images: Dict[str, str] = Field(default_factory=dict)
    diagrams: Dict[str, str] = Field(default_factory=dict)
    cover_image: Optional[str] = None

    # Quality assurance
    content_review: Optional[str] = None
    technical_review: Optional[str] = None
    editorial_review: Optional[str] = None
    fact_check: Optional[str] = None
    readability_score: Optional[float] = None

    # Content statistics
    total_images: int = 0
    total_tables: int = 0
    total_code_blocks: int = 0
    total_examples: int = 0
    total_references: int = 0

    # Tracking fields
    generation_started: Optional[datetime] = None
    generation_completed: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    version: str = "1.0.0"

    # Final content
    acknowledgments: Optional[str] = None
    about_the_author: Optional[str] = None
    conclusion: Optional[str] = None
    appendices: Dict[str, str] = Field(default_factory=dict)
    bibliography: Optional[str] = None
    index_terms: List[str] = Field(default_factory=list)

    # Compilation
    compiled_book: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Processing status
    current_step: str = "initialized"
    completed_steps: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    @field_validator("topic", mode="before")
    @classmethod
    def topic_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Topic cannot be empty")
        return v.strip()
