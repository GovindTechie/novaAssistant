Nova Assistant
==============

Nova Assistant is a Flask-based personal assistant application with voice command 
integration, Gemini API connectivity, and browser-based text-to-speech. It’s 
designed to work both locally (with direct microphone access) and on headless 
environments like Render (using browser-based audio recording).

Features
--------
- Voice Commands:
  - Locally: Captures audio using your system microphone via speech_recognition.
  - On Render or other headless environments: Records audio in the browser and 
    uploads it to the server for speech recognition.
- Text-to-Speech (Browser):
  - Uses the Web Speech API for spoken responses directly in the user’s browser.
- Gemini API Integration:
  - Answers user queries by calling the Gemini API (requires a GEMINI_API_KEY).
- Web UI:
  - A responsive interface built with Flask templates and static files 
    (HTML, CSS, JavaScript).

Requirements
------------
- Python 3.8+
- Flask
- python-dotenv
- requests
- SpeechRecognition
- gunicorn

Installation
------------
1. Clone the Repository:
   git clone https://github.com/YourUsername/nova-assistant.git
   cd nova-assistant

2. Install Dependencies:
   pip install -r requirements.txt

3. Set Up Environment Variables:
   - Create a .env file in the root directory with:
     GEMINI_API_KEY=your_gemini_api_key
   - Replace 'your_gemini_api_key' with your actual key.

Running Locally
---------------
1. Start the Flask App:
   python app.py

2. Open in Browser:
   Visit http://127.0.0.1:5000 to access the Nova Assistant interface.
   Use the microphone button (server-side mic) or browser-based recording 
   section, depending on your environment.

Deploying on Render
-------------------
1. Push Code to GitHub:
   Make sure your code and requirements.txt are committed to a GitHub repository.

2. Create a New Web Service on Render:
   - Sign in to https://render.com/
   - Select "New" → "Web Service"
   - Connect your GitHub repository
   - Build Command: pip install -r requirements.txt
   - Start Command: gunicorn app:app --bind 0.0.0.0:5000

3. Set Environment Variables:
   Add GEMINI_API_KEY in the Render dashboard to match your .env setup.

4. Deploy & Test:
   Wait for the build to finish, then visit the generated URL to test your assistant.

Usage
-----
- Local Voice Command:
  Click "Click to speak" to record audio using your PC microphone 
  (works only when running locally with a real microphone).
- Browser Recording (Headless):
  Click "Start Recording," then "Stop Recording," and finally 
  "Upload Recorded Audio" to process commands on a remote server (e.g., Render).
- Text Commands:
  Type your query in the "Type your command here…" field and press "Send."

License
-------
This project is licensed under the MIT License – feel free to modify as needed.

Acknowledgments
---------------
- Flask for the web framework
- SpeechRecognition for voice capture
- Web Speech API for browser-based TTS
- Render for hosting

Author
------
Govind Khedkar
(Feel free to add more details or links here.)
