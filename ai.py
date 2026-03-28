import httpx
from groq import AsyncGroq
from config import GROQ_API_KEY, GEMINI_API_KEY
import structlog

logger = structlog.get_logger()

def build_prompt(job_type:str, payload: dict):
    if job_type == "summarise":
        return f"Summarise the following text: {payload.get('text')}"
    elif job_type == "translate":
        return f"Translate the following text to {payload.get('language')}: {payload.get('text')}"
    elif job_type == "validate":
        return f"Validate the following text: {payload.get('text')}"
    else:
        return f"Process the following: {payload}"

client = AsyncGroq(api_key=GROQ_API_KEY)

async def call_groq(job_type: str, payload: dict):
    prompt = build_prompt(job_type, payload)
    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile", 
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

async def call_gemini(job_type: str, payload: dict):
    prompt = build_prompt(job_type, payload)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key={GEMINI_API_KEY}"

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json = {
          "contents": [{"parts": [{"text": prompt}]}]
        })
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    

async def run_ai(job_type: str, payload: dict):
    try:
        return await call_groq(job_type, payload)
    except Exception as e:
        logger.warning("Groq failed, falling back to Gemini", error=str(e))
        return await call_gemini(job_type, payload)

