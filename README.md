# DevFest Vibe Lounge Agent

Domain-specific AI assistant built with the official **Google GenAI SDK (`google-genai`)**, **FastAPI**, and **Gemini** for DevFest Johannesburg & Sandton.

## Challenge Verification Coverage
- **Station 01 (Agent & Multi-Turn State):** Initializes `google.genai.Client()` from `GEMINI_API_KEY`, sets domain `system_instruction`, and tracks multi-turn state via `client.chats.create()`.
- **Station 02 (Typed Function Calling & POPIA Guardrails):** Exposes `get_station_status(station_id: int)` with strict integer range validation (`1–10`) and regex PII filtering so South African ID numbers and phone numbers are never processed or stored.
- **Station 03 (Live Cloud Run Deployment):** Serves a mobile-responsive UI via FastAPI deployed to Google Cloud Run (`africa-south1`).

## Run Locally
```bash
pip install -r requirements.txt
set GEMINI_API_KEY=your_api_key_here
uvicorn main:app --port 8080
