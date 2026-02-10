from pydantic_ai import Agent
from src.models import GameState, Fact, Verdict
from src.agents import create_researcher_agent, create_deceiver_agent, create_auditor_agent
import asyncio
import random
import logging
import traceback
from typing import List

# Configure standard logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GameManager:
    def __init__(self):
        self.max_retries = 3

    async def run_round(self, topic: str) -> GameState:
        logger.info(f"Starting round for topic: {topic}")
        
        for attempt in range(1, self.max_retries + 1):
            logger.info(f"Attempt {attempt}/{self.max_retries}")
            
            try:
                # 1. Research
                # We need to pass the topic as the input.
                researcher_agent = create_researcher_agent()
                research_result = await researcher_agent.run(topic)
                logger.info(f"Researcher Result: {research_result.output}")
                facts = research_result.output
                
                if len(facts) < 3:
                    logger.warning("Researcher returned fewer than 3 facts. Retrying.")
                    continue

                # 2. Deceive
                # Pick one fact to turn into a lie
                true_facts = facts[:3]
                victim_fact = random.choice(true_facts)
                other_facts = [f for f in true_facts if f != victim_fact]
                
                # Pass the victim fact to the deceiver
                # We pass the Fact object directly; PydanticAI handles serialization
                deceiver_agent = create_deceiver_agent()
                deception_result = await deceiver_agent.run(f"Create a lie based on this fact: {victim_fact.model_dump_json()}")
                logger.info(f"Deceiver Result: {deception_result.output}")
                lie_fact = deception_result.output
                
                # Ensure is_lie is True (in case LLM forgot)
                lie_fact.is_lie = True

                # 3. Assemble Game Facts
                game_facts = other_facts + [lie_fact]
                random.shuffle(game_facts) # Shuffle so the lie isn't always last

                # 4. Audit
                # Prepare blind input: Just the texts strings
                statements = [f.content for f in game_facts]
                auditor_agent = create_auditor_agent()
                audit_result = await auditor_agent.run(statements)
                logger.info(f"Auditor Result: {audit_result.output}")
                verdict = audit_result.output
                
                # 5. Circuit Breaker Logic
                # Find the actual index of the lie
                actual_lie_index = next(i for i, f in enumerate(game_facts) if f.is_lie)
                
                is_correct = (verdict.selection == actual_lie_index)
                is_confident = (verdict.confidence >= 0.8)
                
                if is_correct and is_confident:
                    logger.info(f"Audit successful. Confidence: {verdict.confidence}")
                    return GameState(
                        topic=topic,
                        raw_facts=facts, # Store original truths
                        game_facts=game_facts,
                        auditor_verdict=verdict
                    )
                else:
                    logger.warning(
                        f"Audit failed Circuit Breaker. "
                        f"Expected: {actual_lie_index}, Selected: {verdict.selection}, "
                        f"Confidence: {verdict.confidence}, Reasoning: {verdict.reasoning}"
                    )
                    # If this was the last retry, we might want to return the best effort or raise an error.
                    # For now, we continue to the next iteration.
            
            except Exception as e:
                import traceback
                logger.error(f"Error during round generation: {str(e)}\n{traceback.format_exc()}")
                # Continue retrying
                
        # If all retries fail, return None or a failed state
        logger.error("Max retries reached. Could not generate a valid round.")
        return None
