from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Suggestion:
    """Represents an edit suggestion."""

    position: int
    original: str
    recommendation: str


@dataclass
class EmbeddedElement:
    """Represents an embedded piece of content."""

    element_type: str
    content: str
    position: int


@dataclass
class SectionMeta:
    """Metadata describing a section of text."""

    heading: str
    start: int
    end: int


@dataclass
class ChapterOutput:
    """Output from chapter-level processing."""

    content: str
    metadata: Dict[str, Any]
    acronym_glossary: Dict[str, str] | None = None


@dataclass
class TOCEntry:
    """Table of contents entry."""

    chapter: str
    title: str


@dataclass
class Config:
    """Global configuration settings."""

    book_title: str = "Untitled"
    author: str = "Unknown"


@dataclass
class AgentInput:
    """Generic input for agents."""

    content: str = ""
    metadata: Optional[Dict[str, Any]] = None
    outline: Optional[List[SectionMeta]] = None
    inputs: Optional[List[ChapterOutput]] = None


@dataclass
class AgentOutput:
    """Generic output from agents."""

    corrected_text: Optional[str] = None
    suggestions: Optional[List[Suggestion]] = None
    enhanced_content: Optional[str] = None
    added_elements: Optional[List[EmbeddedElement]] = None
    resolved_content: Optional[str] = None
    acronym_glossary: Optional[Dict[str, str]] = None
    is_valid: Optional[bool] = None
    issues: Optional[List[str]] = None
    final_doc: Optional[str] = None
    toc: Optional[List[TOCEntry]] = None
