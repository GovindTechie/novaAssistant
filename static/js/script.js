/*
 * script.js
 *
 * This file manages UI interactions for NOVA Assistant.
 */

document.addEventListener("DOMContentLoaded", function() {
    attachResultControlEvents();
});

let currentController = null;

function updateResult(text) {
  const resultText = document.getElementById("resultText");
  resultText.style.opacity = 0;
  setTimeout(() => {
    resultText.innerText = text;
    resultText.style.opacity = 1;
  }, 100);
}

function attachResultControlEvents() {
  const copyBtn = document.getElementById("copyResult");
  const clearBtn = document.getElementById("clearResult");

  if (copyBtn) {
    copyBtn.addEventListener("click", function() {
      const fullText = document.getElementById("resultText").innerText;
      navigator.clipboard.writeText(fullText).then(() => {
        alert("Response copied to clipboard!");
      });
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener("click", function() {
      updateResult("");
    });
  }
}

function updateInteraction(text) {
  document.getElementById("interactionText").innerText = text;
}

/* --- Disable Search Suggestions by commenting out these functions ---
function fetchSuggestions(query) {
  fetch(`/suggest?q=${encodeURIComponent(query)}`)
    .then(response => response.json())
    .then(data => {
      if (data && data[1]) {
        showSuggestions(data[1]);
      }
    })
    .catch(error => console.error("Error fetching suggestions:", error));
}

function showSuggestions(suggestions) {
  const suggestionsDiv = document.getElementById("suggestions");
  suggestionsDiv.innerHTML = "";
  suggestions.forEach(s => {
    const div = document.createElement("div");
    div.classList.add("suggestion-item");
    div.innerText = s;
    div.addEventListener("click", function() {
      document.getElementById("manualCommand").value = "search " + s;
      clearSuggestions();
    });
    suggestionsDiv.appendChild(div);
  });
}

function clearSuggestions() {
  document.getElementById("suggestions").innerHTML = "";
}
--- End Suggestions --- */

const manualCommandInput = document.getElementById("manualCommand");
manualCommandInput.addEventListener("keyup", function(e) {
  const value = this.value;
  // Search suggestions disabled:
  // if (value.toLowerCase().startsWith("search ")) {
  //   const parts = value.split(" ");
  //   if (parts.length > 1) {
  //     const query = parts.slice(1).join(" ");
  //     fetchSuggestions(query);
  //   }
  // } else {
  //   clearSuggestions();
  // }
});

manualCommandInput.addEventListener("keydown", function(e) {
  if (e.key === "Tab") {
    // Disable suggestion navigation since suggestions are disabled.
    e.preventDefault();
  }
});

document.getElementById("micButton").addEventListener("click", function() {
  updateInteraction("Speak now...");
  updateResult("");
  currentController = new AbortController();
  fetch("/listen", { 
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
    signal: currentController.signal
  })
  .then(response => response.json())
  .then(data => {
    updateResult(data.result);
    document.getElementById("sendCommand").innerText = "Send";
    speakBrowser(data.result);
    // If the server returns an open_url, open it on the client side.
    if (data.open_url) {
      window.open(data.open_url, '_blank');
    }
  })
  .catch(error => {
    if (error.name === 'AbortError') {
      updateResult("Response generation stopped.");
    } else {
      updateResult("An error occurred. Please try again later.");
      console.error("Error:", error);
    }
    document.getElementById("sendCommand").innerText = "Send";
  });
});

document.getElementById("stopSpeechButton").addEventListener("click", function() {
  window.speechSynthesis.cancel();
});

function sendManualCommand() {
  let commandText = manualCommandInput.value;
  if (!commandText) return;

  updateInteraction("Processing command...");
  updateResult("");
  const sendBtn = document.getElementById("sendCommand");
  sendBtn.innerText = "Stop";

  if (commandText.trim().toLowerCase() === "who are you?") {
    const intro = "Hello, I'm Nova Desk – your next-generation AI companion and virtual assistant integrated with Gemini. Developed by Govind Khedkar in Beed, Maharashtra. How can I help you today?";
    updateResult(intro);
    sendBtn.innerText = "Send";
    speakBrowser(intro);
    return;
  }

  currentController = new AbortController();
  fetch("/command", { 
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ command: commandText }),
    signal: currentController.signal
  })
  .then(response => response.json())
  .then(data => {
    updateResult(data.result);
    sendBtn.innerText = "Send";
    speakBrowser(data.result);
    if (data.open_url) {
      window.open(data.open_url, '_blank');
    }
  })
  .catch(error => {
    if (error.name === 'AbortError') {
      updateResult("Response generation stopped.");
    } else {
      updateResult("An error occurred. Please try again later.");
      console.error("Error:", error);
    }
    sendBtn.innerText = "Send";
  });
}

document.getElementById("sendCommand").addEventListener("click", function() {
  const btn = document.getElementById("sendCommand");
  if (btn.innerText === "Stop" && currentController) {
    currentController.abort();
  } else {
    sendManualCommand();
  }
});

manualCommandInput.addEventListener("keydown", function(e) {
  if (e.key === "Enter") {
    sendManualCommand();
  }
});

// ----------------- Browser-Based Audio Recording -----------------

let mediaRecorder;
let recordedChunks = [];

async function startBrowserRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    recordedChunks = [];

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        recordedChunks.push(event.data);
      }
    };

    mediaRecorder.onstop = () => {
      const audioBlob = new Blob(recordedChunks, { type: 'audio/wav' });
      const audioUrl = URL.createObjectURL(audioBlob);
      document.getElementById('recordedAudio').src = audioUrl;
      // Store the blob globally for uploading
      window.recordedAudioBlob = audioBlob;
    };

    mediaRecorder.start();
    updateInteraction("Recording started...");
  } catch (error) {
    console.error("Error accessing microphone:", error);
    updateInteraction("Error accessing microphone.");
  }
}

function stopBrowserRecording() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
    updateInteraction("Recording stopped. You can now upload.");
  }
}

async function uploadRecordedAudio() {
  if (!window.recordedAudioBlob) {
    alert("No recorded audio found. Please record first.");
    return;
  }

  const formData = new FormData();
  formData.append("file", window.recordedAudioBlob, "recorded_audio.wav");

  try {
    const response = await fetch("/upload", {
      method: "POST",
      body: formData
    });
    const result = await response.json();
    if (result.text) {
      updateResult(result.text);
      speakBrowser(result.text);
      alert("Audio processed: " + result.text);
    } else if (result.error) {
      updateResult(result.error);
      alert("Error: " + result.error);
    }
  } catch (error) {
    console.error("Upload error:", error);
    updateResult("Error uploading audio.");
  }
}

// Browser TTS function using Web Speech API
function speakBrowser(text) {
  const synth = window.speechSynthesis;
  const utter = new SpeechSynthesisUtterance(text);
  synth.speak(utter);
}

// Attach event listeners for audio recording buttons
document.getElementById("startRecordingBtn").addEventListener("click", startBrowserRecording);
document.getElementById("stopRecordingBtn").addEventListener("click", stopBrowserRecording);
document.getElementById("uploadRecordingBtn").addEventListener("click", uploadRecordedAudio);
