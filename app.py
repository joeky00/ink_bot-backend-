from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import re
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

# ====== API KEYS ======
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "b311a02382fa4a88b9d1b4bfc74bb051")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "5e8310b5845626994bcbf672a6ff5b60")

# ====== Football Knowledge Base ======
football_knowledge = {
    "teams": {
        "manchester united": "Manchester United is one of the most successful clubs in English football, based in Manchester.",
        "manchester city": "Manchester City is a Premier League club known for their recent success under Pep Guardiola.",
        "liverpool": "Liverpool FC is a historic club with a rich European heritage, known for their passionate fanbase.",
        "arsenal": "Arsenal FC, based in North London, are known for their attractive style of play.",
        "chelsea": "Chelsea FC is a London-based club with significant success in domestic and European competitions.",
        "tottenham": "Tottenham Hotspur, also known as Spurs, are a North London club with a modern stadium.",
    },
    "players": {
        "haaland": "Erling Haaland is a Norwegian striker known for his incredible goal-scoring record.",
        "mbappe": "Kylian Mbappe is a French forward known for his pace and finishing ability.",
        "messi": "Lionel Messi is widely considered one of the greatest footballers of all time.",
        "ronaldo": "Cristiano Ronaldo is a Portuguese forward and one of football's all-time greats.",
        "salah": "Mohamed Salah is an Egyptian winger/forward known for his pace and goal-scoring.",
    },
    "positions": {
        "goalkeeper": "The goalkeeper is the only player allowed to use hands within the penalty area.",
        "defender": "Defenders are responsible for stopping the opposing team from scoring.",
        "midfielder": "Midfielders control the tempo of the game and link defense with attack.",
        "forward": "Forwards are primarily responsible for scoring goals.",
        "striker": "A striker is the main goal-scoring forward in the team.",
    },
    "general": {
        "premier league": "The Premier League is the top division of English football with 20 teams.",
        "transfer window": "Transfer windows are periods when clubs can buy and sell players - summer (June-August) and winter (January).",
        "champions league": "The UEFA Champions League is Europe's premier club competition.",
        "world cup": "The FIFA World Cup is held every four years and is football's most prestigious tournament.",
    }
}

# ====== Helper Functions ======
def get_transfer_news():
    """Get latest football transfer news"""
    try:
        url = f"https://newsapi.org/v2/everything?q=football+transfers+premier+league&language=en&sortBy=publishedAt&pageSize=5&apiKey={NEWS_API_KEY}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("articles") and len(data["articles"]) > 0:
            articles = data["articles"][:3]  # Get top 3 articles
            news_summary = "📰 Latest Transfer News:\n"
            for i, article in enumerate(articles, 1):
                news_summary += f"{i}. {article['title']} (Source: {article['source']['name']})\n"
            return news_summary.strip()
        return "⚠️ No transfer news available at the moment."
    except Exception as e:
        return f"⚠️ Error fetching transfer news: Unable to connect to news service."

def get_next_match():
    """Get next Premier League match"""
    try:
        headers = {
            "x-rapidapi-host": "v3.football.api-sports.io",
            "x-apisports-key": FOOTBALL_API_KEY,
        }
        # Get next Premier League fixtures
        url = "https://v3.football.api-sports.io/fixtures?league=39&season=2024&next=5"
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("response") and len(data["response"]) > 0:
            fixtures = data["response"][:3]  # Get next 3 matches
            match_summary = "⚽ Upcoming Premier League Matches:\n"
            for i, fixture in enumerate(fixtures, 1):
                teams = fixture["teams"]
                fixture_date = fixture["fixture"]["date"][:10]  # Get date only
                match_summary += f"{i}. {teams['home']['name']} vs {teams['away']['name']} on {fixture_date}\n"
            return match_summary.strip()
        return "⚠️ No upcoming Premier League matches found."
    except Exception as e:
        return f"⚠️ Error fetching match data: Unable to connect to football API."

def search_knowledge_base(query: str) -> str:
    """Search the football knowledge base"""
    query_lower = query.lower()
    
    # Search in all categories
    for category, items in football_knowledge.items():
        for key, info in items.items():
            if key in query_lower or any(word in key for word in query_lower.split()):
                return f"🤖 {info}"
    
    # If no exact match, look for partial matches
    for category, items in football_knowledge.items():
        for key, info in items.items():
            query_words = query_lower.split()
            if any(word in key for word in query_words):
                return f"🤖 {info}"
    
    return None

def generate_response_by_keywords(query: str) -> str:
    """Generate responses based on keywords"""
    query_lower = query.lower()
    
    # Question about rules
    if any(word in query_lower for word in ["offside", "rule", "law", "regulation"]):
        return "🤖 Football has 17 laws that govern the game, including offside, fouls, and penalties. The offside rule prevents players from gaining unfair advantage by positioning themselves closer to the goal than the last defender."
    
    # Question about tactics
    if any(word in query_lower for word in ["formation", "tactic", "strategy", "4-4-2", "4-3-3"]):
        return "🤖 Common football formations include 4-4-2, 4-3-3, and 3-5-2. Each formation has different tactical advantages for attack and defense."
    
    # Question about history
    if any(word in query_lower for word in ["history", "founded", "established", "first"]):
        return "🤖 The Premier League was founded in 1992, replacing the First Division. Manchester United has won the most Premier League titles (13), followed by Manchester City."
    
    # Question about stats
    if any(word in query_lower for word in ["goal", "score", "record", "most", "best"]):
        return "🤖 The Premier League record for most goals in a season is 32, shared by Mohamed Salah (2017-18) and Alan Shearer (1993-94, 1994-95)."
    
    return None

def sports_ai_response(user_input: str) -> str:
    """Main response logic"""
    user_input_lower = user_input.lower()

    # Check for transfer-related queries
    if any(keyword in user_input_lower for keyword in ["transfer", "signed", "signing", "bought", "sold", "rumor", "news"]):
        return get_transfer_news()

    # Check for match-related queries
    if any(keyword in user_input_lower for keyword in ["next match", "upcoming", "fixture", "game", "when", "playing", "schedule"]):
        return get_next_match()

    # Search knowledge base
    kb_response = search_knowledge_base(user_input)
    if kb_response:
        return kb_response

    # Generate keyword-based response
    keyword_response = generate_response_by_keywords(user_input)
    if keyword_response:
        return keyword_response

    # Fallback response
    return "⚽ I'm your football assistant! Ask me about:\n• Transfer news and rumors\n• Upcoming Premier League matches\n• Football teams and players\n• Rules and tactics\n• Premier League history"

# ====== Request/Response Models ======
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

# ====== API Routes ======
@app.get("/")
async def root():
    return {"message": "Ink Bot Football Assistant API is running! 🤖⚽", "version": "1.0.0 (Lightweight)"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ink-bot", "version": "lightweight"}

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

@app.get("/test/knowledge")
async def test_knowledge():
    """Test knowledge base"""
    return {"response": search_knowledge_base("manchester united")}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
