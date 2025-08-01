from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ====== Initialize FastAPI ======
app = FastAPI(title="Ink Bot Football Assistant", version="1.0.0")

# Allow CORS for your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====== Load Model ======
model_name = "google/flan-t5-small"
try:
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    # Use text2text-generation pipeline for flan-t5
    text_generator = pipeline("text2text-generation", model=model, tokenizer=tokenizer, max_length=512)
except Exception as e:
    print(f"Error loading model: {e}")
    text_generator = None

# ====== API KEYS ======
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "b311a02382fa4a88b9d1b4bfc74bb051")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "5e8310b5845626994bcbf672a6ff5b60")

# ====== Football Context ======
football_context = """
The Premier League is the top football league in England with 20 teams.
Popular teams include Manchester United, Manchester City, Liverpool, Arsenal, Chelsea, and Tottenham.
Football transfers happen during transfer windows - summer (June-August) and winter (January).
Key positions include goalkeeper, defender, midfielder, and forward.
Famous players include Cristiano Ronaldo, Lionel Messi, Kylian Mbappe, and Erling Haaland.
"""

# ====== Helper Functions ======
def get_transfer_news():
    """Get latest football transfer news"""
    try:
        url = f"https://newsapi.org/v2/everything?q=football+transfers+premier+league&language=en&sortBy=publishedAt&pageSize=3&apiKey={NEWS_API_KEY}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("articles") and len(data["articles"]) > 0:
            article = data["articles"][0]
            return f"📰 Latest Transfer News: \"{article['title']}\" (Source: {article['source']['name']})"
        return "⚠️ No transfer news available at the moment."
    except Exception as e:
        return f"⚠️ Error fetching transfer news: {str(e)}"

def get_next_match():
    """Get next Premier League match"""
    try:
        headers = {
            "x-rapidapi-host": "v3.football.api-sports.io",
            "x-apisports-key": FOOTBALL_API_KEY,
        }
        # Get next Premier League fixtures
        url = "https://v3.football.api-sports.io/fixtures?league=39&season=2024&next=1"
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("response") and len(data["response"]) > 0:
            fixture = data["response"][0]
            teams = fixture["teams"]
            fixture_date = fixture["fixture"]["date"]
            return f"⚽ Next Premier League Match: {teams['home']['name']} vs {teams['away']['name']} on {fixture_date[:10]}"
        return "⚠️ No upcoming Premier League matches found."
    except Exception as e:
        return f"⚠️ Error fetching match data: {str(e)}"

def generate_ai_response(user_input: str) -> str:
    """Generate AI response using flan-t5"""
    if not text_generator:
        return "⚠️ AI model not available. Please try again later."
    
    try:
        # Create a prompt for the model
        prompt = f"Answer this football question based on the context: {football_context}\n\nQuestion: {user_input}\nAnswer:"
        
        # Generate response
        result = text_generator(prompt, max_length=150, num_return_sequences=1, temperature=0.7)
        answer = result[0]['generated_text'].strip()
        
        # Clean up the response
        if answer:
            return f"🤖 {answer}"
        else:
            return "⚽ I'm still learning about football. Try asking about transfers, matches, or players!"
    except Exception as e:
        print(f"AI generation error: {e}")
        return "⚽ I'm still learning about football. Try asking about transfers, matches, or players!"

def sports_ai_response(user_input: str) -> str:
    """Main response logic"""
    user_input_lower = user_input.lower()

    # Check for transfer-related queries
    if any(keyword in user_input_lower for keyword in ["transfer", "signed", "signing", "bought", "sold"]):
        return get_transfer_news()

    # Check for match-related queries
    if any(keyword in user_input_lower for keyword in ["next match", "upcoming", "fixture", "game", "when", "playing"]):
        return get_next_match()

    # For other questions, use AI generation
    return generate_ai_response(user_input)

# ====== Request/Response Models ======
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

# ====== API Routes ======
@app.get("/")
async def root():
    return {"message": "Ink Bot Football Assistant API is running! 🤖⚽"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ink-bot"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint"""
    try:
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        user_message = request.message.strip()
        bot_reply = sports_ai_response(user_message)
        
        return ChatResponse(response=bot_reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# ====== Test Endpoints ======
@app.get("/test/transfers")
async def test_transfers():
    """Test transfer news endpoint"""
    return {"response": get_transfer_news()}

@app.get("/test/matches")
async def test_matches():
    """Test match data endpoint"""
    return {"response": get_next_match()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
    
