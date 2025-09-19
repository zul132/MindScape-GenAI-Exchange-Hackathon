from flask import Flask, request, jsonify
import os
import json # RAG UPDATE: Import the json library
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


# RAG UPDATE: Load the mental health resources from the JSON file
def load_mental_health_resources():
    """Loads mental health resources from the JSON knowledge base."""
    try:
        with open(os.path.join("data", "resources.json"), 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("WARNING: resources.json not found. The RAG pipeline will not have access to resources.")
        return {}

# RAG UPDATE: Store resources in a global variable for efficiency
mental_health_resources = load_mental_health_resources()


# RAG UPDATE: Simple retrieval logic based on sentiment score
def retrieve_relevant_resources(sentiment_score):
    """
    Retrieves relevant mental health resources from the knowledge base
    based on the user's sentiment score.
    """
    if not mental_health_resources:
        return None

    # If sentiment is very negative, suggest crisis hotlines
    if sentiment_score < -0.6:
        return mental_health_resources.get("crisis_hotlines")
    # If sentiment is moderately negative, suggest online counseling
    elif -0.6 <= sentiment_score < -0.25:
        return mental_health_resources.get("online_counseling")
    # For milder negative feelings, suggest youth communities
    elif -0.25 <= sentiment_score < 0:
        return mental_health_resources.get("youth_communities")
    else:
        return None # No resources needed for positive sentiment


def generate_gemini_response(text, resources=None): # RAG UPDATE: Add 'resources' parameter
    """
    Generates a response using the Gemini API with the google-generativeai SDK.
    Optionally includes retrieved resources for a more helpful response.
    """
    gemini_model = genai.GenerativeModel("gemini-1.5-flash-latest")
    
    # RAG UPDATE: Dynamically change the prompt based on whether resources were retrieved
    if resources:
        # Convert resources list to a formatted string for the prompt
        resources_text = "\n".join([f"- {res['name']}: {res['description']} (Contact/Website: {res.get('contact', res.get('website'))})" for res in resources])
        
        prompt = f"""You are a compassionate and supportive mental wellness companion for the youth of India. A user has shared the following with you:

        "{text}"

        Their message indicates significant distress. Based on their message, please provide a comforting, empathetic, and culturally sensitive response. 
        It is very important that you gently and naturally weave the following resources into your advice. Do not just list them. Explain why one of them might be helpful.

        Here are some resources you MUST suggest:
        {resources_text}
        
        Keep your response concise, supportive, and actionable. Start by acknowledging their feelings.
        """
    else:
        prompt = f"""You are a compassionate and supportive mental wellness companion for the youth of India. A user has shared the following with you:

        "{text}"

        Based on their message, please provide a comforting and supportive response. If their message indicates mild distress, you can gently suggest talking to a friend, family member, or a professional. Keep your response concise, empathetic and culturally sensitive to an Indian context."""
    
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
    with open(temp_path, "rb") as audio_file_content:
        content = audio_file_content.read()

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

    # RAG UPDATE: Retrieve resources based on sentiment
    relevant_resources = retrieve_relevant_resources(sentiment.score)

    # RAG UPDATE: Pass the retrieved resources to Gemini
    gemini_response = generate_gemini_response(transcript, resources=relevant_resources)

    return jsonify({
        "transcript": transcript,
        "sentiment_score": sentiment.score,
        "sentiment_magnitude": sentiment.magnitude,
        "gemini_response": gemini_response
    })

if __name__ == "__main__":
    app.run(debug=True, port=5001)