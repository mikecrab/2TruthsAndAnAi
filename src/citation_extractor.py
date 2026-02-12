import logging
from typing import Optional, List
from src.models import SourceCitation

logger = logging.getLogger(__name__)

class CitationExtractor:
    """
    Extracts exact sentences from Wikipedia that justify quiz answers
    
    This provides traceability and proves that answers are verifiable.
    """
    
    def extract_citation(
        self, 
        source_text: str, 
        answer_text: str,
        section_title: str = "Unknown",
        section_url: str = ""
    ) -> Optional[SourceCitation]:
        """
        Find the exact sentence in source_text that contains the answer
        
        Args:
            source_text: The Wikipedia text to search
            answer_text: The answer to find
            section_title: Title of the section being searched
            section_url: URL to the Wikipedia section
            
        Returns:
            SourceCitation with exact sentence and position, or None if not found
        """
        # Split into sentences (simple approach)
        sentences = self._split_into_sentences(source_text)
        
        # Search for the sentence containing the answer
        for idx, sentence in enumerate(sentences):
            if self._contains_answer(sentence, answer_text):
                logger.info(f"Found citation in sentence {idx}: {sentence[:100]}...")
                return SourceCitation(
                    sentence=sentence.strip(),
                    section_title=section_title,
                    section_url=section_url,
                    sentence_index=idx
                )
        
        logger.warning(f"Could not find citation for answer: {answer_text}")
        return None
    
    def extract_citation_for_question(
        self,
        source_text: str,
        question_text: str,
        correct_answer: str,
        section_title: str = "Unknown",
        section_url: str = ""
    ) -> Optional[SourceCitation]:
        """
        Find the sentence that supports the correct answer to a question
        
        This is more sophisticated - it looks for sentences that contain
        information relevant to both the question and answer.
        """
        sentences = self._split_into_sentences(source_text)
        
        # First pass: find sentences containing the answer
        candidates = []
        for idx, sentence in enumerate(sentences):
            if self._contains_answer(sentence, correct_answer):
                candidates.append((idx, sentence))
        
        if not candidates:
            logger.warning(f"No sentences found containing answer: {correct_answer}")
            return None
        
        # If only one candidate, return it
        if len(candidates) == 1:
            idx, sentence = candidates[0]
            return SourceCitation(
                sentence=sentence.strip(),
                section_title=section_title,
                section_url=section_url,
                sentence_index=idx
            )
        
        # Multiple candidates: try to find the best match
        # For now, just return the first one
        # TODO: Could use semantic similarity here
        idx, sentence = candidates[0]
        logger.info(f"Found {len(candidates)} candidate sentences, using first one")
        return SourceCitation(
            sentence=sentence.strip(),
            section_title=section_title,
            section_url=section_url,
            sentence_index=idx
        )
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences
        
        Simple approach: split on '. ' but handle some edge cases
        """
        # Replace common abbreviations to avoid false splits
        text = text.replace('Dr.', 'Dr')
        text = text.replace('Mr.', 'Mr')
        text = text.replace('Mrs.', 'Mrs')
        text = text.replace('Ms.', 'Ms')
        text = text.replace('Prof.', 'Prof')
        text = text.replace('Sr.', 'Sr')
        text = text.replace('Jr.', 'Jr')
        text = text.replace('U.S.', 'US')
        text = text.replace('U.K.', 'UK')
        
        # Split on sentence boundaries
        sentences = []
        current = []
        
        for char in text:
            current.append(char)
            if char in '.!?' and len(current) > 1:
                sentence = ''.join(current).strip()
                if len(sentence) > 10:  # Ignore very short "sentences"
                    sentences.append(sentence)
                current = []
        
        # Add remaining text
        if current:
            sentence = ''.join(current).strip()
            if len(sentence) > 10:
                sentences.append(sentence)
        
        return sentences
    
    def _contains_answer(self, sentence: str, answer: str) -> bool:
        """
        Check if sentence contains the answer
        
        Uses case-insensitive substring matching
        """
        sentence_lower = sentence.lower()
        answer_lower = answer.lower()
        
        # Direct substring match
        if answer_lower in sentence_lower:
            return True
        
        # Try matching individual words (for multi-word answers)
        answer_words = answer_lower.split()
        if len(answer_words) > 1:
            # Check if all words appear in the sentence
            return all(word in sentence_lower for word in answer_words if len(word) > 2)
        
        return False
