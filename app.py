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
    model = genai.GenerativeModel('gemini-pro')
    return model

try:
    gemini_model = configure_gemini()
except ValueError as e:
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

        # Save the chat message to MongoDB
        message_data = {
            "user_message": user_message,
            "bot_response": bot_response
        }
        collection = get_collection()
        collection.insert_one(message_data)

        print(f"Gemini Response: {bot_response}")
        return jsonify({"response": bot_response})

    except Exception as e:
        print(f"Error generating response: {e}")

        # Still save the user message, even if the bot fails (log error)
        message_data = {
            "user_message": user_message,
            "bot_response": "I'm sorry, there was an error generating a response."
        }
        collection = get_collection()
        collection.insert_one(message_data)

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