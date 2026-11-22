from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

app = Flask(__name__)

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI")
# print(f"MONGO_URI from .env: {MONGO_URI}") 
DATABASE_NAME = "chatbot_db"
COLLECTION_NAME = "chat_messages"

def get_mongo_client():
    return MongoClient(MONGO_URI)

def get_db():
    client = get_mongo_client()
    return client[DATABASE_NAME]

def get_collection():
    db = get_db()
    return db[COLLECTION_NAME]

# Configure Gemini
def configure_gemini():
    if not GOOGLE_API_KEY:
        raise ValueError("The Google Api is not set or found")
    genai.configure(api_key=GOOGLE_API_KEY)

    supported_models = [
        model.name
        for model in genai.list_models()
        if "generateContent" in model.supported_generation_methods
    ]
    preferred_models = [
        "models/gemini-flash-lite-latest",
        "models/gemini-flash-latest",
        "models/gemini-3.8-flash",
        "models/gemini-2.5-flash",
    ]
    model_name = next(
        (name for name in preferred_models if name in supported_models),
        supported_models[0] if supported_models else None,
    )

    if model_name is None:
        raise ValueError("No Gemini model supporting generateContent is available")

    print(f"Using Gemini model: {model_name}")
    return genai.GenerativeModel(model_name)

try:
    gemini_model = configure_gemini()
except Exception as e:
    print(f"Configuration Error: {e}")
    gemini_model = None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get_response", methods=["POST"])
def get_response():
    user_message = request.form["message"]
    print(f"User Message: {user_message}")

    if gemini_model is None:
        return jsonify({"response": "Gemini model is not configured. Check the server logs."})

    try:
        response = gemini_model.generate_content(user_message)
        bot_response = response.text

        # MongoDB persistence is optional and must not block a chatbot response.
        message_data = {
            "user_message": user_message,
            "bot_response": bot_response
        }
        if MONGO_URI:
            try:
                collection = get_collection()
                collection.insert_one(message_data)
            except Exception as mongo_error:
                print(f"MongoDB persistence error: {mongo_error}")

        print(f"Gemini Response: {bot_response}")
        return jsonify({"response": bot_response})

    except Exception as e:
        print(f"Error generating response: {e}")

        # Still save the user message, even if the bot fails (log error)
        message_data = {
            "user_message": user_message,
            "bot_response": "I'm sorry, there was an error generating a response."
        }
        if MONGO_URI:
            try:
                collection = get_collection()
                collection.insert_one(message_data)
            except Exception as mongo_error:
                print(f"MongoDB persistence error: {mongo_error}")

        return jsonify({"response": "I'm sorry, I encountered an error."})

@app.route("/history")
def history():
    collection = get_collection()
    messages = list(collection.find().sort("_id", -1).limit(20))  # Get last 20 messages

    for message in messages:
        message["_id"] = str(message["_id"])

    return render_template("history.html", messages=messages)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)