from vertexai.preview.generative_models import GenerativeModel


def give_recommendations_with_gemini(transcript):
    model = GenerativeModel("gemini-2.5-pro")

    print("\n--- Performing Spoken Grammar Analysis ---")
    spoken_grammar_prompt = f"""
    Act as a public speaking coach. Review this transcript for spoken grammatical errors, awkward phrasing, and run-on sentences.
    Do not correct it like a formal essay; instead, provide friendly suggestions on how to make the sentences clearer and more impactful for a live audience.
    Do not repeat the transcript here, just provide your analysis.

    Transcript:
    {transcript}
    """
    grammar_res = model.generate_content([spoken_grammar_prompt])
    print("Spoken Grammar Analysis:")
    print("grammaer response",grammar_res.candidates[0].content.parts[0].text)
    return grammar_res.candidates[0].content.parts[0].text