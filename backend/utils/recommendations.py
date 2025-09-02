import requests
import json

def give_recommendations(transcript):
    url = "http://localhost:11434/api/generate"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "llama2",
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