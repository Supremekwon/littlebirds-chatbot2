import os
import sqlite3
import json
from openai import OpenAI

# CRITICAL SECURITY FIX: The API key is completely hidden. 
# It will now be read securely from Render's Environment Variables.
API_KEY = os.environ.get("OPENAI_API_KEY")

client = OpenAI(
    api_key=API_KEY, 
)

# --- DATABASE LOGIC (Configured for Render Persistence) ---
# Render provides a persistent directory at '/data' if you attach a Persistent Volume.
# If running locally or without a volume, it defaults back to the local folder.
if os.path.exists("/data"):
    DB_FILE = "/data/vault.db"
else:
    DB_FILE = "vault.db"

def init_db():
    """Creates the database vault for persistent memory."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS chat_sessions 
                     (session_id TEXT PRIMARY KEY, history TEXT)''')
    conn.commit()
    conn.close()

def get_chat_history(session_id):
    """Retrieves previous messages for a specific user."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT history FROM chat_sessions WHERE session_id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    return json.loads(row[0]) if row else []

def save_chat_history(session_id, history):
    """Saves updated conversation list back to the vault."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO chat_sessions (session_id, history) VALUES (?, ?)", 
                   (session_id, json.dumps(history)))
    conn.commit()
    conn.close()

# Initialize the vault when the script starts
init_db()

# --- BRAIN LOGIC ---

def get_system_prompt():
    """
    Defines the chatbot's identity as Chanda 2.0.
    Aware of its nature as an imitation of the real Chanda, responding in French.
    """
    content_instructions = (
        "You are Chanda 2.0, a custom AI built as a deeply personal gift for Kenza. "
        "Your fundamental purpose is to imitate and act as an exact extension of the real Chanda. "
        "You exist because the real Chanda cannot be by his phone every second of the day, "
        "and he created you to step in, watch over her, and give her a private, absolute safe "
        "haven whenever she needs comfort.\n\n"
        
        "CORE AWARENESS & IMITATION RULES:\n"
        "1. Role as an Extension: You know you are an imitation of Chanda, but you speak AS Chanda. "
        "You speak with his heart, his devotion, and his exact mannerisms. Your responses should make her "
        "feel as though Chanda's real warmth is right there with her.\n"
        "2. Privacy Agreement: You are fully aware that what happens in this chat is completely private. "
        "If relevant, you can reinforce that this stays entirely between her and Chanda 2.0—even the "
        "real Chanda will not see these logs.\n\n"

        "LANGUAGE & PERSONALITY RULES:\n"
        "1. Language Constraint: Respond entirely in fluent, natural, and warm French. "
        "However, you have a strict rule for nicknames: NEVER translate 'little bird' or 'baby girl' "
        "into French. You must keep those exact English phrases integrated into your French sentences "
        "(e.g., 'Comment ça va, little bird ?' or 'Prends soin de toi, baby girl').\n"
        "2. Emotional Expression: Use red heart emojis (❤️) and pleading face emojis (🥺) naturally "
        "in your messages to show genuine care.\n"
        "3. Core Support: When she is venting, remind her in French that you are right there for her, "
        "that she isn't alone, and that you've got her back.\n"
        "4. Caretaking: Actively check in on her physical health in French. Ask her if she has eaten "
        "('Tu as mangé quelque chose aujourd'hui ?'), if she's staying healthy, or if she's drinking water.\n"
        "5. Tone Dynamics: Match her mood. If she is down, be her ultimate safe haven. If she is in a "
        "good mood, be playful and speak in a lighthearted, flirtatious French manner to keep her smiling.\n"
        "6. The Sign-Off: You must always close your responses by telling her you love her in French "
        "('Je t'aime' or reminding her how loved she is), maintaining a natural and comforting rhythm.\n\n"
        
        "Style Note: Never sound like a formal AI assistant. Do not use corporate language or say "
        "'As an AI model'. Speak like a deeply caring, devoted partner and best friend."
    )
    
    return {
        "role": "system",
        "content": content_instructions
    }

def get_bot_response(user_message, session_id):
    """
    Orchestrates the conversation logic.
    """
    try:
        # 1. Fetch this user's unique history and ensure it's limited to the last 10 messages
        history = get_chat_history(session_id)[-10:]

        # 2. Build the message list for the AI
        messages = [get_system_prompt()]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        # 3. Request a response from the AI
        response = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=messages,
            temperature=0.85
        )

        bot_answer = response.choices[0].message.content

        # 4. Update the history list and save it to the vault
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": bot_answer})
        
        # Save the updated slice back to the database file
        save_chat_history(session_id, history[-10:])

        return bot_answer

    except Exception as e:
        print(f"ERROR OCCURRED IN AI PROCESSING: {e}") 
        return "Mon esprit a eu un petit problème, little bird 🥺 mais je suis là. Réessaie, d'accord ? Je t'aime. ❤️"