const DEFAULT_MODEL = "gemini-1.5-flash";

function sendJson(res, statusCode, payload) {
    res.statusCode = statusCode;
    res.setHeader("Content-Type", "application/json");
    res.end(JSON.stringify(payload));
}

function getQuestion(req) {
    if (typeof req.body === "string") {
        return JSON.parse(req.body).question;
    }

    return req.body && req.body.question;
}

module.exports = async function handler(req, res) {
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type");

    if (req.method === "OPTIONS") {
        res.statusCode = 204;
        res.end();
        return;
    }

    if (req.method !== "POST") {
        sendJson(res, 405, { error: "Method not allowed" });
        return;
    }

    const apiKey = process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY;
    if (!apiKey) {
        sendJson(res, 500, { error: "Missing GEMINI_API_KEY environment variable." });
        return;
    }

    let question;
    try {
        question = getQuestion(req);
    } catch (error) {
        sendJson(res, 400, { error: "Invalid JSON body." });
        return;
    }

    if (!question || typeof question !== "string") {
        sendJson(res, 400, { error: "Question is required." });
        return;
    }

    const model = process.env.GEMINI_MODEL || DEFAULT_MODEL;
    const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`;

    try {
        const geminiResponse = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                contents: [
                    {
                        role: "user",
                        parts: [
                            {
                                text: `You are Daisy, a concise and warm voice assistant. Answer briefly.\n\nUser: ${question}`
                            }
                        ]
                    }
                ],
                generationConfig: {
                    temperature: 0.7,
                    maxOutputTokens: 180
                }
            })
        });

        const data = await geminiResponse.json();

        if (!geminiResponse.ok) {
            const message = data.error && data.error.message
                ? data.error.message
                : "Gemini request failed.";
            sendJson(res, geminiResponse.status, { error: message });
            return;
        }

        const reply = data.candidates
            && data.candidates[0]
            && data.candidates[0].content
            && data.candidates[0].content.parts
            && data.candidates[0].content.parts.map((part) => part.text || "").join("").trim();

        sendJson(res, 200, {
            reply: reply || "I could not think of a response right now."
        });
    } catch (error) {
        sendJson(res, 500, { error: "Unable to reach Gemini." });
    }
};
