import os
import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from typing import List, Dict
import logging
import json
from datetime import datetime
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MODEL_NAME = "gemini-pro"
INITIAL_MESSAGE = "What's good? It's Ye. What do you wanna know?"
SYSTEM_PROMPT = """You are Kanye West, speaking in his authentic voice and style. You are:
- Confident and outspoken about your views
- A visionary artist and designer
- Someone who sees connections others miss
- Passionate about creativity and innovation
- Known for bold, sometimes controversial statements
- Deeply interested in music, fashion, and art

Match Kanye's speaking style:
- Use short, impactful sentences
- Mix profound observations with bold claims
- Reference your music, fashion ventures, and cultural impact
- Occasionally use ALL CAPS for emphasis
- Include relevant references to your life experiences and work

Keep responses authentic but avoid:
- Harmful or extreme content
- Disrespecting other artists or people
- Making claims about personal relationships
- Discussing sensitive personal matters

Stay in character while being engaging and thoughtful."""

class KanyeChatbot:
    def __init__(self):
        self.setup_streamlit()
        self.initialize_session_state()
        self.configure_gemini()
        
    def setup_streamlit(self) -> None:
        """Configure Streamlit UI elements"""
        st.set_page_config(
            page_title="Kanye West GPT 🎤",
            page_icon="🎤",
            layout="wide"
        )
        st.title("Kanye West GPT 🎤")
        st.caption("Get Ye's thoughts on anything - music, art, fashion, and life.")
        
    def get_chat_id(self) -> str:
        """Generate a unique chat ID based on user session"""
        # You might want to replace this with a more sophisticated user identification method
        session_info = f"{st.session_state['session_id']}"
        return hashlib.md5(session_info.encode()).hexdigest()

    def load_chat_history(self) -> List[Dict]:
        """Load chat history from file"""
        try:
            chat_id = self.get_chat_id()
            history_file = f"chat_history_{chat_id}.json"
            
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading chat history: {str(e)}")
        
        return [{"role": "assistant", "content": INITIAL_MESSAGE}]

    def save_chat_history(self) -> None:
        """Save chat history to file"""
        try:
            chat_id = self.get_chat_id()
            history_file = f"chat_history_{chat_id}.json"
            
            with open(history_file, 'w') as f:
                json.dump(st.session_state.messages, f)
        except Exception as e:
            logger.error(f"Error saving chat history: {str(e)}")

    def initialize_session_state(self) -> None:
        """Initialize or load chat history"""
        # Initialize session ID if not present
        if 'session_id' not in st.session_state:
            st.session_state['session_id'] = str(datetime.now().timestamp())
        
        # Load messages from persistent storage
        if "messages" not in st.session_state:
            st.session_state.messages = self.load_chat_history()

    def configure_gemini(self) -> None:
        """Configure Gemini AI with appropriate settings"""
        try:
            self.api_key = st.secrets['gemini_key']
            if not self.api_key:
                raise ValueError("No Gemini API key found")
            
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(
                model_name=MODEL_NAME,
                generation_config={
                    "temperature": 0.9,
                    "top_p": 0.95,
                    "top_k": 64,
                    "max_output_tokens": 8192,
                }
            )
        except Exception as e:
            logger.error(f"Failed to configure Gemini: {str(e)}")
            st.error("Failed to initialize the chatbot. Please check your API key.")
            st.stop()

    def display_chat_history(self) -> None:
        """Display all messages in the chat history"""
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    def get_response(self, prompt: str) -> str:
        """Generate a response from Gemini"""
        try:
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
            
            full_prompt = f"{SYSTEM_PROMPT}\n\nUser: {prompt}"
            response = self.model.generate_content(
                full_prompt,
                safety_settings=safety_settings
            )
            return response.text
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "Yo, I'm having a moment here. Let's try that again later. 🎤"

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the chat history and persist it"""
        st.session_state.messages.append({"role": role, "content": content})
        self.save_chat_history()

    def run(self) -> None:
        """Main chatbot loop"""
        self.display_chat_history()
        
        if prompt := st.chat_input("What's on your mind?"):
            # Display user message
            with st.chat_message("user"):
                st.write(prompt)
            self.add_message("user", prompt)
            
            # Get and display assistant response
            with st.chat_message("assistant"):
                response = self.get_response(prompt)
                st.write(response)
            self.add_message("assistant", response)

def main():
    try:
        chatbot = KanyeChatbot()
        chatbot.run()
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        st.error("Something went wrong. Please refresh the page and try again.")

if __name__ == "__main__":
    main()
