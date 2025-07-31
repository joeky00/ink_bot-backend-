from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import requests
import re

# ====== Initialize FastAPI ======
app = FastAPI()

# Allow CORS for your frontend (you can restrict domains here)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====== Load Model ======
model_name = "google/flan-t5-small"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
qa_pipeline = pipeline("question-answering", model=model, tokenizer=tokenizer)

# ====== Load Context (from FIFA player dataset QA) ======
with open("qa_context.txt", "r") as file:
    context = file.read()

# ====== API KEYS ======
NEWS_API_KEY = "b311a02382fa4a88b9d1b4bfc74bb051"
FOOTBALL_API_KEY = "5e8310b5845626994bcbf672a6ff5b60"

# ====== Helper Functions ======
def get_transfer_news():
    url = f"https://newsapi.org/v2/everything?q=football transfers&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    response = requests.get(url)
    data = response.json()
    if data.get("articles"):
        article = data["articles"][0]
        return f"📰 Latest Transfer: \"{article['title']}\" (Source: {article['source']['name']})"
    return "⚠️ No transfer news available."

def get_next_match():
    headers = {
        "x-rapidapi-host": "v3.football.api-sports.io",
        "x-apisports-key": FOOTBALL_API_KEY,
    }
    url = "https://v3.football.api-sports.io/fixtures?league=39&season=2024&next=1"
    response = requests.get(url, headers=headers)
    data = response.json()
    if data.get("response"):
        match = data["response"][0]["teams"]
        return f"⚽ Next Match: {match['home']['name']} vs {match['away']['name']}"
    return "⚠️ No upcoming matches found."

def sports_ai_response(user_input: str) -> str:
    user_input = user_input.lower()

    # If it's a QA-type query
    if any(k in user_input for k in ["who", "what", "how", "when", "is", "was"]):
        try:
            result = qa_pipeline(question=user_input, context=context)
            return f"🤖 Answer: {result['answer']}"
        except:
            return "⚠️ Sorry, I couldn't find an answer. Please rephrase your question."

    # If it's about transfers
    if "transfer" in user_input or "signed" in user_input:
        return get_transfer_news()

    # If it's about matches
    if any(k in user_input for k in ["next match", "upcoming match", "who is playing", "next premier league game"]):
        return get_next_match()

    # Fallback
    return "⚽ I'm still learning. Try asking about a football player, transfer, or upcoming match!"

# ====== Request Model ======
class ChatRequest(BaseModel):
    message: str

# ====== API Route ======
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    user_message = request.message
    bot_reply = sports_ai_response(user_message)
    return {"response": bot_reply}
    
