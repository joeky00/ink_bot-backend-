from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import json
from typing import Optional

# ====== Initialize FastAPI ======
app = FastAPI(
    title="Ink Bot Football Assistant", 
    version="1.0.0",
    description="A smart football assistant providing transfer news and Premier League updates"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====== API Keys ======
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "b311a02382fa4a88b9d1b4bfc74bb051")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "5e8310b5845626994bcbf672a6ff5b60")

# ====== Football Database ======
FOOTBALL_DATA = {
    "premier_league_teams": {
        "arsenal": {
            "full_name": "Arsenal FC",
            "stadium": "Emirates Stadium",
            "manager": "Mikel Arteta",
            "info": "Arsenal is one of the most successful clubs in English football, known for their attractive playing style."
        },
        "chelsea": {
            "full_name": "Chelsea FC",
            "stadium": "Stamford Bridge",
            "info": "Chelsea is a London-based club with significant success in both domestic and European competitions."
        },
        "liverpool": {
            "full_name": "Liverpool FC",
            "stadium": "Anfield",
            "info": "Liverpool has a rich history in European competitions and is known for their passionate fanbase."
        },
        "manchester united": {
            "full_name": "Manchester United",
            "stadium": "Old Trafford",
            "info": "Manchester United is one of the most successful and globally supported football clubs."
        },
        "manchester city": {
            "full_name": "Manchester City",
            "stadium": "Etihad Stadium",
            "info": "Manchester City has become a dominant force in recent years under Pep Guardiola."
        },
        "tottenham": {
            "full_name": "Tottenham Hotspur",
            "stadium": "Tottenham Hotspur Stadium",
            "info": "Spurs are known for their attacking football and have a modern, state-of-the-art stadium."
        }
    },
    "football_positions": {
        "goalkeeper": "The only player allowed to use hands within the penalty area, responsible for preventing goals.",
        "defender": "Players who primarily focus on stopping the opposition from scoring.",
        "midfielder": "Players who control the game's tempo and link defense with attack.",
        "forward": "Players primarily responsible for scoring goals and creating attacking opportunities.",
        "striker": "The main goal-scoring forward, usually positioned closest to the opponent's goal."
    },
    "transfer_windows": {
        "summer": "June 10 - August 31: The main transfer window when most big transfers happen.",
        "winter": "January 1 - January 31: A shorter window for mid-season adjustments."
    }
}

