import wikipedia
import logging
from typing import Optional, List, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class WikipediaPage:
    """Represents a Wikipedia page with metadata"""
    title: str
    url: str
    content: str
    summary: str
    links: List[str]
    sections: Dict[str, str]  # section_title -> section_content

class WikipediaClient:
    """Wrapper for Wikipedia API with error handling and caching"""
    
    def __init__(self):
        # Set language to English
        wikipedia.set_lang("en")
        self._cache: Dict[str, WikipediaPage] = {}
    
    def get_page(self, title: str, auto_suggest: bool = False) -> Optional[WikipediaPage]:
        """
        Fetch a Wikipedia page by title
        
        Args:
            title: Wikipedia page title
            auto_suggest: Whether to auto-suggest similar titles
            
        Returns:
            WikipediaPage object or None if page not found
        """
        # Check cache first
        if title in self._cache:
            logger.info(f"Cache hit for page: {title}")
            return self._cache[title]
        
        try:
            logger.info(f"Fetching Wikipedia page: {title}")
            page = wikipedia.page(title, auto_suggest=auto_suggest)
            
            # Parse sections
            sections = self._parse_sections(page.content)
            
            wiki_page = WikipediaPage(
                title=page.title,
                url=page.url,
                content=page.content,
                summary=page.summary,
                links=page.links[:50],  # Limit to first 50 links
                sections=sections
            )
            
            # Cache the result
            self._cache[title] = wiki_page
            logger.info(f"Successfully fetched page: {page.title}")
            
            return wiki_page
            
        except wikipedia.exceptions.DisambiguationError as e:
            logger.warning(f"Disambiguation page for '{title}'. Options: {e.options[:5]}")
            # Try the first option
            if e.options:
                return self.get_page(e.options[0], auto_suggest=False)
            return None
            
        except wikipedia.exceptions.PageError as e:
            logger.error(f"Page not found: {title}. Error: {e}")
            # Try with auto_suggest if not already tried
            if not auto_suggest:
                logger.info(f"Retrying with auto_suggest=True")
                try:
                    return self.get_page(title, auto_suggest=True)
                except:
                    pass
            return None
            
        except Exception as e:
            logger.error(f"Error fetching Wikipedia page '{title}': {e}")
            return None
    
    def get_random_page(self) -> Optional[WikipediaPage]:
        """Get a random Wikipedia page"""
        try:
            random_title = wikipedia.random(1)
            return self.get_page(random_title)
        except Exception as e:
            logger.error(f"Error getting random page: {e}")
            return None
    
    def search(self, query: str, limit: int = 5) -> List[str]:
        """
        Search Wikipedia for pages matching query
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of page titles
        """
        try:
            results = wikipedia.search(query, results=limit)
            logger.info(f"Search for '{query}' returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error searching Wikipedia: {e}")
            return []
    
    def _parse_sections(self, content: str) -> Dict[str, str]:
        """
        Parse Wikipedia page content into sections
        
        Args:
            content: Full page content
            
        Returns:
            Dictionary mapping section titles to content
        """
        sections = {}
        current_section = "Introduction"
        current_content = []
        
        lines = content.split('\n')
        
        for line in lines:
            # Check if line is a section header (starts with ==)
            if line.startswith('==') and line.endswith('=='):
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                current_section = line.strip('= ').strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
