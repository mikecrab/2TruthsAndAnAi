import os
from dotenv import load_dotenv

# Load environment variables FIRST before importing anything from src/
load_dotenv()

# PydanticAI expects GOOGLE_API_KEY for Gemini models
# If GEMINI_API_KEY is present but GOOGLE_API_KEY is not, copy it over.
if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

# Force anyio to use asyncio
os.environ["ANYIO_BACKEND"] = "asyncio"

import streamlit as st

import asyncio
import anyio
import logging
import sys

# Configure logging to stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger("streamlit_app")

# Now it is safe to import src modules which initialize Agents
from src.game_manager import GameManager
from src.models import GameState

st.set_page_config(page_title="Two Truths and an AI", layout="wide")

# Custom CSS for highlights
st.markdown("""
<style>
.highlight-lie {
    background-color: #ffcccc;
    padding: 2px 5px;
    border-radius: 3px;
    color: #990000;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

st.title("Two Truths and an AI 🤖")
st.markdown("### A Multi-Agent Verification Game")

# Initialize Session State
if "game_state" not in st.session_state:
    st.session_state.game_state = None
if "presented_facts" not in st.session_state:
    st.session_state.presented_facts = []
if "user_guess" not in st.session_state:
    st.session_state.user_guess = None
if "revealed" not in st.session_state:
    st.session_state.revealed = False

# Streak Mode State
if "streak_score" not in st.session_state:
    st.session_state.streak_score = 0
if "streak_active" not in st.session_state:
    st.session_state.streak_active = False
if "game_over" not in st.session_state:
    st.session_state.game_over = False
if "load_next_round" not in st.session_state:
    st.session_state.load_next_round = False
if "next_round_state" not in st.session_state:
    st.session_state.next_round_state = None

# Display current score if streak is active
if st.session_state.streak_active:
    st.metric("Current Streak", st.session_state.streak_score, help="Correct answers in a row")
    st.info("🎮 Streak mode active! Keep going until you get one wrong.")
    # Use the last topic from session state
    if "current_topic" not in st.session_state:
        st.session_state.current_topic = "Quantum Physics"
    topic = st.session_state.current_topic
else:
    # Only show topic input when not in active streak
    topic = st.text_input("Enter a topic:", "Quantum Physics")
    st.session_state.current_topic = topic



# Handle loading next round after correct answer
if st.session_state.get("load_next_round", False):
    st.session_state.load_next_round = False
    
    # Reset state for next round
    st.session_state.game_state = None
    st.session_state.presented_facts = []
    st.session_state.user_guess = None
    st.session_state.revealed = False
    
    # Load next round
    async def run_full_game():
        manager = GameManager()
        with st.spinner(f"Loading next round... Streak: {st.session_state.streak_score}"):
            game_state = await manager.run_round(topic)
        
        if not game_state:
            return None
        
        return game_state
    
    try:
        game_state = anyio.run(run_full_game)
    except Exception as e:
        import traceback
        error_msg = str(e)
        
        # Handle specific API errors gracefully
        if "503" in error_msg or "UNAVAILABLE" in error_msg:
            st.error("⚠️ **API Temporarily Unavailable**\n\nThe Gemini API is experiencing high demand. Your streak has ended.\n\nPlease try again in a few moments.")
            logger.error(f"503 Service Unavailable during streak: {e}")
        elif "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            st.error("⚠️ **Rate Limit Exceeded**\n\nYou've hit the API rate limit. Your streak has ended.\n\nPlease wait a moment and try again.")
            logger.error(f"429 Rate Limit during streak: {e}")
        elif "404" in error_msg:
            st.error("⚠️ **Model Not Found**\n\nThe configured model is not available. Your streak has ended.")
            logger.error(f"404 Model Not Found during streak: {e}")
        else:
            st.error(f"⚠️ **Error Loading Next Round**\n\n{error_msg}\n\nYour streak has ended.")
            logger.error(f"Error loading next round: {e}\n{traceback.format_exc()}")
        
        game_state = None
        st.session_state.game_over = True
    
    if game_state:
        st.session_state.game_state = game_state
        st.session_state.presented_facts = []  # No presentations needed
        st.rerun()



# Only show Start Round button when not in active streak
if not st.session_state.streak_active:
    if st.button("Start Round"):
        logger.info("Start Round button clicked.")
        try:
            loop = asyncio.get_running_loop()
            logger.info(f"Event loop inside button callback: {loop}")
        except RuntimeError:
            logger.info("No event loop inside button callback.")

        # Reset state

        st.session_state.game_state = None
        st.session_state.presented_facts = []
        st.session_state.user_guess = None
        st.session_state.revealed = False
        
        # Run game and generate presentations in a single async context
        async def run_full_game():
            # Generate game state
            manager = GameManager()
            with st.spinner(f"Researching & Auditing '{topic}'... (This may take a moment if the Auditor rejects hallucinations)"):
                game_state = await manager.run_round(topic)
            
            if not game_state:
                return None
            
            return game_state
        
        # Use anyio.run to ensure PydanticAI works correctly with its backend auto-detection
        try:
            game_state = anyio.run(run_full_game)
        except Exception as e:
            import traceback
            error_msg = str(e)
            
            # Handle specific API errors gracefully
            if "503" in error_msg or "UNAVAILABLE" in error_msg:
                st.error("⚠️ **API Temporarily Unavailable**\n\nThe Gemini API is experiencing high demand. Please try again in a few moments.")
                logger.error(f"503 Service Unavailable: {e}")
            elif "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                st.error("⚠️ **Rate Limit Exceeded**\n\nYou've hit the API rate limit. Please wait a moment and try again.")
                logger.error(f"429 Rate Limit: {e}")
            elif "404" in error_msg:
                st.error("⚠️ **Model Not Found**\n\nThe configured model is not available. Please check your model configuration.")
                logger.error(f"404 Model Not Found: {e}")
            else:
                st.error(f"⚠️ **Error**\n\n{error_msg}")
                logger.error(f"Error running game: {e}\n{traceback.format_exc()}")
            
            game_state = None
        
        if game_state:
            st.session_state.game_state = game_state
            st.session_state.presented_facts = []  # No presentations needed
            st.rerun()
        # Don't show additional error if we already showed one above


# Display Game Interface
# ... existing code ...

# Display Game Interface
if st.session_state.game_state:
    gameState = st.session_state.game_state
    
    st.divider()
    st.subheader("Which one is the AI Hallucination?")
    
    col1, col2, col3 = st.columns(3)
    
    cols = [col1, col2, col3]
    
    for i, col in enumerate(cols):
        with col:
            st.markdown(f"### Statement #{i + 1}")
            # Display fact content directly
            st.info(gameState.game_facts[i].content)
            
            if not st.session_state.get("revealed", False):
                if st.button("Call Bullshit", key=f"btn_{i}"):
                    st.session_state.user_guess = i
                    st.session_state.revealed = True
                    st.rerun()
    
    # Background load next round while user is viewing current question
    if not st.session_state.get("revealed", False) and st.session_state.streak_active:
        if "next_round_state" not in st.session_state or st.session_state.next_round_state is None:
            with st.spinner("Pre-loading next round..."):
                async def load_next_round():
                    manager = GameManager()
                    return await manager.run_round(topic)
                
                try:
                    next_game_state = anyio.run(load_next_round)
                    st.session_state.next_round_state = next_game_state
                    logger.info("Next round pre-loaded successfully")
                except Exception as e:
                    logger.error(f"Error pre-loading next round: {e}")
                    st.session_state.next_round_state = None
    
    # Reveal Phase
    if st.session_state.get("revealed", False):
        st.divider()
        
        actual_lie_index = -1
        for idx, f in enumerate(gameState.game_facts):
            if f.is_lie:
                actual_lie_index = idx
                break
        
        user_guess = st.session_state.user_guess
        is_correct = (user_guess == actual_lie_index)
        
        if is_correct:
            # Correct answer - show success and Auditor reasoning
            st.session_state.streak_score += 1
            st.session_state.streak_active = True
            st.success(f"🎉 Correct! Streak: {st.session_state.streak_score}")
            
            # Show Auditor's reasoning
            st.markdown("### 🔍 Auditor's Analysis")
            st.info(f"**Why it's false:** {gameState.auditor_verdict.reasoning}")
            
            # Show Next button to continue (round should already be pre-loaded)
            if st.button("➡️ Next Round", type="primary"):
                # Use pre-loaded round if available
                if st.session_state.get("next_round_state"):
                    st.session_state.game_state = st.session_state.next_round_state
                    st.session_state.next_round_state = None  # Clear for next time
                    st.session_state.presented_facts = []
                    st.session_state.user_guess = None
                    st.session_state.revealed = False
                    st.rerun()
                else:
                    # Fallback: load on demand if pre-load failed
                    st.session_state.load_next_round = True
                    st.session_state.revealed = False
                    st.rerun()
        else:
            # Wrong answer - game over
            st.error(f"❌ Wrong! The lie was Statement #{actual_lie_index + 1}.")
            st.markdown(f"### Game Over! Final Score: {st.session_state.streak_score}")
            st.session_state.game_over = True
            st.session_state.next_round_state = None  # Clear pre-loaded round since streak ended
            
            # Show play again button
            if st.button("Play Again"):
                st.session_state.streak_score = 0
                st.session_state.streak_active = False
                st.session_state.game_over = False
                st.session_state.game_state = None
                st.session_state.presented_facts = []
                st.session_state.user_guess = None
                st.session_state.revealed = False
                st.session_state.load_next_round = False
                st.session_state.next_round_state = None  # Clear pre-loaded round
                st.rerun()
            
        st.markdown("### Auditor's Report")
        verdict = gameState.auditor_verdict
        
        st.markdown(f"**Confidence Score:** `{verdict.confidence}`")
        st.markdown(f"**Reasoning:** {verdict.reasoning}")
        
        # Highlight Logic
        lie_content = gameState.game_facts[actual_lie_index].content
        if verdict.highlight_start is not None and verdict.highlight_end is not None:
             start = verdict.highlight_start
             end = verdict.highlight_end
             # Ensure indices are valid
             if 0 <= start < end <= len(lie_content):
                 highlighted = (
                     lie_content[:start] + 
                     f"<span class='highlight-lie'>{lie_content[start:end]}</span>" + 
                     lie_content[end:]
                 )
                 st.markdown(f"**The Lie:** {highlighted}", unsafe_allow_html=True)
             else:
                 st.markdown(f"**The Lie:** {lie_content}")
        else:
             st.markdown(f"**The Lie:** {lie_content}")

        st.markdown("### Ground Truth Data")
        with st.expander("Show Original Sources"):
            for f in gameState.game_facts:
                if f.is_lie:
                    st.write(f"❌ **Fabrication**: {f.content}")
                else:
                    st.write(f"✅ **Fact**: {f.content} | [Source]({f.source})")
