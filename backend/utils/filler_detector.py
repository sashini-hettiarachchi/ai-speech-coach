import requests
import json

FILLERS = ["um", "uh", "like", "you know", "basically", "actually", "literally", "so"]

def count_filler_words(transcript: str) -> dict:
    """
    Uses a local LLaMA 2 model (via Ollama API) to count filler words in a transcript.
    Returns a dictionary with filler counts and total.
    """

    filler_word_prompt = f"""
    You are an assistant that analyzes spoken transcripts to detect filler words.
    Filler words include: {", ".join(f'"{f}"' for f in FILLERS)}.

    Instructions:
    1. Read the transcript carefully.
    2. Identify and count all filler words.
    3. Return the result strictly as JSON:
       {{
         "fillers": {{"um": 1, "uh": 1}},
         "total": 2
       }}

    Transcript:
    {transcript}
    """

    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama2", "prompt": filler_word_prompt, "stream": False},
            timeout=60,
        )
        resp.raise_for_status()

        data = resp.json()
        result_text = data.get("response", "").strip()

        # Try parsing directly
        try:
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError:
            # Try extracting JSON substring from text
            start = result_text.find("{")
            end = result_text.rfind("}") + 1
            if start != -1 and end != -1:
                json_part = result_text[start:end]
                try:
                    result = json.loads(json_part)
                    return result
                except json.JSONDecodeError:
                    pass

        # If LLaMA output wasn’t JSON → fallback
        print("Warning: Model did not return valid JSON, using naive fallback.")
        raise ValueError("Invalid JSON from model")

    except (requests.RequestException, ValueError) as e:
        print("Error analyzing fillers:", e)

        # Fallback: naive count
        words = transcript.lower().split()
        filler_counts = {f: words.count(f) for f in FILLERS if f in words}
        return {"fillers": filler_counts, "total": sum(filler_counts.values())}
