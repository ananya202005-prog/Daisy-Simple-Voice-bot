// DOM Elements
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const statusText = document.getElementById("status");
const orbWrapper = document.getElementById("orbWrapper");

// Speech API Check
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (!SpeechRecognition) {
    statusText.innerText = "Speech Recognition not supported. Use Chrome or Edge.";
    startBtn.disabled = true;
}

// State
let recognition = null;
let isActive = false;
let isSpeaking = false;
let isThinking = false;
let greetingDone = false;

// Helpers: Orb states
function setOrb(state) {
    orbWrapper.classList.remove("idle", "listening", "speaking");
    if (state) orbWrapper.classList.add(state);
}

// Check if text contains the wake word
function isWakeWord(text) {
    const lower = text.toLowerCase().replace(/[^a-z\s]/g, "");
    const triggers = [
        "hey daisy", "hi daisy", "hay daisy", "hey desi",
        "a daisy", "hey dazy", "hey dasey", "hey daisie",
        "hey daisi", "he daisy", "hey dazie", "haye daisy",
        "hey daise", "hey dizzy", "hey lazy", "hey deisy",
        "they daisy", "hey daizy"
    ];
    return triggers.some((trigger) => lower.includes(trigger));
}

// Initialize SpeechRecognition once if supported
if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.continuous = true;
    recognition.interimResults = false;

    recognition.onstart = () => {
        console.log("[Daisy] Recognition started");
        if (!isSpeaking && !isThinking) {
            setOrb("listening");
            statusText.innerText = greetingDone
                ? "Listening... ask me anything"
                : "Listening... say Hey Daisy";
        }
    };

    recognition.onresult = (event) => {
        for (let i = event.resultIndex; i < event.results.length; i++) {
            if (!event.results[i].isFinal) continue;

            const transcript = event.results[i][0].transcript.trim();
            console.log("[Daisy] Heard:", transcript);

            if (!greetingDone && isWakeWord(transcript)) {
                console.log("[Daisy] Wake word detected");
                greetingDone = true;
                isThinking = true;
                try { recognition.abort(); } catch (error) {}
                speak("How can I help you today?");
                return;
            }
            if (greetingDone) {
                console.log("[Daisy] Sending to Sheet Agent:", transcript);
                isThinking = true;
                try { recognition.abort(); } catch (error) {}
                askSheetAgent(transcript);
                return;
            }
        }

        console.log("[Daisy] Not a wake word, still listening...");
    };

    recognition.onerror = (event) => {
        console.log("[Daisy] Error:", event.error);

        if (event.error === "not-allowed" || event.error === "service-not-allowed") {
            isActive = false;
            setOrb("idle");
            statusText.innerText = "Microphone blocked. Allow permission and click Start.";
            return;
        }

        // Only retry starting if active and not already processing speech or thinking
        if (isActive && !isSpeaking && !isThinking) {
            setTimeout(startListening, 800);
        }
    };

    recognition.onend = () => {
        console.log("[Daisy] Recognition ended");
        if (isActive && !isSpeaking && !isThinking) {
            setTimeout(startListening, 400);
        }
    };
}

// Start listening function
function startListening() {
    console.log("[Daisy] startListening called", { isActive, isSpeaking, isThinking });

    if (!isActive || isSpeaking || isThinking || !recognition) {
        console.log("[Daisy] startListening stopped by condition");
        return;
    }

    try {
        recognition.start();
        console.log("[Daisy] Calling recognition.start()");
    } catch (error) {
        console.log("[Daisy] Start failed (likely already running):", error.message);
    }
}

// Speak with SpeechSynthesis
function speak(text) {
    isSpeaking = true;
    isThinking = false;
    setOrb("speaking");
    statusText.innerText = "Daisy is speaking...";

    // Ensure recognition is stopped while speaking
    if (recognition) {
        try { recognition.abort(); } catch (error) {}
    }

    let utterance = new SpeechSynthesisUtterance(text);

    utterance.lang = "en-US";
    utterance.rate = 1;
    utterance.pitch = 1.1;

    utterance.onend = () => {
        console.log("[Daisy] Done speaking");
        isSpeaking = false;

        if (isActive) {
            startListening();
        } else {
            setOrb("idle");
        }
    };

    utterance.onerror = (event) => {
        console.log("[Daisy] Speech error:", event);
        isSpeaking = false;
        if (isActive) {
            startListening();
        }
    };

    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
}

// Ask the Python Google Sheet backend
async function askSheetAgent(question) {
    setOrb("speaking");
    statusText.innerText = "Thinking...";

    try {
        const res = await fetch("http://127.0.0.1:8000/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question })
        });
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.error || `Request failed with ${res.status}`);
        }

        console.log("[Daisy] Sheet Agent replied:", data.reply);
        isThinking = false;
        speak(data.reply || "I did not get a clear answer.");
    } catch (error) {
        console.error("[Daisy] Backend error:", error);
        isThinking = false;
        speak("Sorry, I could not connect to my brain right now.");
    }
}

// Button handlers
startBtn.addEventListener("click", async () => {
    console.log("[Daisy] START button clicked");

    try {
        await navigator.mediaDevices.getUserMedia({ audio: true });
        console.log("[Daisy] Microphone allowed");
    } catch (error) {
        console.error("[Daisy] Microphone error:", error);
        statusText.innerText = "Please allow microphone access.";
        return;
    }

    isActive = true;
    isSpeaking = false;
    isThinking = false;
    greetingDone = false;

    setOrb("listening");
    statusText.innerText = "Listening... say Hey Daisy";

    startListening();
});

stopBtn.addEventListener("click", () => {
    console.log("[Daisy] STOP clicked");
    isActive = false;
    isSpeaking = false;
    isThinking = false;
    greetingDone = false;

    window.speechSynthesis.cancel();
    if (recognition) {
        try { recognition.abort(); } catch (error) {}
    }
    setOrb("idle");
    statusText.innerText = "Stopped. Click Start to begin.";
});

window.speechSynthesis.getVoices();
if (speechSynthesis.onvoiceschanged !== undefined) {
    speechSynthesis.onvoiceschanged = () => speechSynthesis.getVoices();
}

setOrb("idle");
console.log("[Daisy] Script loaded successfully");
