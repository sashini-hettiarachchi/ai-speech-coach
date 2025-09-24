import requests
import json

# Import configuration with fallback
try:
    from config import LLM_ENDPOINT, LLM_MODEL
except ImportError:
    LLM_ENDPOINT = "http://localhost:11434/api/generate"
    LLM_MODEL = "llama2"

def give_recommendations(transcript):
    url = LLM_ENDPOINT
    headers = {"Content-Type": "application/json"}
    data = {
        "model": LLM_MODEL,
        "prompt": f"Act as a public speaking coach. Review this transcript for spoken grammatical errors, awkward phrasing, and run-on sentences.\n\nTranscript:\n{transcript}\n",
        "stream": False
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "")
    except requests.RequestException as e:
        print("Error giving recommendations:", e)
        return "Sorry, I couldn't generate recommendations at this time."