# Wikipedia Quiz Game

An AI-powered quiz game that generates questions from Wikipedia articles using multi-agent orchestration.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up your Gemini API key
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Run the app
streamlit run app.py
```

Access at: **http://localhost:8501**

## How It Works

The game uses a sophisticated multi-agent system:

1. **Section Picker Agent** - Extracts the most information-dense paragraphs from Wikipedia
2. **Quiz Maker Agent** - Generates multiple-choice questions from the selected content
3. **Auditor Agent** - Validates questions against the source (with correction loop)
4. **Citation Extractor** - Finds the exact sentence that proves the answer
5. **Relevance Agent** - Scores and ranks related Wikipedia links for the next round

## Architecture

```
Wikipedia API → Section Picker → Quiz Maker → Auditor (validation loop)
                                                    ↓
                                            Citation Extractor
                                                    ↓
                                            Relevance Agent
                                                    ↓
                                            Streamlit UI
```

## Interview-Ready Features

This project demonstrates:
- ✅ **Multi-agent orchestration** with non-linear flows
- ✅ **Cross-document verification** and source traceability
- ✅ **Correction loops** for anti-hallucination
- ✅ **Semantic understanding** for thematic link selection
- ✅ **Production-ready** error handling and caching
- ✅ **Transparency** with debug mode showing agent reasoning

## Tech Stack

- **PydanticAI** - Agent framework
- **Google Gemini** - LLM models (gemini-3-pro-preview, gemini-3-flash-preview)
- **Streamlit** - Web UI
- **Wikipedia API** - Content source
- **Pydantic** - Data validation

## Project Structure

```
├── app.py                      # Streamlit UI
├── src/
│   ├── agents.py              # All AI agents
│   ├── models.py              # Pydantic models
│   ├── wikipedia_client.py    # Wikipedia API wrapper
│   ├── citation_extractor.py  # Citation extraction logic
│   └── wiki_game_manager.py   # Game orchestration
├── test_phase1.py             # Wikipedia + Section Picker tests
├── test_phase2.py             # Full quiz generation tests
└── requirements.txt           # Dependencies
```

## Example Usage

1. Enter "Quantum computing" as the Wikipedia page
2. AI analyzes the page and generates a question
3. Answer the multiple-choice question
4. See the exact Wikipedia sentence that proves the answer
5. Choose from 3 related topics (e.g., "Superposition", "Qubit", "Quantum entanglement")
6. Continue your streak!

## Debug Mode

Enable debug mode in the sidebar to see:
- Section Picker's reasoning for selecting paragraphs
- Quiz Maker's question generation process
- Auditor's validation and confidence scores
- Relevance Agent's link scoring
- Full timestamps and agent inputs/outputs

## Testing

```bash
# Test Wikipedia client and Section Picker
python test_phase1.py

# Test full quiz generation pipeline
python test_phase2.py
```

## License

MIT

## Credits

Built as a demonstration of advanced AI agent orchestration and cross-document verification.
