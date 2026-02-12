"""
New Game Manager for Wikipedia Quiz Game

This orchestrates all agents in sequence with correction loops.
"""
import logging
import asyncio
from typing import Optional, Dict
from datetime import datetime

from src.models import GameState, DebugLog
from src.wikipedia_client import WikipediaClient
from src.agents import (
    create_section_picker_agent,
    create_quiz_maker_agent,
    create_auditor_agent,
    create_relevance_agent
)
from src.citation_extractor import CitationExtractor

logger = logging.getLogger(__name__)

class WikiQuizGameManager:
    """
    Manages the Wikipedia Quiz Game flow with multi-agent orchestration
    """
    
    def __init__(self, max_correction_attempts: int = 3, debug_mode: bool = False):
        self.max_correction_attempts = max_correction_attempts
        self.debug_mode = debug_mode
        self.wiki_client = WikipediaClient()
        self.citation_extractor = CitationExtractor()
    
    def _map_sections_to_names(self, wiki_sections: Dict[str, str], selected_texts: list) -> Dict[int, str]:
        """
        Map selected section texts back to their original Wikipedia section names
        
        Args:
            wiki_sections: Dictionary of section_name -> section_content from Wikipedia
            selected_texts: List of selected section texts
            
        Returns:
            Dictionary mapping index -> section_name
        """
        mapping = {}
        
        for i, selected_text in enumerate(selected_texts):
            # Find which Wikipedia section this text came from
            for section_name, section_content in wiki_sections.items():
                # Check if the selected text is a substring of this section
                if selected_text.strip() in section_content:
                    mapping[i] = section_name
                    break
            
            # If not found, use a generic name
            if i not in mapping:
                mapping[i] = f"Section {i+1}"
        
        return mapping
    
    async def run_round(self, page_title: str) -> Optional[GameState]:
        """
        Run a complete quiz round for a Wikipedia page
        
        Args:
            page_title: Title of the Wikipedia page
            
        Returns:
            GameState with question, citation, and relevant links
        """
        logger.info(f"Starting quiz round for: {page_title}")
        
        # Initialize game state
        game_state = GameState(
            wikipedia_page_title=page_title,
            wikipedia_url="",  # Will be filled after fetching page
        )
        
        # Step 1: Fetch Wikipedia page
        page = self.wiki_client.get_page(page_title)
        if not page:
            logger.error(f"Could not fetch Wikipedia page: {page_title}")
            return None
        
        game_state.wikipedia_url = page.url
        logger.info(f"Fetched page: {page.title}")
        
        # Step 2: Section Picker - Extract dense paragraphs
        logger.info("Running Section Picker agent...")
        
        try:
            # Try primary model first
            section_picker = create_section_picker_agent(use_fallback=False)
            section_result = await section_picker.run(page.content)
            selected_sections = section_result.output
            game_state.selected_sections = selected_sections
            
            if self.debug_mode:
                game_state.debug_logs.append(DebugLog(
                    agent_name="Section Picker",
                    input_data=f"Page content ({len(page.content)} chars)",
                    output_data=f"{len(selected_sections.sections)} sections selected",
                    reasoning=selected_sections.reasoning,
                    timestamp=datetime.now().isoformat()
                ))
            
            logger.info(f"Selected {len(selected_sections.sections)} sections")
            
        except Exception as e:
            error_msg = str(e)
            # Check if it's a 503 error (API overload)
            if '503' in error_msg or 'high demand' in error_msg.lower():
                logger.warning(f"Primary model overloaded, trying fallback model...")
                try:
                    section_picker_fallback = create_section_picker_agent(use_fallback=True)
                    section_result = await section_picker_fallback.run(page.content)
                    selected_sections = section_result.output
                    game_state.selected_sections = selected_sections
                    logger.info(f"Fallback successful! Selected {len(selected_sections.sections)} sections")
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")
                    return None
            else:
                logger.error(f"Section Picker failed: {e}")
                return None
        
        # Map sections to their original Wikipedia section names
        section_mapping = self._map_sections_to_names(page.sections, selected_sections.sections)
        
        # Step 3: Quiz Maker + Auditor Correction Loop
        logger.info("Starting Quiz Maker + Auditor correction loop...")
        
        # Combine selected sections into one text
        combined_text = "\n\n".join(selected_sections.sections)
        
        question = None
        for attempt in range(1, self.max_correction_attempts + 1):
            logger.info(f"Correction loop attempt {attempt}/{self.max_correction_attempts}")
            game_state.correction_attempts = attempt
            
            # Run Quiz Maker
            quiz_maker = create_quiz_maker_agent()
            try:
                quiz_result = await quiz_maker.run(combined_text)
                question = quiz_result.output
                
                if self.debug_mode:
                    game_state.debug_logs.append(DebugLog(
                        agent_name=f"Quiz Maker (Attempt {attempt})",
                        input_data=f"Combined sections ({len(combined_text)} chars)",
                        output_data=question.question_text,
                        reasoning=question.explanation,
                        timestamp=datetime.now().isoformat()
                    ))
                
                logger.info(f"Quiz Maker generated question: {question.question_text[:100]}...")
                
            except Exception as e:
                logger.error(f"Quiz Maker failed on attempt {attempt}: {e}")
                if attempt == self.max_correction_attempts:
                    return None
                continue
            
            # Run Auditor for validation
            auditor = create_auditor_agent()
            try:
                # Prepare input for auditor
                auditor_input = {
                    "question": question.question_text,
                    "options": question.options,
                    "correct_answer": question.options[question.correct_answer_index],
                    "source_text": combined_text
                }
                
                audit_result = await auditor.run(str(auditor_input))
                validation = audit_result.output
                
                if self.debug_mode:
                    game_state.debug_logs.append(DebugLog(
                        agent_name=f"Auditor (Attempt {attempt})",
                        input_data=f"Question + source text",
                        output_data=f"Valid: {validation.is_valid}, Confidence: {validation.confidence}",
                        reasoning=validation.issues or "No issues found",
                        timestamp=datetime.now().isoformat()
                    ))
                
                logger.info(f"Auditor validation: valid={validation.is_valid}, confidence={validation.confidence}")
                
                # Check if validation passed
                if validation.is_valid and validation.confidence >= 0.8:
                    logger.info("Question validated successfully!")
                    game_state.question = question
                    break
                else:
                    logger.warning(f"Validation failed: {validation.issues}")
                    if attempt < self.max_correction_attempts:
                        logger.info(f"Retrying with correction note: {validation.correction_note}")
                        # In a more sophisticated implementation, we would pass the correction_note
                        # back to the Quiz Maker. For now, we just retry.
                        continue
                    else:
                        logger.error("Max correction attempts reached. Using best effort question.")
                        game_state.question = question
                        break
                        
            except Exception as e:
                logger.error(f"Auditor failed on attempt {attempt}: {e}")
                if attempt == self.max_correction_attempts:
                    # Use the question anyway
                    game_state.question = question
                    break
                continue
        
        if not game_state.question:
            logger.error("Failed to generate a valid question")
            return None
        
        # Step 4: Extract Source Citation
        logger.info("Extracting source citation...")
        try:
            correct_answer = game_state.question.options[game_state.question.correct_answer_index]
            
            # Try to find which section contains the answer
            section_name = "Wikipedia"
            section_url = page.url  # Default to page URL
            
            for i, section_text in enumerate(selected_sections.sections):
                if self.citation_extractor._contains_answer(section_text, correct_answer):
                    section_name = section_mapping.get(i, "Wikipedia")
                    # Create URL with section anchor
                    # Wikipedia section anchors use underscores instead of spaces
                    section_anchor = section_name.replace(" ", "_")
                    section_url = f"{page.url}#{section_anchor}"
                    break
            
            citation = self.citation_extractor.extract_citation_for_question(
                source_text=combined_text,
                question_text=game_state.question.question_text,
                correct_answer=correct_answer,
                section_title=section_name,
                section_url=section_url
            )
            
            if citation:
                game_state.source_citation = citation
                logger.info(f"Citation extracted: {citation.sentence[:100]}...")
            else:
                logger.warning("Could not extract citation")
                
        except Exception as e:
            logger.error(f"Citation extraction failed: {e}")
        
        # Step 5: Relevance Agent - Score links
        logger.info("Running Relevance Agent...")
        try:
            relevance_agent = create_relevance_agent()
            
            # Prepare input
            relevance_input = {
                "question": game_state.question.question_text,
                "available_links": page.links
            }
            
            relevance_result = await relevance_agent.run(str(relevance_input))
            relevance_scores = relevance_result.output
            
            game_state.available_links = relevance_scores[:3]  # Top 3
            
            if self.debug_mode:
                game_state.debug_logs.append(DebugLog(
                    agent_name="Relevance Agent",
                    input_data=f"Question + {len(page.links)} links",
                    output_data=f"{len(game_state.available_links)} relevant links selected",
                    reasoning=", ".join([f"{r.link_title} ({r.relevance_score:.2f})" for r in game_state.available_links]),
                    timestamp=datetime.now().isoformat()
                ))
            
            logger.info(f"Selected {len(game_state.available_links)} relevant links")
            
        except Exception as e:
            logger.error(f"Relevance Agent failed: {e}")
            # Continue without relevant links
        
        logger.info("Quiz round completed successfully!")
        return game_state
