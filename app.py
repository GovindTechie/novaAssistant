import os
import time
import datetime
import webbrowser
import requests
import speech_recognition as sr
import logging
import platform
from dotenv import load_dotenv
from flask import Flask, render_template, jsonify, request, Response
from werkzeug.utils import secure_filename
from pydub import AudioSegment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logging.error("GEMINI_API_KEY is not set. Please add it to your .env file.")
    raise ValueError("GEMINI_API_KEY is not set. Please add it to your .env file.")

app = Flask(__name__)

# Use a different upload folder when deployed on Render
UPLOAD_FOLDER = "/tmp/uploads" if os.getenv("RENDER") else "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ------------------ Original Functions ------------------

def speak(text):
    """
    Instead of generating an MP3 and playing it,
    this function simply logs the text.
    """
    logging.info("TTS (simulated): %s", text)

def stop_speech():
    """
    Since we're not actually playing audio, there's nothing to stop.
    """
    return "Speech stopped. (No live speech to cancel.)"

def query_gemini(prompt):
    """
    Query the Gemini API using the provided prompt.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except requests.RequestException as e:
        logging.error("Error querying Gemini API: %s", e)
        return "Error: Unable to contact Gemini API."
    except (KeyError, IndexError) as e:
        logging.error("Unexpected response format: %s", e)
        return "Error: Unexpected response format from Gemini API."

def take_command():
    """
    Listen for a voice command using the microphone.
    Returns the recognized command as text, or "None" if recognition fails.
    """
    r = sr.Recognizer()
    with sr.Microphone() as source:
        logging.info("Listening for voice command...")
        r.pause_threshold = 0.8
        r.energy_threshold = 300
        try:
            audio = r.listen(source, timeout=5)
        except sr.WaitTimeoutError:
            logging.warning("Listening timed out.")
            return "None"
    try:
        logging.info("Recognizing voice command...")
        query = r.recognize_google(audio, language="en-in")
        logging.info("User said: %s", query)
        return query
    except sr.UnknownValueError:
        logging.warning("Could not understand audio.")
        return "None"
    except sr.RequestError as e:
        logging.error("Speech recognition error: %s", e)
        return "None"

def open_desktop_app(app_name):
    """
    Attempt to open an application via the Windows Start Menu.
    Only works on Windows. On other OS, logs a warning.
    """
    if platform.system() == "Windows":
        try:
            speak(f"Searching for {app_name} in the Start Menu...")
            if "calculator" in app_name.lower():
                speak(f"Opening {app_name}...")
                os.system("calc")
            elif "notepad" in app_name.lower():
                speak(f"Opening {app_name}...")
                os.system("notepad")
            else:
                speak(f"Opening {app_name}...")
                os.system(f'start {app_name}')
            return f"Opening {app_name} on your desktop..."
        except Exception as e:
            logging.error("Error opening desktop app: %s", e)
            speak(f"Sorry, I couldn't open {app_name}.")
            return f"Error: {e}"
    else:
        logging.warning("Desktop app opening is only supported on Windows.")
        speak("Desktop app opening is only supported on Windows.")
        return "Desktop app opening is only supported on Windows."

def process_command(command):
    """
    Process a voice or manual command.
    Returns either:
      - A Flask Response object (if we want to return JSON for open/search).
      - A string (if we just want to return text).
    """
    command_lower = command.lower().strip()
    response_text = ""

    # 1. Basic "who are you?" question
    if command_lower in ["who are you", "what is your name", "who r u"]:
        response_text = "I am Nova, your personal assistant created by Govind Khedkar."
        speak(response_text)
        return response_text

    # 2. Exit command
    elif command_lower in ["exit", "exits"]:
        speak("Goodbye!")
        response_text = "Goodbye! Exiting now..."

    # 3. If command is not empty/none
    elif command_lower and command_lower != "none":
        if "open" in command_lower:
            if "desktop" in command_lower:
                response_text = "Desktop app commands work only locally."
            else:
                website = command_lower.split("open", 1)[1].strip().replace(" ", "")
                url = f"https://www.{website}.com"
                response_text = f"Opening website: {website}"
                return jsonify({"result": response_text, "command": command, "open_url": url})
        elif "search" in command_lower:
            search_query = command_lower.split("search", 1)[1].strip()
            if search_query:
                speak(f"Searching for {search_query} on Google...")
                query_str = search_query.replace(" ", "+")
                url = f"https://www.google.com/search?q={query_str}"
                response_text = f"Searching for: {search_query}"
                return jsonify({"result": response_text, "command": command, "open_url": url})
        elif "play music" in command_lower:
            music_name = command_lower.split("play music", 1)[1].strip()
            if music_name:
                speak(f"Searching for {music_name} on YouTube...")
                query_str = music_name.replace(" ", "+")
                url = f"https://www.youtube.com/results?search_query={query_str}"
                response_text = f"Playing music: {music_name} on YouTube"
                return jsonify({"result": response_text, "command": command, "open_url": url})
            else:
                speak("Please specify the song name.")
                response_text = "No song name provided."
        elif "the time" in command_lower:
            import pytz
            tz = pytz.timezone('Asia/Kolkata')
            current_time = datetime.datetime.now(tz).strftime("%I:%M %p")
            speak(f"The time is {current_time}")
            response_text = f"The time is {current_time}"
        else:
            gemini_response = query_gemini(command)
            # Remove asterisks from the Gemini response
            clean_response = gemini_response.replace("*", "")
            speak(clean_response)
            response_text = clean_response

    else:
        speak("I didn't catch that. Please try again.")
        response_text = "No valid command recognized."

    return response_text

# ----------------- Flask Routes -----------------

@app.route('/')
def index():
    return render_template("base.html")

@app.route('/listen', methods=["POST"])
def listen():
    # For hosted environments, instruct users to use browser-based recording
    return jsonify({
        "result": "Direct microphone input is not available in this environment. Please use the browser-based audio recording/upload functionality.",
        "command": ""
    })

@app.route('/command', methods=["POST"])
def command_route():
    data = request.get_json()
    command_text = data.get("command", "")
    outcome = process_command(command_text)
    if isinstance(outcome, Response):
        return outcome
    else:
        return jsonify({"result": outcome, "command": command_text})

@app.route('/stop_speech', methods=["POST"])
def stop_speech_route():
    result = stop_speech()
    return jsonify({"result": result})

@app.route('/suggest')
def suggest():
    q = request.args.get("q", "")
    suggestions = [
        "weather",
        "news today",
        "best music",
        "time now",
        "latest headlines"
    ]
    return jsonify([q, suggestions])

# ----------------- New Endpoint for Audio Upload -----------------

@app.route('/upload', methods=["POST"])
def upload_audio():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    # Always attempt to convert the uploaded file to WAV.
    try:
        # Use pydub to open the file (auto-detects format)
        sound = AudioSegment.from_file(filepath)
        # Export the sound to WAV using default parameters
        new_filepath = os.path.splitext(filepath)[0] + '.wav'
        sound.export(new_filepath, format="wav")
        filepath = new_filepath
    except Exception as e:
        return jsonify({"error": f"Audio conversion error: {e}"}), 500

    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(filepath) as source:
            audio = recognizer.record(source)
        recognized_text = recognizer.recognize_google(audio)
        return jsonify({"message": "Success", "text": recognized_text})
    except sr.UnknownValueError:
        return jsonify({"error": "Could not understand audio"}), 400
    except sr.RequestError as e:
        return jsonify({"error": f"Speech Recognition service error: {e}"}), 500


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
