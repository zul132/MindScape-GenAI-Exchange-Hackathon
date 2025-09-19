from flask import Flask, request, jsonify
import os
import json
from google.cloud import speech
from google.cloud import language_v1
from google.oauth2 import service_account
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# --- Service account credentials ---
CREDENTIALS_PATH = "D:\\Hackathons\\Google_GenAI_Exchange_Hackathon\\MindScape-Project\\credentials\\genai-exchange-hack-4c8e1b0ee7a3.json"
credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)

# --- Initialize Gemini with API Key ---
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file.")
genai.configure(api_key=api_key)


def load_mental_health_resources():
    """Loads mental health resources from the JSON knowledge base."""
    try:
        with open(os.path.join("data", "resources.json"), 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("WARNING: resources.json not found.")
        return {}

mental_health_resources = load_mental_health_resources()


# IMPROVEMENT: New function to classify distress level using Gemini
def classify_distress_level_with_gemini(text):
    """
    Uses Gemini to classify the user's text into a specific distress level.
    """
    gemini_model = genai.GenerativeModel("gemini-1.5-flash-latest")
    
    prompt = f"""You are an expert psychological text analyst. Your task is to classify the user's mental state based on their journal entry.
    
    Analyze the following text and classify its distress level into one of these four categories ONLY: [crisis, moderate, mild, none].

    - 'crisis': User expresses suicidal thoughts, extreme hopelessness, self-harm, or is in immediate danger. Examples: "I want to end it all", "I can't go on anymore", "Life isn't worth living".
    - 'moderate': User expresses strong feelings of depression, anxiety, loneliness, or significant emotional pain. Examples: "I feel so alone and sad all the time", "My anxiety is overwhelming me".
    - 'mild': User expresses general stress, frustration, sadness, or worry. Examples: "I'm feeling stressed about my exams", "I had a bad day".
    - 'none': User expresses neutral or positive feelings.

    User's text: "{text}"

    Your response must ONLY be one of the four category names (crisis, moderate, mild, none) and nothing else.
    """
    
    try:
        response = gemini_model.generate_content(prompt)
        # Clean up the response to ensure it's just one of the keywords
        classification = response.text.strip().lower()
        if classification in ["crisis", "moderate", "mild", "none"]:
            return classification
        else:
            # Fallback in case of an unexpected response from Gemini
            return "mild" 
    except Exception as e:
        print(f"Error in Gemini classification: {e}")
        return "mild" # Default to 'mild' on error


# IMPROVEMENT: Retrieval logic is now based on the distress level classification
def retrieve_resources_by_distress_level(distress_level):
    """
    Retrieves relevant mental health resources from the knowledge base
    based on the classified distress level.
    """
    if not mental_health_resources:
        return None

    if distress_level == "crisis":
        return mental_health_resources.get("crisis_hotlines")
    elif distress_level == "moderate":
        return mental_health_resources.get("online_counseling")
    elif distress_level == "mild":
        return mental_health_resources.get("youth_communities")
    else: # "none"
        return None


def generate_gemini_response(text, resources=None):
    """
    Generates a response using the Gemini API.
    Optionally includes retrieved resources for a more helpful response.
    """
    gemini_model = genai.GenerativeModel("gemini-1.5-flash-latest")
    
    if resources:
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

    # (The Speech-to-Text part remains exactly the same...)
    audio_file = request.files["audio_data"]
    filename = audio_file.filename
    
    if not os.path.exists("temp"):
        os.makedirs("temp")

    temp_path = os.path.join("temp", filename)
    audio_file.save(temp_path)

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

    # (The original sentiment analysis can still be useful for other purposes, so we keep it)
    language_client = language_v1.LanguageServiceClient(credentials=credentials)
    document = language_v1.Document(content=transcript, type_=language_v1.Document.Type.PLAIN_TEXT)
    sentiment = language_client.analyze_sentiment(document=document).document_sentiment

    # IMPROVEMENT: Classify distress level using our new function
    distress_level = classify_distress_level_with_gemini(transcript)

    # IMPROVEMENT: Retrieve resources based on the new, more accurate classification
    relevant_resources = retrieve_resources_by_distress_level(distress_level)

    # Pass the retrieved resources to Gemini for the final response
    gemini_response = generate_gemini_response(transcript, resources=relevant_resources)

    return jsonify({
        "transcript": transcript,
        "sentiment_score": sentiment.score, # Still useful to return
        "sentiment_magnitude": sentiment.magnitude,
        "distress_level": distress_level, # IMPROVEMENT: Return the new classification for debugging/UI
        "gemini_response": gemini_response
    })

if __name__ == "__main__":
    app.run(debug=True, port=5001)