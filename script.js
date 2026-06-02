// ── DOM Elements ──────────────────────────────────
const startBtn   = document.getElementById("startBtn");
const stopBtn    = document.getElementById("stopBtn");
const statusText = document.getElementById("status");
const orbWrapper = document.getElementById("orbWrapper");

// ── Speech API Check ──────────────────────────────
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (!SpeechRecognition) {
    statusText.innerText = "Speech Recognition not supported. Use Chrome or Edge.";
    startBtn.disabled = true;
}

// ── State ─────────────────────────────────────────
let recognition  = null;
let isActive     = false;
let isSpeaking   = false;
let greetingDone = false;

// ── Helpers: Orb states ───────────────────────────
function setOrb(state) {
    orbWrapper.classList.remove("idle", "listening", "speaking");
    if (state) orbWrapper.classList.add(state);
}

// ── Check if text contains the wake word ──────────
function isWakeWord(text) {
    const lower = text.toLowerCase().replace(/[^a-z\s]/g, "");
    const triggers = [
        "hey daisy", "hi daisy", "hay daisy", "hey desi",
        "a daisy", "hey dazy", "hey dasey", "hey daisie",
        "hey daisi", "he daisy", "hey dazie", "haye daisy",
        "hey daise", "hey dizzy", "hey lazy", "hey deisy",
        "they daisy", "hey daizy"
    ];
    return triggers.some(t => lower.includes(t));
}

// ── Start listening ───────────────────────────────
function startListening() {
    if (!isActive || isSpeaking) return;

    // Always create a fresh instance to avoid Chrome bugs
    if (recognition) {
        try { recognition.abort(); } catch(e) {}
        recognition = null;
    }

    recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.continuous = true;
    recognition.interimResults = false;

    recognition.onstart = () => {
        console.log("[Daisy] Recognition started");
        if (!isSpeaking) {
            setOrb("listening");
            statusText.innerText = greetingDone
                ? "Listening... ask me anything"
                : "Listening... say Hey Daisy";
        }
    };

    recognition.onresult = (event) => {
        // Get the latest final result
        for (let i = event.resultIndex; i < event.results.length; i++) {
            if (!event.results[i].isFinal) continue;

            const transcript = event.results[i][0].transcript.trim();
            console.log("[Daisy] Heard:", transcript);

            // WAKE WORD CHECK
            if (!greetingDone && isWakeWord(transcript)) {
                console.log("[Daisy] Wake word detected!");
                greetingDone = true;

                // Stop recognition before speaking
                try { recognition.abort(); } catch(e) {}
                speak("How can I help you dad?");
                return;
            }

            // FOLLOW-UP QUESTION (after greeting)
            if (greetingDone) {
                console.log("[Daisy] Sending to Gemini:", transcript);
                try { recognition.abort(); } catch(e) {}
                askGemini(transcript);
                return;
            }

            // Not the wake word — just keep listening
            console.log("[Daisy] Not a wake word, still listening...");
        }
    };

    recognition.onerror = (event) => {
        console.log("[Daisy] Error:", event.error);

        if (event.error === "not-allowed" || event.error === "service-not-allowed") {
            isActive = false;
            setOrb(null);
            statusText.innerText = "Microphone blocked. Allow permission and click Start.";
            return;
        }

        // For any other error, restart after a short delay
        if (isActive && !isSpeaking) {
            setTimeout(startListening, 800);
        }
    };

    recognition.onend = () => {
        console.log("[Daisy] Recognition ended");
        // Auto-restart if we're still active and not speaking
        if (isActive && !isSpeaking) {
            setTimeout(startListening, 400);
        }
    };

    try {
        recognition.start();
        console.log("[Daisy] Calling recognition.start()");
    } catch (e) {
        console.log("[Daisy] Start failed:", e.message);
        setTimeout(startListening, 800);
    }
}

// ── Speak with SpeechSynthesis ────────────────────
function speak(text) {
    isSpeaking = true;
    setOrb("speaking");
    statusText.innerText = "Daisy is speaking...";

    // Stop any ongoing recognition
    if (recognition) {
        try { recognition.abort(); } catch(e) {}
        recognition = null;
    }

    const utterance  = new SpeechSynthesisUtterance(text);
    utterance.lang   = "en-US";
    utterance.rate   = 1;
    utterance.pitch  = 1.1;

    // Try to pick a nice voice
    const voices = window.speechSynthesis.getVoices();
    const preferred = voices.find(v =>
        /zira|samantha|google.*female|female/i.test(v.name));
    if (preferred) utterance.voice = preferred;

    utterance.onend = () => {
        console.log("[Daisy] Done speaking");
        isSpeaking = false;
        if (isActive) startListening();
    };

    utterance.onerror = (e) => {
        console.log("[Daisy] Speech error:", e);
        isSpeaking = false;
        if (isActive) startListening();
    };

    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
}

// ── Ask the Gemini backend ────────────────────────
async function askGemini(question) {
    setOrb("speaking");
    statusText.innerText = "Thinking...";

    try {
        const res = await fetch("/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question })
        });
        const data = await res.json();
        console.log("[Daisy] Gemini replied:", data.reply);
        speak(data.reply);
    } catch (err) {
        console.error("[Daisy] Backend error:", err);
        speak("Sorry, I could not connect to my brain right now.");
    }
}

// ── Button handlers ───────────────────────────────
startBtn.addEventListener("click", () => {
    if (isActive) return;
    console.log("[Daisy] START clicked");
    isActive     = true;
    greetingDone = false;

    // Pre-load voices
    window.speechSynthesis.getVoices();

    startListening();
});

stopBtn.addEventListener("click", () => {
    console.log("[Daisy] STOP clicked");
    isActive     = false;
    isSpeaking   = false;
    greetingDone = false;

    window.speechSynthesis.cancel();
    if (recognition) {
        try { recognition.abort(); } catch(e) {}
        recognition = null;
    }
    setOrb(null);
    statusText.innerText = "Stopped. Click Start to begin.";
});

// Pre-load voices (needed in Chrome)
window.speechSynthesis.getVoices();
if (speechSynthesis.onvoiceschanged !== undefined) {
    speechSynthesis.onvoiceschanged = () => speechSynthesis.getVoices();
}

console.log("[Daisy] Script loaded successfully ✓");