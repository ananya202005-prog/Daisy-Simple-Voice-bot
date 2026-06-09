import os
import traceback
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import urllib.request
import json
import gspread
from google.oauth2.service_account import Credentials

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str

def get_sheet_data():
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

    credentials = Credentials.from_service_account_info(
        {
            "type": "service_account",
            "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
            "private_key": os.getenv("GOOGLE_PRIVATE_KEY").replace("\\n", "\n"),
            "token_uri": "https://oauth2.googleapis.com/token",
        },
        scopes=scopes,
    )

    client = gspread.authorize(credentials)

    sheet = client.open_by_key(os.getenv("GOOGLE_SHEET_ID"))
    worksheet = sheet.worksheet("Sheet1")

    return worksheet.get_all_records()

def format_list(items):
    if not items:
        return ""
    if len(items) == 1:
        return str(items[0])
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(map(str, items[:-1])) + f", and {items[-1]}"

def find_answer(question, rows):
    q = question.lower()

    # 1. Try to find a specific record mentioned in the query (by name, company, email, etc.)
    person_row = None
    
    # Sort rows to prioritize exact or better matches if needed, but linear search is fine
    for row in rows:
        first = str(row.get("First_Name", "")).strip()
        last = str(row.get("Last Name", "")).strip()
        full = f"{first} {last}".strip()
        
        matched = False
        # Match by name
        if full and full.lower() in q:
            matched = True
        elif first and first.lower() in q:
            matched = True
        elif last and last.lower() in q:
            matched = True
            
        # Match by other fields if name didn't match
        if not matched:
            for key, val in row.items():
                str_val = str(val).strip().lower()
                # Exclude very short strings to avoid false positives with generic words
                if len(str_val) > 3 and str_val in q:
                    matched = True
                    break

        if matched:
            person_row = row
            break

    # If a specific record was matched, handle their query
    if person_row:
        first = str(person_row.get("First_Name", "")).strip()
        last = str(person_row.get("Last Name", "")).strip()
        full = f"{first} {last}".strip()
        company = str(person_row.get("Company Name", "")).strip()
        display_name = full or company or "This record"

        # Specific field mappings for a single person's details
        # Format: (list of keywords to match, column_key, output_template)
        person_mappings = [
            (["email count", "email-count", "number of email"], "Email-Count", f"{display_name} has been emailed {{val}} times."),
            (["email", "emails"], "Email", f"{display_name}'s email is {{val}}."),
            (["phone", "mobile", "number", "contact"], "Mobile", f"{display_name}'s mobile number is {{val}}."),
            (["call attempt", "call"], "Call Attempt", f"{display_name} has {{val}} call attempts."),
            (["company", "organization", "work"], "Company Name", f"{display_name} works at {{val}}."),
            (["lead source", "source"], "Lead Source", f"{display_name}'s lead source is {{val}}."),
            (["lead date"], "Lead Date", f"{display_name}'s lead date is {{val}}."),
            (["assigned", "assignee", "owner"], "Assigned To", f"{display_name} is assigned to {{val}}."),
            (["follow up count", "follow-up count", "number of follow ups"], "Follow-Up Count", f"{display_name} has {{val}} follow-ups."),
            (["last follow up date", "last follow-up-date", "last follow-up date"], "Last Follow-Up Date", f"{display_name}'s last follow-up date was {{val}}."),
            (["follow up", "followup", "next follow"], "Next Followup", f"{display_name}'s next follow-up is on {{val}}."),
            (["show", "event", "expo"], "Show", f"{display_name}'s show is {{val}}."),
            (["linkedin headline", "headline"], "LINKEDIN-HEADLINE", f"{display_name}'s LinkedIn headline is {{val}}."),
            (["linkedin reply"], "LINKEDIN-REPLY", f"{display_name}'s LinkedIn reply is: {{val}}."),
            (["linkedin url", "linkedin link"], "LINKEDIN-URL", f"{display_name}'s LinkedIn URL is {{val}}."),
            (["linkedin message", "linkedin msg", "linkedin status", "linkedin"], "Linkedin Msg", f"{display_name}'s LinkedIn message status is {{val}}."),
            (["whatsapp permission", "whats app permission"], "Whatsapp_Permission", f"{display_name}'s WhatsApp permission is {{val}}."),
            (["whatsapp", "whats app"], "WhatsApp msg count", f"{display_name}'s WhatsApp message count is {{val}}."),
            (["comment", "note"], "Comments", f"Comments for {display_name}: {{val}}."),
            (["pitch deck", "deck"], "Pitch Deck URL", f"{display_name}'s pitch deck URL is {{val}}."),
            (["interested for", "interest", "interested"], "Interested for", f"{display_name} is interested for: {{val}}."),
            (["reply status", "reply"], "Reply Status", f"{display_name}'s reply status is: {{val}}."),
            (["stand size", "booth size", "size"], "Stand Size", f"{display_name}'s stand size is {{val}}."),
            (["payment status"], "Payment Status", f"{display_name}'s payment status is {{val}}."),
            (["amount", "price", "cost", "payment"], "Amount", f"{display_name}'s amount is {{val}}."),
            (["crm lead id", "lead id"], "CRM Lead ID", f"{display_name}'s CRM lead ID is {{val}}."),
            (["crm update"], "CRM Update", f"{display_name}'s CRM update status is {{val}}."),
            (["every catch crm", "every-catch crm", "every catch"], "EVERY-CATCH CRM", f"{display_name}'s Every Catch CRM status is {{val}}."),
            (["eventbrite"], "Eventbrite Update", f"{display_name}'s Eventbrite update is {{val}}."),
            (["exhibitor mis", "mis"], "Exhibitor MIS", f"{display_name}'s Exhibitor MIS status is {{val}}."),
            (["welcome email"], "Welcome Email", f"{display_name}'s welcome email status is {{val}}."),
            (["welcome message", "welcome msg"], "Welcome Msg", f"{display_name}'s welcome message status is {{val}}."),
            (["canva"], "Canva Update", f"{display_name}'s Canva update status is {{val}}."),
            (["website"], "Website Update", f"{display_name}'s Website update status is {{val}}."),
            (["social media", "post"], "Social Media Post", f"{display_name}'s social media post status is {{val}}."),
            (["sms status", "sms"], "SMS_STATUS", f"{display_name}'s SMS status is {{val}}."),
            (["workflow"], "Workflow-Identifier", f"{display_name}'s workflow identifier is {{val}}.")
        ]

        # Sort person_mappings by max keyword length in descending order to match specific phrases first
        sorted_person_mappings = sorted(person_mappings, key=lambda m: max(len(kw) for kw in m[0]), reverse=True)
        
        for keywords, col_key, template in sorted_person_mappings:
            for kw in keywords:
                if kw in q:
                    val = person_row.get(col_key, None)
                    # Handle alternative keys or fallbacks
                    if val is None:
                        if col_key == "Comments":
                            val = person_row.get("Comment", "not available")
                        elif col_key == "Linkedin Msg":
                            val = person_row.get("LinkedIn Msg", "not available")
                        elif col_key == "WhatsApp msg count":
                            val = person_row.get("WhatsApp msg", person_row.get("WhatsApp msg ", "not available"))
                        else:
                            val = "not available"
                    else:
                        val = str(val).strip()
                        if not val or val.lower() in ["", "n/a", "none", "null"]:
                            val = "not available"
                    return template.format(val=val)

        # Default — return a summary of the record
        summary = (
            f"Here's what I know about {display_name}: "
            f"Assigned to: {person_row.get('Assigned To', 'N/A')}, "
            f"Lead Date: {person_row.get('Lead Date', 'N/A')}, "
            f"Source: {person_row.get('Lead Source', 'N/A')}, "
            f"Company: {person_row.get('Company Name', 'N/A')}, "
            f"Mobile: {person_row.get('Mobile', 'N/A')}, "
            f"Email: {person_row.get('Email', 'N/A')}, "
            f"Show: {person_row.get('Show', 'N/A')}, "
            f"Next Follow-up: {person_row.get('Next Followup', 'N/A')}, "
            f"Email Count: {person_row.get('Email-Count', 'N/A')}, "
            f"Call Attempts: {person_row.get('Call Attempt', 'N/A')}, "
            f"LinkedIn Message: {person_row.get('Linkedin Msg', person_row.get('LinkedIn Msg', 'N/A'))}, "
            f"WhatsApp Message Count: {person_row.get('WhatsApp msg count', 'N/A')}, "
            f"Comments: {person_row.get('Comments', 'N/A')}, "
            f"Pitch Deck URL: {person_row.get('Pitch Deck URL', 'N/A')}, "
            f"Interested For: {person_row.get('Interested for', 'N/A')}, "
            f"Follow-Up Count: {person_row.get('Follow-Up Count', 'N/A')}, "
            f"Last Follow-Up Date: {person_row.get('Last Follow-Up Date', 'N/A')}, "
            f"Reply Status: {person_row.get('Reply Status', 'N/A')}, "
            f"LinkedIn Headline: {person_row.get('LINKEDIN-HEADLINE', 'N/A')}, "
            f"LinkedIn Reply: {person_row.get('LINKEDIN-REPLY', 'N/A')}, "
            f"LinkedIn URL: {person_row.get('LINKEDIN-URL', 'N/A')}, "
            f"Stand Size: {person_row.get('Stand Size', 'N/A')}, "
            f"Amount: {person_row.get('Amount', 'N/A')}, "
            f"CRM Update: {person_row.get('CRM Update', 'N/A')}, "
            f"CRM Lead ID: {person_row.get('CRM Lead ID', 'N/A')}, "
            f"Eventbrite Update: {person_row.get('Eventbrite Update', 'N/A')}, "
            f"Exhibitor MIS: {person_row.get('Exhibitor MIS', 'N/A')}, "
            f"Welcome Email: {person_row.get('Welcome Email', 'N/A')}, "
            f"Welcome Msg: {person_row.get('Welcome Msg', 'N/A')}, "
            f"Canva Update: {person_row.get('Canva Update', 'N/A')}, "
            f"Website Update: {person_row.get('Website Update', 'N/A')}, "
            f"Social Media Post: {person_row.get('Social Media Post', 'N/A')}, "
            f"Payment Status: {person_row.get('Payment Status', 'N/A')}, "
            f"WhatsApp Permission: {person_row.get('Whatsapp_Permission', 'N/A')}, "
            f"SMS Status: {person_row.get('SMS_STATUS', 'N/A')}, "
            f"Workflow Identifier: {person_row.get('Workflow-Identifier', 'N/A')}, "
            f"Every Catch CRM: {person_row.get('EVERY-CATCH CRM', 'N/A')}."
        )
        return summary

    # 2. Check if the query is a column-reading request
    mappings = [
        (["first name"], "First_Name", "first names"),
        (["last name"], "Last Name", "last names"),
        (["name", "names", "people", "person"], "Name", "names"),
        (["email count", "email-count", "number of email"], "Email-Count", "email counts"),
        (["email", "emails"], "Email", "emails"),
        (["mobile", "phone", "number", "contact"], "Mobile", "mobile numbers"),
        (["call attempt", "call"], "Call Attempt", "call attempts"),
        (["company", "companies", "organization", "work"], "Company Name", "company names"),
        (["lead source", "source"], "Lead Source", "lead sources"),
        (["lead date"], "Lead Date", "lead dates"),
        (["assigned", "assignee", "owner"], "Assigned To", "assigned owners"),
        (["follow up", "followup", "next follow"], "Next Followup", "next follow-up dates"),
        (["show", "event", "expo"], "Show", "shows"),
        (["linkedin message", "linkedin msg", "linkedin status", "linkedin"], "Linkedin Msg", "LinkedIn message statuses"),
        (["whatsapp", "whats app"], "WhatsApp msg count", "WhatsApp message counts"),
        (["comment", "note"], "Comments", "comments"),
        (["pitch deck url", "pitch deck", "deck url", "deck"], "Pitch Deck URL", "pitch deck URLs"),
        (["interested for", "interest", "interested"], "Interested for", "interested details"),
        (["follow up count", "follow-up count", "number of follow ups"], "Follow-Up Count", "follow-up counts"),
        (["last follow up date", "last follow-up date"], "Last Follow-Up Date", "last follow-up dates"),
        (["reply status", "reply"], "Reply Status", "reply statuses"),
        (["linkedin headline", "headline"], "LINKEDIN-HEADLINE", "LinkedIn headlines"),
        (["linkedin reply"], "LINKEDIN-REPLY", "LinkedIn replies"),
        (["linkedin url", "linkedin link"], "LINKEDIN-URL", "LinkedIn URLs"),
        (["stand size", "booth size", "size"], "Stand Size", "stand sizes"),
        (["amount", "price", "cost", "payment"], "Amount", "amounts"),
        (["crm update"], "CRM Update", "CRM updates"),
        (["crm lead id", "lead id"], "CRM Lead ID", "CRM lead IDs"),
        (["eventbrite update", "eventbrite"], "Eventbrite Update", "Eventbrite updates"),
        (["exhibitor mis", "mis"], "Exhibitor MIS", "Exhibitor MIS statuses"),
        (["welcome email"], "Welcome Email", "welcome email statuses"),
        (["welcome message", "welcome msg"], "Welcome Msg", "welcome message statuses"),
        (["canva update", "canva"], "Canva Update", "Canva updates"),
        (["website update", "website"], "Website Update", "website updates"),
        (["social media post", "social media", "post"], "Social Media Post", "social media posts"),
        (["payment status"], "Payment Status", "payment statuses"),
        (["whatsapp permission", "whats app permission"], "Whatsapp_Permission", "WhatsApp permission statuses"),
        (["sms status", "text status", "sms"], "SMS_STATUS", "SMS statuses"),
        (["workflow identifier", "workflow id"], "Workflow-Identifier", "workflow identifiers"),
        (["every catch crm", "every-catch crm", "every catch"], "EVERY-CATCH CRM", "Every Catch CRM statuses")
    ]

    column_triggers = ["read the column", "list the column", "read all", "list all"]
    is_triggered = any(trigger in q for trigger in column_triggers) or "column" in q

    if is_triggered:
        # Sort mappings by keyword length in descending order to match specific phrases first
        sorted_mappings = sorted(mappings, key=lambda m: max(len(kw) for kw in m[0]), reverse=True)
        for keywords, col_key, label in sorted_mappings:
            for kw in keywords:
                if kw in q:
                    # Extract values for the matching column
                    values = []
                    for row in rows:
                        if col_key == "Name":
                            first = str(row.get("First_Name", "")).strip()
                            last = str(row.get("Last Name", "")).strip()
                            val = f"{first} {last}".strip()
                        else:
                            val = str(row.get(col_key, "")).strip()
                        
                        if val and val.lower() not in ["", "n/a", "none", "null", "not available"]:
                            values.append(val)
                    
                    if values:
                        return f"The {label} in the spreadsheet are: {format_list(values)}."
                    else:
                        return f"The {label} column in the spreadsheet is empty."

    # Fallback to Gemini if exact match fails
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        try:
            model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            
            context_data = json.dumps(rows)
            prompt = (
                f"You are Daisy, a helpful data assistant. Here is the spreadsheet data in JSON format:\n"
                f"{context_data}\n\n"
                f"User Question: {question}\n\n"
                f"Please answer the user's question concisely based ONLY on the provided data."
            )
            
            payload = {
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 180}
            }
            
            req = urllib.request.Request(
                url, 
                data=json.dumps(payload).encode('utf-8'), 
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                reply = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '').strip()
                if reply:
                    return reply
        except Exception as e:
            print(f"Gemini API error: {e}")
            pass

    return "I could not find that person or column in the spreadsheet."

@app.post("/ask")
def ask(request: QuestionRequest):
    try:
        rows = get_sheet_data()
        answer = find_answer(request.question, rows)
        return {"reply": answer}

    except Exception:
        traceback.print_exc()

        return {
            "reply": "Spreadsheet error. Please check the terminal."
        }

@app.get("/")
def home():
    return {"message": "Daisy backend is running"}