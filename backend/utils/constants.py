SERVICE_ACCOUNT_KEY_PATH = "key.json" # Replace with the actual path
REGION = "us-central1"  # Or another region where Vertex AI Gemini is available
AUDIO_FILE_PATH ='test_data/test2.wav'  # Replace with your audio file path
CONTEXT_DATA = {
  "CSSEF_COMPETENCIES": {
    "C1_topic_choice": "CHOOSES AND NARROWS A TOPIC APPROPRIATELY FOR THE AUDIENCE & OCCASION",
    "C2_purpose": "COMMUNICATES THE THESIS/SPECIFIC PURPOSE IN A MANNER APPROPRIATE FOR THE AUDIENCE & OCCASION",
    "C3_supporting_material": "PROVIDES SUPPORTING MATERIAL (INCLUDING ELECTRONIC AND NON-ELECTRONIC PRESENTATIONAL AIDS) APPROPRIATE FOR THE AUDIENCE & OCCASION",
    "C4_organization": "USES AN ORGANIZATIONAL PATTERN APPROPRIATE TO THE TOPIC, AUDIENCE, OCCASION, & PURPOSE",
    "C5_language_use": "USES LANGUAGE APPROPRIATE TO THE AUDIENCE & OCCASION",
    "C6_vocal_variety": "USES VOCAL VARIETY IN RATE, PITCH, & INTENSITY (VOLUME) TO HEIGHTEN & MAINTAIN INTEREST APPROPRIATE TO THE AUDIENCE & OCCASION",
    "C7_pronunciation_and_grammar": "USES PRONUNCIATION, GRAMMAR, & ARTICULATION APPROPRIATE TO THE AUDIENCE & OCCASION",
    "C8_physical_behaviors": "USES PHYSICAL BEHAVIORS THAT SUPPORT THE VERBAL MESSAGE"
  },
  "CONTEXT_SCORES": {
    "academic": {
      "C1_topic_choice": 0.15,
      "C2_purpose": 0.15,
      "C3_supporting_material": 0.15,
      "C4_organization": 0.15,
      "C5_language_use": 0.10,
      "C6_vocal_variety": 0.10,
      "C7_pronunciation_and_grammar": 0.10,
      "C8_physical_behaviors": 0.10
    },
    "persuasive": {
      "C1_topic_choice": 0.10,
      "C2_purpose": 0.20,
      "C3_supporting_material": 0.20,
      "C4_organization": 0.15,
      "C5_language_use": 0.10,
      "C6_vocal_variety": 0.10,
      "C7_pronunciation_and_grammar": 0.10,
      "C8_physical_behaviors": 0.05
    },
    "storytelling": {
      "C1_topic_choice": 0.10,
      "C2_purpose": 0.10,
      "C3_supporting_material": 0.20,
      "C4_organization": 0.20,
      "C5_language_use": 0.15,
      "C6_vocal_variety": 0.10,
      "C7_pronunciation_and_grammar": 0.10,
      "C8_physical_behaviors": 0.05 
    }
  }
}