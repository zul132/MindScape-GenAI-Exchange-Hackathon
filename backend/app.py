from flask import Flask, request, jsonify
import os
from google.cloud import speech
from google.cloud import language_v1
from google.oauth2 import service_account
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# --- Service account credentials for Speech-to-Text and Language API ---
# This is still needed for the other Google Cloud services.
CREDENTIALS_PATH = "D:\\Hackathons\\Google_GenAI_Exchange_Hackathon\\MindScape-Project\\credentials\\genai-exchange-hack-4c8e1b0ee7a3.json"
credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)

# --- Initialize Gemini with API Key ---
# The API key is loaded from the .env file.
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file. Please create a .env file in the 'backend' directory and add your key.")
genai.configure(api_key=api_key)


def generate_gemini_response(text):
    """
    Generates a response using the Gemini API with the google-generativeai SDK.
    """
    gemini_model = genai.GenerativeModel("gemini-1.5-flash-latest")
    prompt = f"""You are a compassionate and supportive mental wellness companion. A user has shared the following with you:

    "{text}"

    Based on their message, please provide a comforting and supportive response. If their message indicates significant distress, gently suggest seeking professional help and provide resources if possible. Keep your response concise and empathetic."""
    
    response = gemini_model.generate_content(prompt)
    return response.text

@app.route("/analyze", methods=["POST"])
def analyze():
    if "audio_data" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files["audio_data"]
    filename = audio_file.filename
    
    if not os.path.exists("temp"):
        os.makedirs("temp")

    temp_path = os.path.join("temp", filename)
    audio_file.save(temp_path)

    # Speech-to-Text
    client = speech.SpeechClient(credentials=credentials)
    with open(temp_path, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)

    encoding = speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED
    if filename.endswith(".wav"):
        encoding = speech.RecognitionConfig.AudioEncoding.LINEAR16
    elif filename.endswith(".mp3"):
        encoding = speech.RecognitionConfig.AudioEncoding.MP3
    elif filename.endswith(".webm"):
        encoding = speech.RecognitionConfig.AudioEncoding.WEBM_OPUS

    config = speech.RecognitionConfig(
        encoding=encoding,
        sample_rate_hertz=48000,
        language_code="en-US",
        audio_channel_count=2,
        enable_separate_recognition_per_channel=False,
    )

    try:
        response = client.recognize(config=config, audio=audio)
        transcript = " ".join([result.alternatives[0].transcript for result in response.results])
    except Exception as e:
        return jsonify({"error": f"Speech-to-Text failed: {e}"}), 500
    finally:
        os.remove(temp_path)

    if not transcript:
        return jsonify({"error": "Could not transcribe audio"}), 500

    # Natural Language API for sentiment analysis
    language_client = language_v1.LanguageServiceClient(credentials=credentials)
    document = language_v1.Document(content=transcript, type_=language_v1.Document.Type.PLAIN_TEXT)
    sentiment = language_client.analyze_sentiment(document=document).document_sentiment

    # Generate response with Gemini
    gemini_response = generate_gemini_response(transcript)

    return jsonify({
        "transcript": transcript,
        "sentiment_score": sentiment.score,
        "sentiment_magnitude": sentiment.magnitude,
        "gemini_response": gemini_response
    })

if __name__ == "__main__":
    app.run(debug=True, port=5001)
