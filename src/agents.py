from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from src.models import Question, SelectedSections, ValidationResult, RelevanceScore
from typing import List

# Model configuration
# Primary: Gemini 1.5 Flash (fast, stable)
# Fallback: Gemini 1.5 Pro (slower but more powerful, for when Flash is overloaded)

SECTION_PICKER_MODEL = GoogleModel('models/gemini-3-pro-preview')
SECTION_PICKER_FALLBACK = GoogleModel('models/gemini-3-flash')

QUIZ_MAKER_MODEL = GoogleModel('models/gemini-3-pro-preview')
QUIZ_MAKER_FALLBACK = GoogleModel('models/gemini-3-flash')

AUDITOR_MODEL = GoogleModel('models/gemini-3-pro-preview')
AUDITOR_FALLBACK = GoogleModel('models/gemini-3-flash')

RELEVANCE_MODEL = GoogleModel('models/gemini-3-pro-preview')
RELEVANCE_FALLBACK = GoogleModel('models/gemini-3-flash')  # Flash is fine for relevance

# ============================================================================
# Wikipedia Quiz Game Agents
# ============================================================================

def create_section_picker_agent(use_fallback: bool = False):
    """
    Section Picker Agent - Extracts the 3 most information-dense paragraphs
    
    This solves the "lost in the middle" problem and token limits by selecting
    only the most relevant content for quiz generation.
    
    Args:
        use_fallback: If True, use the fallback model (slower but more reliable)
    """
    model = SECTION_PICKER_FALLBACK if use_fallback else SECTION_PICKER_MODEL
    
    return Agent(
        model,
        output_type=SelectedSections,
        system_prompt=(
            "You are an expert content curator for a quiz game. "
            "Your task is to analyze a Wikipedia page and select the 3 MOST INFORMATION-DENSE paragraphs. "
            "Look for paragraphs that:\n"
            "1. Contain specific facts, dates, names, or numbers\n"
            "2. Are substantive (not just introductory fluff)\n"
            "3. Cover different aspects of the topic (diversity)\n"
            "4. Are suitable for creating interesting quiz questions\n\n"
            "Avoid:\n"
            "- Very short paragraphs (less than 2 sentences)\n"
            "- Lists of references or external links\n"
            "- 'See also' sections\n"
            "- Overly technical jargon without context\n\n"
            "Return exactly 3 paragraphs with reasoning for why you chose them."
        )
    )

def create_quiz_maker_agent(use_fallback: bool = False):
    """
    Quiz Maker Agent - Generates multiple-choice questions
    
    Creates engaging questions with 4 options based on the selected sections.
    
    Args:
        use_fallback: If True, use the fallback model (slower but more reliable)
    """
    model = QUIZ_MAKER_FALLBACK if use_fallback else QUIZ_MAKER_MODEL
    
    return Agent(
        model,
        output_type=Question,
        system_prompt=(
            "You are an expert quiz creator. "
            "You will receive 3 information-dense paragraphs from a Wikipedia page. "
            "Your task is to create ONE multiple-choice question with 4 options (A, B, C, D). "
            "\n"
            "Requirements:\n"
            "1. The question must be DIRECTLY ANSWERABLE from the provided text\n"
            "2. The correct answer must be EXPLICITLY stated in the text\n"
            "3. Create 3 plausible wrong answers that are thematically related but incorrect\n"
            "4. Make the question interesting and specific (avoid yes/no questions)\n"
            "5. Difficulty should be Medium (not too easy, not impossibly hard)\n"
            "6. For the EXPLANATION:\n"
            "   - Write it like you're sharing an interesting fact with a friend\n"
            "   - Include a fun detail or background context\n"
            "   - NEVER use phrases like: 'The text states', 'According to the text', 'The passage mentions'\n"
            "   - Just state the fact naturally and add context\n"
            "   - Example: Instead of 'The text states X happened in 1995', write 'X happened in 1995, marking a turning point...'\n"
            "\n"
            "CRITICAL: Do NOT hallucinate facts. Only use information from the provided text. "
            "If you cannot create a good question from the text, say so in the explanation."
        )
    )

