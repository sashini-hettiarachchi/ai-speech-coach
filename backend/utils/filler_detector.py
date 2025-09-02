# from vertexai.preview.generative_models import GenerativeModel, Part
import requests



FILLERS = ["um", "uh", "like", "you know", "so", "basically", "actually"]

# def count_fillers_with_gemini(transcript):
#     """
#     Analyzes the transcript using Vertex AI's Gemini model for filler words and spoken grammar.
#     """

#     model = GenerativeModel("gemini-2.5-pro") 

#     print("\n--- Performing Filler Word Analysis (LLM-Powered Contextual) ---")
#     filler_word_prompt = f"""
#     Analyze the following speech transcript. Identify and list all filler words (like 'um', 'ah', 'like', 'you know', 'so', 'right', 'hmm').
#     Calculate the total filler word count and provide it in the top level of the response.

#     Transcript:
#     {transcript}
#     """
#     response = model.generate_content([filler_word_prompt])
#     print("LLM-Powered Filler Word Analysis:")
#     print("filler word response",response.candidates[0].content.parts[0].text)
#     return response.candidates[0].content.parts[0].text


def count_filler_words(transcript):
    """
    Counts filler words in the given transcript.
    """
    resp = requests.post("http://localhost:11434/api/generate", json={
    "model": "llama2",
    "prompt": "Analyze transcript and highlight sensitive words."
    })
    print(resp.json()["response"])
    words = transcript.lower().split()
    filler_counts = {filler: words.count(filler) for filler in FILLERS if words.count(filler) > 0}
    return filler_counts