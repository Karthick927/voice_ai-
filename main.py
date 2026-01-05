import os
import uuid
import streamlit as st
from groq import Groq
from elevenlabs import ElevenLabs
import tempfile
import base64
from dotenv import load_dotenv

# ===============================
# CONFIG
# ===============================
load_dotenv()

# Page config
st.set_page_config(
    page_title="Sana AI - Voice Call",
    page_icon="📞",
    layout="centered"
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #1a0033 0%, #330033 100%);
    }
    .main-title {
        text-align: center;
        color: #ff66ff;
        font-size: 3em;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        margin-bottom: 10px;
    }
    .subtitle {
        text-align: center;
        color: #cc99ff;
        font-style: italic;
        margin-bottom: 30px;
    }
    .call-status {
        text-align: center;
        font-size: 1.5em;
        color: #ff66ff;
        margin: 20px 0;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }
    .message-box {
        background-color: rgba(51, 0, 51, 0.5);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        border-left: 4px solid #ff66ff;
    }
</style>
""", unsafe_allow_html=True)


# ===============================
# INIT CLIENTS
# ===============================
@st.cache_resource
def init_clients():
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    eleven_client = ElevenLabs(api_key=st.secrets["ELEVENLABS_API_KEY"])
    return groq_client, eleven_client


groq, eleven = init_clients()

VOICE_ID = "flHkNRp1BlvT73UL6gyz"

SYSTEM_PROMPT = (
    "You are Sana, an eloquent villainess. "
    "Calm, confident, teasing, intelligent, slightly cruel. "
    "You always call the user 'senpai'. "
    "Your replies are concise but dramatic."
)


# ===============================
# FUNCTIONS
# ===============================
def ai_reply(user_text):
    completion = groq.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ],
        temperature=0.8
    )
    return completion.choices[0].message.content


def text_to_speech(text):
    """Generate audio and return bytes"""
    try:
        audio = eleven.text_to_speech.convert(
            voice_id=VOICE_ID,
            model_id="eleven_multilingual_v2",
            text=text,
            output_format="mp3_44100_128"
        )

        # Collect all audio chunks
        audio_bytes = b""
        for chunk in audio:
            audio_bytes += chunk

        return audio_bytes
    except Exception as e:
        st.error(f"Audio generation error: {str(e)}")
        return None


# ===============================
# SESSION STATE
# ===============================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "call_active" not in st.session_state:
    st.session_state.call_active = False
if "current_audio" not in st.session_state:
    st.session_state.current_audio = None

# ===============================
# UI
# ===============================
st.markdown('<h1 class="main-title">📞 Sana AI Voice Call</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Text to Sana, she replies with her voice...</p>', unsafe_allow_html=True)

# Call status
if st.session_state.call_active:
    st.markdown('<p class="call-status">🔴 Call Active - Sana is listening...</p>', unsafe_allow_html=True)
else:
    st.markdown('<p class="call-status">⚪ Ready to start call</p>', unsafe_allow_html=True)

# Sidebar controls
with st.sidebar:
    st.header("📞 Call Controls")

    if not st.session_state.call_active:
        if st.button("📞 Start Call", use_container_width=True):
            st.session_state.call_active = True
            st.session_state.messages = []
            st.rerun()
    else:
        if st.button("📴 End Call", use_container_width=True, type="primary"):
            st.session_state.call_active = False
            st.rerun()

    st.markdown("---")

    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown("### 💀 About Sana")
    st.markdown("*Calm, confident, teasing, intelligent, slightly cruel.*")
    st.markdown("She always calls you 'senpai'")
    st.markdown("---")
    st.markdown("**💬 How it works:**")
    st.markdown("1. Start the call")
    st.markdown("2. Type your message")
    st.markdown("3. Sana replies with voice automatically")

# Display conversation history
st.markdown("### 💬 Conversation")

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"""
        <div class="message-box" style="border-left-color: #66ccff;">
            <strong>🧑 You:</strong><br>
            {msg["content"]}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="message-box" style="border-left-color: #ff66ff;">
            <strong>💀 Sana:</strong><br>
            {msg["content"]}
        </div>
        """, unsafe_allow_html=True)

# Chat input (only show when call is active)
if st.session_state.call_active:
    st.markdown("---")

    # Show audio player if there's audio to play
    if st.session_state.current_audio:
        st.audio(st.session_state.current_audio, format='audio/mp3', autoplay=True)
        st.session_state.current_audio = None  # Clear after displaying

    prompt = st.chat_input("Type your message to Sana...")

    if prompt:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Show user message
        st.markdown(f"""
        <div class="message-box" style="border-left-color: #66ccff;">
            <strong>🧑 You:</strong><br>
            {prompt}
        </div>
        """, unsafe_allow_html=True)

        # Get AI response
        with st.spinner("💭 Sana is thinking..."):
            response = ai_reply(prompt)

        # Show Sana's response
        st.markdown(f"""
        <div class="message-box" style="border-left-color: #ff66ff;">
            <strong>💀 Sana:</strong><br>
            {response}
        </div>
        """, unsafe_allow_html=True)

        # Generate and play audio
        with st.spinner("🎤 Sana is speaking..."):
            audio_bytes = text_to_speech(response)
            if audio_bytes:
                st.session_state.current_audio = audio_bytes
                st.success("🔊 Sana is speaking!")

        # Save to history
        st.session_state.messages.append({"role": "assistant", "content": response})

        st.rerun()
else:
    st.info("📞 Click 'Start Call' to begin talking with Sana")

# Footer
st.markdown("---")
st.markdown(
    '<p style="text-align: center; color: #cc99ff; font-size: 0.9em;">'
    '💀 Sana awaits your words, senpai...'
    '</p>',
    unsafe_allow_html=True
)
