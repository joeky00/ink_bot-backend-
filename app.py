import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=["*"])

# Configure Gemini API
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel('gemini-1.5-flash-preview-0409')

def query_gemini(prompt: str) -> str:
    try:
        print(f"Querying Gemini with: {prompt}")
        response = gemini_model.generate_content(prompt)
        print(f"Response Text: {response.text}")
        return response.text.strip()
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return f"An unexpected error occurred: {str(e)}"

@app.route('/api/chat', methods=['POST'])
def chat_api():
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        message = data['message']
        history = data.get('history', [])
        
        # Build context from history for better responses
        if history and len(history) > 0:
            # Take last 6 messages for context (3 exchanges)
            recent_history = history[-6:] if len(history) > 6 else history
            context_parts = []
            for msg in recent_history:
                role = "Human" if msg['role'] == 'user' else "Assistant"
                context_parts.append(f"{role}: {msg['content']}")
            
            context = "\n".join(context_parts)
            full_prompt = f"Previous conversation context:\n{context}\n\nHuman: {message}\n\nAssistant:"
        else:
            full_prompt = f"Human: {message}\n\nAssistant:"
        
        # Get response from Gemini
        response = query_gemini(full_prompt)
        
        return jsonify({
            'response': response,
            'status': 'success'
        })
        
    except Exception as e:
        print(f"API Error: {str(e)}")
        return jsonify({
            'error': f'An error occurred: {str(e)}',
            'status': 'error'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy', 
        'message': 'INK Bot API is running',
        'model': 'gemini-1.5-flash-preview-0409'
    })

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'INK Bot API is running!',
        'endpoints': {
            'health': '/api/health',
            'chat': '/api/chat (POST)'
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
