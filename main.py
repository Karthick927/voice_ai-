import os
import uuid
import streamlit as st
from groq import Groq
from elevenlabs import ElevenLabs
import base64
from dotenv import load_dotenv

# ===============================
# CONFIG
# ===============================
load_dotenv()

st.set_page_config(
    page_title="Sana AI - Voice Call",
    page_icon="📞",
    layout="centered"
)

# Custom CSS
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #1a0033 0%, #330033 100%); }
    .main-title { text-align: center; color: #ff66ff; font-size: 3em; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); margin-bottom: 10px; }
    .subtitle { text-align: center; color: #cc99ff; font-style: italic; margin-bottom: 30px; }
    .call-status { text-align: center; font-size: 1.5em; color: #ff66ff; margin: 20px 0; animation: pulse 2s infinite; }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
    .message-box { background-color: rgba(51, 0, 51, 0.5); border-radius: 15px; padding: 20px; margin: 10px 0; border-left: 4px solid #ff66ff; }
</style>
""", unsafe_allow_html=True)

# ===============================
# INIT CLIENTS
# ===============================
@st.cache_resource
def init_clients():
    # Use st.secrets for deployed apps, fall back to environment variables for local testing
    groq_api = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
    eleven_api = st.secrets.get("ELEVENLABS_API_KEY") or os.getenv("ELEVENLABS_API_KEY")
    
    return Groq(api_key=groq_api), ElevenLabs(api_key=eleven_api)

groq, eleven = init_clients()
VOICE_ID = "flHkNRp1BlvT73UL6gyz"
SYSTEM_PROMPT = "You are Sana, an eloquent villainess. Calm, confident, teasing, intelligent, slightly cruel. You always call the user 'senpai'. Your replies are concise but dramatic."

# ===============================
# FUNCTIONS
# ===============================
def ai_reply(user_text):
    completion = groq.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.messages[-5:] + [{"role": "user", "content": user_text}],
        temperature=0.8
    )
    return completion.choices[0].message.content

def text_to_speech(text):
    try:
        audio = eleven.text_to_speech.convert(
            voice_id=VOICE_ID,
            model_id="eleven_multilingual_v2",
            text=text,
            output_format="mp3_44100_128"
        )
        audio_bytes = b"".join([chunk for chunk in audio])
        return audio_bytes
    except Exception as e:
        st.error(f"Audio generation error: {str(e)}")
        return None

def autoplay_audio(audio_bytes):
    """Bypasses browser autoplay blocks using Base64 injection"""
    b64 = base64.b64encode(audio_bytes).decode()
    md = f"""
        <audio autoplay="true">
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
    """
    st.markdown(md, unsafe_allow_html=True)

# ===============================
# SESSION STATE
# ===============================
if "messages" not in st.session_state: st.session_state.messages = []
if "call_active" not in st.session_state: st.session_state.call_active = False

# ===============================
# UI
# ===============================
st.markdown('<h1 class="main-title">📞 Sana AI Voice Call</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Text to Sana, she replies with her voice...</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("📞 Call Controls")
    if not st.session_state.call_active:
        if st.button("📞 Start Call", use_container_width=True):
            st.session_state.call_active = True
            st.rerun()
    else:
        if st.button("📴 End Call", use_container_width=True, type="primary"):
            st.session_state.call_active = False
            st.rerun()
    
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Display logic
if st.session_state.call_active:
    st.markdown('<p class="call-status">🔴 Call Active - Sana is listening...</p>', unsafe_allow_html=True)
    
    # History Container
    for msg in st.session_state.messages:
        color = "#66ccff" if msg["role"] == "user" else "#ff66ff"
        label = "🧑 You" if msg["role"] == "user" else "💀 Sana"
        st.markdown(f'<div class="message-box" style="border-left-color: {color};"><strong>{label}:</strong><br>{msg["content"]}</div>', unsafe_allow_html=True)

    # Input
    prompt = st.chat_input("Type your message to Sana...")

    if prompt:
        # 1. User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.markdown(f'<div class="message-box" style="border-left-color: #66ccff;"><strong>🧑 You:</strong><br>{prompt}</div>', unsafe_allow_html=True)

        # 2. AI Response
        with st.spinner("💭 Sana is thinking..."):
            response = ai_reply(prompt)
        
        st.markdown(f'<div class="message-box" style="border-left-color: #ff66ff;"><strong>💀 Sana:</strong><br>{response}</div>', unsafe_allow_html=True)
        st.session_state.messages.append({"role": "assistant", "content": response})

        # 3. Voice Generation & Autoplay
        with st.spinner("🎤 Sana is speaking..."):
            audio_data = text_to_speech(response)
            if audio_data:
                autoplay_audio(audio_data) # Trigger immediate play
else:
    st.info("📞 Click 'Start Call' to begin talking with Sana")
