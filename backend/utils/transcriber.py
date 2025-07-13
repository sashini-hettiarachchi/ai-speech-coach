
from google.cloud import speech_v1p1beta1 as speech
import vertexai
from google.oauth2 import service_account


SERVICE_ACCOUNT_KEY_PATH = "key.json" # Replace with the actual path
REGION = "us-central1"  # Or another region where Vertex AI Gemini is available
AUDIO_FILE_PATH ='test_data/test2.wav'  # Replace with your audio file path


credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_KEY_PATH)
PROJECT_ID = credentials.project_id
vertexai.init(project=PROJECT_ID, location=REGION, credentials=credentials)


def transcribe_audio_with_speech_to_text(audio_file_path):
    """
    Transcribes an audio file using Google Cloud Speech-to-Text API with word time offsets and automatic punctuation.
    Authenticates using provided credentials.
    """
    # Pass the credentials object to the SpeechClient
    client = speech.SpeechClient(credentials=credentials)

    with open(audio_file_path, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,  # Adjust based on your audio file's encoding
        sample_rate_hertz=48000,  # Adjust based on your audio file's sample rate
        language_code="en-US",  # Adjust to your audio's language
        enable_word_time_offsets=True,
        enable_automatic_punctuation=True,
        # model="default" or "enhanced" based on your needs
    )

    print(f"Transcribing audio: {audio_file_path}...")
    response = client.recognize(config=config, audio=audio)
    print("Transcription complete.")
    
    print('response', response)

    full_transcript = ""
    word_details = []

    for result in response.results:
        full_transcript += result.alternatives[0].transcript
        for word_info in result.alternatives[0].words:
            word_details.append(
                {
                    "word": word_info.word,
                    "start_time": word_info.start_time.total_seconds(),
                    "end_time": word_info.end_time.total_seconds(),
                }
            )
    return full_transcript
