from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from uuid import UUID, uuid4

# ============================================================================
# Wikipedia Quiz Game Models
# ============================================================================

class Question(BaseModel):
    """Multiple choice question with 4 options"""
    question_text: str = Field(description="The question being asked")
    options: List[str] = Field(description="4 answer options (A, B, C, D)")
    correct_answer_index: int = Field(description="Index of the correct answer (0-3)")
    difficulty: str = Field(description="Easy, Medium, or Hard")
    explanation: str = Field(description="Why this is the correct answer")

class SourceCitation(BaseModel):
    """Exact sentence from Wikipedia that justifies the answer"""
    sentence: str = Field(description="The exact sentence from Wikipedia")
    section_title: str = Field(description="Section where the sentence was found")
    section_url: str = Field(description="Direct link to the Wikipedia section")
    sentence_index: int = Field(description="Position of sentence in the section")

class SelectedSections(BaseModel):
    """The 3 most information-dense paragraphs from Wikipedia"""
    sections: List[str] = Field(description="List of 3 selected paragraph texts")
    reasoning: str = Field(description="Why these sections were chosen")

class ValidationResult(BaseModel):
    """Result of Auditor's validation"""
    is_valid: bool = Field(description="Whether the question is valid and verifiable")
    confidence: float = Field(description="Confidence score 0.0-1.0")
    issues: Optional[str] = Field(None, description="Issues found if not valid")
    correction_note: Optional[str] = Field(None, description="Guidance for Quiz Maker to fix issues")

class RelevanceScore(BaseModel):
    """Wikipedia link with relevance score"""
    link_title: str = Field(description="Title of the Wikipedia page")
    relevance_score: float = Field(description="Relevance score 0.0-1.0")
    reasoning: str = Field(description="Why this link is relevant")

class DebugLog(BaseModel):
    """Debug information for transparency"""
    agent_name: str = Field(description="Name of the agent")
    input_data: str = Field(description="Input to the agent")
    output_data: str = Field(description="Output from the agent")
    reasoning: Optional[str] = Field(None, description="Agent's reasoning process")
    timestamp: str = Field(description="When this step occurred")

class GameState(BaseModel):
    """Complete game state for one round"""
    round_id: UUID = Field(default_factory=uuid4)
    wikipedia_page_title: str = Field(description="Current Wikipedia page")
    wikipedia_url: str = Field(description="URL to the Wikipedia page")
    selected_sections: Optional[SelectedSections] = None
    question: Optional[Question] = None
    source_citation: Optional[SourceCitation] = None
    available_links: List[RelevanceScore] = Field(default_factory=list, description="Top 3 relevant links")
    user_answer: Optional[int] = None
    is_correct: Optional[bool] = None
    debug_logs: List[DebugLog] = Field(default_factory=list, description="Debug trail")
    correction_attempts: int = Field(default=0, description="Number of correction loop iterations")

# ============================================================================
# Legacy Models (for backward compatibility during migration)
# ============================================================================

class Fact(BaseModel):
    content: str = Field(description="The actual fact statement.")
    source: str = Field(description="Source or citation for the fact.")
    is_lie: bool = Field(description="True if this is the fabricated lie.")

class Verdict(BaseModel):
    selection: int = Field(description="The index (0-2) of the statement believed to be the lie.")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0.")
    reasoning: str = Field(description="Explanation of why this statement was chosen.")
    highlight_start: Optional[int] = Field(None, description="Start index of the suspicious part in the statement.")
    highlight_end: Optional[int] = Field(None, description="End index of the suspicious part in the statement.")