def create_auditor_agent(use_fallback: bool = False):
    """
    Auditor Agent - Validates questions against source text
    
    Acts as a circuit breaker to ensure questions are verifiable.
    
    Args:
        use_fallback: If True, use the fallback model (slower but more reliable)
    """
    model = AUDITOR_FALLBACK if use_fallback else AUDITOR_MODEL
    
    return Agent(
        model,
        output_type=ValidationResult,
        system_prompt=(
            "You are the Auditor, a supreme validator of factual accuracy. "
            "You will receive:\n"
            "1. A multiple-choice question with 4 options\n"
            "2. The source text from Wikipedia\n"
            "\n"
            "Your task is to verify that:\n"
            "1. The correct answer is EXPLICITLY stated in the source text\n"
            "2. The question is not misleading or ambiguous\n"
            "3. The wrong answers are plausibly incorrect (not obviously wrong)\n"
            "4. No information is hallucinated or assumed\n"
            "\n"
            "If the question is valid:\n"
            "- Set is_valid=True\n"
            "- Set confidence to 0.8-1.0\n"
            "- Leave issues and correction_note as None\n"
            "\n"
            "If the question has issues:\n"
            "- Set is_valid=False\n"
            "- Set confidence to 0.0-0.7\n"
            "- Describe the specific issues found\n"
            "- Provide a correction_note with guidance on how to fix it\n"
            "\n"
            "Be strict but fair. The goal is to ensure every question is verifiable."
        )
    )

def create_relevance_agent(use_fallback: bool = False):
    """
    Relevance Agent - Scores Wikipedia links by thematic relevance
    
    Helps create a guided learning path through related topics.
    
    Args:
        use_fallback: If True, use the fallback model (slower but more reliable)
    """
    model = RELEVANCE_FALLBACK if use_fallback else RELEVANCE_MODEL
    
    return Agent(
        model,
        output_type=List[RelevanceScore],
        system_prompt=(
            "You are an expert at identifying thematically related topics. "
            "Given a quiz question and a list of Wikipedia page links, "
            "score each link based on how relevant it is to the question's topic. "
            "\n"
            "Return the top 5 most relevant links with:\n"
            "1. relevance_score: 0.0 to 1.0 (1.0 = highly relevant)\n"
            "2. reasoning: Brief explanation of why it's relevant\n"
            "\n"
            "Prioritize links that:\n"
            "- Are directly related to the question's subject\n"
            "- Would provide interesting follow-up learning\n"
            "- Are not too broad or too narrow\n"
            "\n"
            "Avoid:\n"
            "- Generic links (e.g., 'List of...', 'Category:...')\n"
            "- Overly broad topics\n"
            "- Completely unrelated topics\n"
            "\n"
            "Return exactly 3 links, ordered by relevance (highest first)."
        )
    )

# ============================================================================
# Legacy Agents (for backward compatibility)
# ============================================================================

RESEARCHER_MODEL = GoogleModel('models/gemini-3-flash-preview')
GIVER_MODEL = GoogleModel('models/gemini-3-flash-preview')

def create_researcher_agent():
    return Agent(
        RESEARCHER_MODEL,
        output_type=List[Fact],
        system_prompt=(
            "You are an expert researcher for a trivia game. "
            "Your goal is to find 3 distinct, obscure, but verifiable facts about the given topic. "
            "Each fact must be TRUE. "
            "Even if the inputted topic is broad, still try to keep the group of questions somewhat related to each other. "
            "Provide a valid source URL or citation for each. "
            "Set 'is_lie' to False for all of them."
        )
    )

def create_deceiver_agent():
    return Agent(
        RESEARCHER_MODEL,
        output_type=Fact,
        system_prompt=(
            "You are a master deceiver. You will receive a true fact. "
            "Your task is to rewrite it to be a plausible LIE. "
            "Change a specific detail (e.g., a date, a name, a number, or a cause) so it is factually incorrect but sounds believable. "
            "Do not make it obvious. "
            "Set 'is_lie' to True. "
            "Keep the source field as the original source (to make it look real), or invent a very plausible sounding one."
        )
    )
