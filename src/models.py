from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID, uuid4

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

class GameState(BaseModel):
    round_id: UUID = Field(default_factory=uuid4)
    topic: str
    raw_facts: List[Fact] = Field(default_factory=list, description="Original facts from researcher + created lie.")
    game_facts: List[Fact] = Field(default_factory=list, description="The 3 shuffled facts presented to users.")
    auditor_verdict: Optional[Verdict] = None
    user_guess: Optional[int] = None
