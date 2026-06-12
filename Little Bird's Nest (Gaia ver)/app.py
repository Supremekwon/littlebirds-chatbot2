import os
import uuid
from flask import Flask, render_template, request, jsonify, session
from va_logic import get_bot_response

app = Flask(__name__)
# Securely handle sessions (Needed for unique user memory)
app.secret_key = os.urandom(24)

@app.route('/')
def landing():
    """Landing page for the application."""
    return render_template('landing.html')

@app.route('/chat')
def chat():
    """Main chat interface."""
    # Assign a unique session ID if the user doesn't have one
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return render_template('index.html')

@app.route('/message', methods=['POST'])
def message():
    """Endpoint that receives user text and returns AI response."""
    user_input = request.json.get('message')
    user_id = session.get('session_id')

    # Pass the message to the logic file
    response = get_bot_response(user_input, user_id)

    return jsonify({'reply': response})

if __name__ == '__main__':
    app.run(debug=True)