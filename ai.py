import httpx
from groq import AsyncGroq
from config import GROQ_API_KEY, GEMINI_API_KEY
import structlog


logger = structlog.get_logger()

def build_prompt(job_type:str, payload: dict):
    if job_type == "summarise":
        return f"Summarise the following text DO NOT ADD ANY EXTRA NOTES: {payload.get('text')}"
    elif job_type == "translate":
        return f"Translate the following text to {payload.get('language')} ONLY TRANSLATE IT DO NOT ADD ANY EXTRA NOTES: {payload.get('text')}"
    elif job_type == "validate":
        return f"Validate the following text DO NOT ADD ANY EXTRA NOTES: {payload.get('text')}"
    else:
        return f"Process the following: {payload}"

client = AsyncGroq(api_key=GROQ_API_KEY)

async def call_groq_prompt(prompt: str):
    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile", 
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

async def call_gemini_prompt(prompt: str):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key={GEMINI_API_KEY}"
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json={
            "contents": [{"parts": [{"text": prompt}]}]
        })
        response.raise_for_status()
        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise ValueError("Gemini returned no candidates (possible content filter)")
        return candidates[0]["content"]["parts"][0]["text"]

async def execute_ai_prompt(prompt: str):
    try:
        return await call_groq_prompt(prompt)
    except Exception as e:
        logger.warning("Groq failed, falling back to Gemini", error=str(e))
        return await call_gemini_prompt(prompt)

async def call_groq(job_type: str, payload: dict):
    prompt = build_prompt(job_type, payload)
    return await call_groq_prompt(prompt)

async def call_gemini(job_type: str, payload: dict):
    prompt = build_prompt(job_type, payload)
    return await call_gemini_prompt(prompt)

async def run_ai(job_type: str, payload: dict):
    prompt = build_prompt(job_type, payload)
    return await execute_ai_prompt(prompt)
