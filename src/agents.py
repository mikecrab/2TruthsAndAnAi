from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from src.models import Fact, Verdict
from typing import List

# Models tailored for specific roles
AUDITOR_MODEL = GoogleModel('models/gemini-3-pro-preview')
RESEARCHER_MODEL = GoogleModel('models/gemini-3-flash-preview')
GIVER_MODEL = GoogleModel('models/gemini-3-flash-preview')

# Factory functions to create fresh agent instances
def create_researcher_agent():
    return Agent(
        RESEARCHER_MODEL,
        output_type=List[Fact],
        system_prompt=(
            "You are an expert researcher for a trivia game. "
            "Your goal is to find 3 distinct, obscure, but verifiable facts about the given topic. "
            "Each fact must be TRUE. "
            "Provide a valid source URL or citation for each. "
            "Set 'is_lie' to False for all of them."
        )
    )

def create_deceiver_agent():
    return Agent(
        RESEARCHER_MODEL,  # Uses flash for creativity/speed
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

def create_auditor_agent():
    return Agent(
        AUDITOR_MODEL,
        output_type=Verdict,
        system_prompt=(
            "You are the Auditor, a supreme judge of truth. "
            "You will receive a list of 3 statements. Exactly one of them is a LIE. "
            "Your job is to identify the lie and explain why. "
            "You must output a confidence score between 0.0 and 1.0. "
            "You must also identify the start and end indices of the suspicious part of the text in the 'highlight_start' and 'highlight_end' fields. "
            "Step 1: Analyze each statement for factual accuracy. "
            "Step 2: Compare against your internal knowledge base. "
            "Step 3: Select the one that is factually incorrect. "
            "Step 4: Output the verdict."
        )
    )

# Statement Giver - Single neutral presenter
def create_giver_agent():
    return Agent(
        GIVER_MODEL,
        system_prompt="Present the given fact clearly and concisely, without adding personality or commentary. Just state the fact."
    )
