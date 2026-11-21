import os
import re
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# 1. Initialize official GoogleGenAI client via environment variable (Station 01 & 02)
if not os.environ.get("GEMINI_API_KEY"):
    raise RuntimeError("GEMINI_API_KEY environment variable is missing.")

client = genai.Client()  # Automatically reads GEMINI_API_KEY
app = FastAPI(title="DevFest Vibe Lounge Agent")

# 2. Typed Tool Definition with Strict Input Guardrails (Station 02)
def get_station_status(station_id: int) -> dict:
    """Returns live status for a DevFest Vibe Lounge station (1 to 10)."""
    # Guardrail: Validate argument bounds
    if not isinstance(station_id, int) or not (1 <= station_id <= 10):
        return {"error": "Invalid stationId. Must be an integer between 1 and 10."}
    
    mock_stations = {
        1: {"station": "Build Lounge", "status": "OPEN", "wait_mins": 2},
        2: {"station": "Security Lab", "status": "BUSY", "wait_mins": 12},
        3: {"station": "Cloud Scale Pod", "status": "OPEN", "wait_mins": 0},
    }
    return mock_stations.get(station_id, {"station": f"Station {station_id}", "status": "OPEN", "wait_mins": 5})

# 3. Domain-Specific System Instructions + Safety Guardrails (Station 01 & 02)
SYSTEM_INSTRUCTION = """
You are the official DevFest Johannesburg & Sandton Vibe Lounge Assistant.
- Be concise, practical, and helpful.
- Use the `get_station_status` tool whenever a user asks about a station's availability or wait time.
- If a user asks about an invalid station number, explain politely that valid stations are 1 through 10.
- PRIVACY GUARDRAIL (POPIA): Never ask for, repeat, or store personal identifiable information (ID numbers, phone numbers, emails).
"""

# In-memory multi-turn chat sessions (no persistent PII logging for POPIA compliance)
sessions: dict[str, object] = {}

class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=64)
    message: str = Field(..., min_length=1, max_length=1000)

def contains_pii(text: str) -> bool:
    """POPIA Guardrail: Detects 13-digit SA ID numbers or standard phone numbers."""
    sa_id_pattern = r"\b\d{13}\b"
    phone_pattern = r"\b(?:\+27|0)[6-8][0-9]{8}\b"
    return bool(re.search(sa_id_pattern, text) or re.search(phone_pattern, text))

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    # Input Guardrail: POPIA check
    if contains_pii(req.message):
        return {
            "reply": "For your privacy under POPIA, please do not share ID numbers or phone numbers here. How else can I help with DevFest?"
        }

    # Initialize multi-turn chat session if new (Station 01)
    if req.session_id not in sessions:
        sessions[req.session_id] = client.chats.create(
            model="gemini-3.5-flash-lite",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=[get_station_status],
                temperature=0.4,
            ),
        )

    chat = sessions[req.session_id]
    try:
        response = chat.send_message(req.message)
        return {"reply": response.text}
    except Exception as e:
        print("GEMINI API ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Unable to process request safely.")