# ====== Helper Functions ======
def get_transfer_news() -> str:
    """Fetch latest football transfer news"""
    try:
        url = f"https://newsapi.org/v2/everything"
        params = {
            "q": "football transfers premier league",
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 5,
            "apiKey": NEWS_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("articles") and len(data["articles"]) > 0:
            articles = data["articles"][:3]
            news_items = []
            
            for i, article in enumerate(articles, 1):
                title = article.get("title", "No title")
                source = article.get("source", {}).get("name", "Unknown source")
                news_items.append(f"{i}. {title}\n   📰 {source}")
            
            return "🔥 **Latest Transfer News:**\n\n" + "\n\n".join(news_items)
        
        return "⚠️ No recent transfer news available at the moment."
        
    except requests.exceptions.RequestException:
        return "⚠️ Unable to fetch transfer news right now. Please try again later."
    except Exception as e:
        return "⚠️ Error retrieving transfer news. Please try again."

def get_premier_league_fixtures() -> str:
    """Fetch upcoming Premier League matches"""
    try:
        headers = {
            "x-rapidapi-host": "v3.football.api-sports.io",
            "x-apisports-key": FOOTBALL_API_KEY,
        }
        
        # Premier League ID is 39
        url = "https://v3.football.api-sports.io/fixtures"
        params = {
            "league": "39",
            "season": "2024",
            "next": "5"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("response") and len(data["response"]) > 0:
            fixtures = data["response"][:3]
            match_items = []
            
            for i, fixture in enumerate(fixtures, 1):
                home_team = fixture["teams"]["home"]["name"]
                away_team = fixture["teams"]["away"]["name"]
                match_date = fixture["fixture"]["date"][:10]  # Get date only
                match_time = fixture["fixture"]["date"][11:16]  # Get time
                
                match_items.append(f"{i}. {home_team} vs {away_team}\n   📅 {match_date} at {match_time}")
            
            return "⚽ **Upcoming Premier League Matches:**\n\n" + "\n\n".join(match_items)
        
        return "⚠️ No upcoming Premier League fixtures found."
        
    except requests.exceptions.RequestException:
        return "⚠️ Unable to fetch fixture data right now. Please try again later."
    except Exception as e:
        return "⚠️ Error retrieving fixture information. Please try again."

def search_football_info(query: str) -> Optional[str]:
    """Search for football information in our database"""
    query_lower = query.lower()
    
    # Search teams
    for team_key, team_info in FOOTBALL_DATA["premier_league_teams"].items():
        if team_key in query_lower or team_info["full_name"].lower() in query_lower:
            stadium = team_info.get("stadium", "")
            manager = team_info.get("manager", "")
            info = team_info.get("info", "")
            
            response = f"🏟️ **{team_info['full_name']}**\n\n{info}"
            if stadium:
                response += f"\n\n🏟️ Stadium: {stadium}"
            if manager:
                response += f"\n👨‍💼 Manager: {manager}"
            
            return response
    
    # Search positions
    for position, description in FOOTBALL_DATA["football_positions"].items():
        if position in query_lower:
            return f"⚽ **{position.title()}**: {description}"
    
    # Search transfer windows
    if "transfer window" in query_lower or "when" in query_lower and "transfer" in query_lower:
        return ("🗓️ **Transfer Windows:**\n\n"
                "**Summer Window:** June 10 - August 31\n"
                "**Winter Window:** January 1 - January 31")
    
    return None

def generate_smart_response(user_input: str) -> str:
    """Generate intelligent responses based on user input"""
    query_lower = user_input.lower()
    
    # Greeting responses
    if any(greeting in query_lower for greeting in ["hello", "hi", "hey", "good morning", "good afternoon"]):
        return "👋 Hello! I'm Ink Bot, your football assistant. Ask me about transfers, matches, teams, or players!"
    
    # Rules and regulations
    if any(word in query_lower for word in ["offside", "rule", "law", "foul", "penalty"]):
        return ("📋 **Football Rules:**\n\n"
                "Football has 17 laws including offside, fouls, penalties, and throw-ins. "
                "The offside rule prevents players from gaining unfair advantage by positioning "
                "themselves closer to the goal than the last defender when the ball is played by a teammate.")
    
    # Tactics and formations
    if any(word in query_lower for word in ["formation", "tactic", "4-4-2", "4-3-3", "strategy"]):
        return ("🎯 **Popular Formations:**\n\n"
                "• **4-4-2**: Balanced formation with 4 defenders, 4 midfielders, 2 forwards\n"
                "• **4-3-3**: Attacking formation with 4 defenders, 3 midfielders, 3 forwards\n"
                "• **3-5-2**: Formation with 3 center-backs, 5 midfielders, 2 strikers")
    
    # Premier League history
    if any(word in query_lower for word in ["history", "founded", "when", "first"]) and "premier league" in query_lower:
        return ("🏆 **Premier League History:**\n\n"
                "The Premier League was founded in 1992, replacing the First Division. "
                "Manchester United has won the most titles (13), followed by Manchester City. "
                "The league consists of 20 teams playing 38 matches each season.")
    
    return None

def process_user_query(user_input: str) -> str:
    """Main function to process user queries"""
    query_lower = user_input.lower()
    
    # Transfer news queries
    if any(keyword in query_lower for keyword in ["transfer", "signing", "signed", "bought", "sold", "news", "rumor"]):
        return get_transfer_news()
    
    # Match/fixture queries
    if any(keyword in query_lower for keyword in ["match", "fixture", "game", "playing", "next", "upcoming", "schedule"]):
        return get_premier_league_fixtures()
    
    # Search football database
    football_info = search_football_info(user_input)
    if football_info:
        return football_info
    
    # Generate smart response
    smart_response = generate_smart_response(user_input)
    if smart_response:
        return smart_response
    
    # Default response
    return ("⚽ **I'm your football assistant!** Ask me about:\n\n"
            "• 📰 Latest transfer news and rumors\n"
            "• ⚽ Upcoming Premier League matches\n"
            "• 🏟️ Premier League teams and stadiums\n"
            "• 📋 Football rules and tactics\n"
            "• 🏆 Premier League history and records")

# ====== Models ======
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

# ====== Routes ======
@app.get("/")
async def root():
    return {
        "message": "⚽ Ink Bot Football Assistant API",
        "version": "1.0.0",
        "status": "active",
        "endpoints": {
            "chat": "/chat (POST)",
            "health": "/health",
            "test_transfers": "/test/transfers",
            "test_matches": "/test/matches"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ink-bot",
        "version": "1.0.0"
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint"""
    try:
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        user_message = request.message.strip()
        if len(user_message) > 500:
            raise HTTPException(status_code=400, detail="Message too long")
        
        bot_response = process_user_query(user_message)
        return ChatResponse(response=bot_response)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

# ====== Test Endpoints ======
@app.get("/test/transfers")
async def test_transfers():
    """Test transfer news functionality"""
    response = get_transfer_news()
    return {"response": response}

@app.get("/test/matches")
async def test_matches():
    """Test match fixtures functionality"""
    response = get_premier_league_fixtures()
    return {"response": response}

@app.get("/test/search/{query}")
async def test_search(query: str):
    """Test search functionality"""
    response = process_user_query(query)
    return {"response": response}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
