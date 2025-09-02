import whisper

def transcrib_audio_with_whisper(audio_file_path):
    """
    Transcribes an audio file using Whisper, keeping filler words.
    """
    model = whisper.load_model("tiny")

    prompt = (
        "I was like, was like, I'm like, you know what I mean, kind of,  um, ah, huh, and so, so um, uh, and um, like um, so like, like it's, it's like, i mean, yeah, ok so, uh so, so uh, yeah so, you know, it's uh, uh and, and uh, like, kind, hmm, mmm"
    )

    response = model.transcribe(
        audio_file_path,
        initial_prompt=prompt,
    )

    return response["text"]
