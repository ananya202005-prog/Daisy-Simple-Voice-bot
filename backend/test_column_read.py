import sys
import os

# Ensure we can import from the backend directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import find_answer

MOCK_ROWS = [
    {
        "Assigned To": "Rahul",
        "Lead Date": "01-Jun-2026",
        "Lead Source": "LinkedIn",
        "First_Name": "Amit",
        "Last Name": "Sharma",
        "Company Name": "TechNova",
        "Mobile": "9876543210",
        "Email": "amit@technova.com",
        "Show": "Startup Expo 2026",
        "Next Followup": "05-Jun-2026",
        "Email-Count": "2",
        "Call Attempt": "1",
        "Linkedin Msg": "Yes",
        "WhatsApp msg count": "1",
        "Comments": "Interested in sponsorship",
        "Pitch Deck URL": "https://deck1.com",
        "Interested for": "Sponsorship",
        "Follow-Up Count": "2",
        "Last Follow-Up Date": "03-Jun-2026",
        "Reply Status": "Replied",
        "LINKEDIN-HEADLINE": "Founder at TechNova",
        "LINKEDIN-REPLY": "Interested",
        "LINKEDIN-URL": "linkedin.com/in/amit",
        "Stand Size": "3x3",
        "Amount": "50000",
        "CRM Update": "Updated",
        "CRM Lead ID": "CRM001",
        "Eventbrite Update": "Registered",
        "Exhibitor MIS": "Added",
        "Welcome Email": "Sent",
        "Welcome Msg": "Sent",
        "Canva Update": "Pending",
        "Website Update": "Pending",
        "Social Media Post": "Pending",
        "Payment Status": "Partial",
        "Whatsapp_Permission": "Yes",
        "SMS_STATUS": "Sent",
        "Workflow-Identifier": "WF001",
        "EVERY-CATCH CRM": "Active"
    },
    {
        "Assigned To": "Priya",
        "Lead Date": "02-Jun-2026",
        "Lead Source": "Website",
        "First_Name": "Neha",
        "Last Name": "Patel",
        "Company Name": "GreenTech",
        "Mobile": "9876543211",
        "Email": "neha@greentech.com",
        "Show": "Startup Expo 2026",
        "Next Followup": "06-Jun-2026",
        "Email-Count": "1",
        "Call Attempt": "2",
        "Linkedin Msg": "No",
        "WhatsApp msg count": "2",
        "Comments": "Wants brochure",
        "Pitch Deck URL": "https://deck2.com",
        "Interested for": "Booth",
        "Follow-Up Count": "1",
        "Last Follow-Up Date": "03-Jun-2026",
        "Reply Status": "Pending",
        "LINKEDIN-HEADLINE": "CEO at GreenTech",
        "LINKEDIN-REPLY": "Awaiting Response",
        "LINKEDIN-URL": "linkedin.com/in/neha",
        "Stand Size": "3x3",
        "Amount": "40000",
        "CRM Update": "Updated",
        "CRM Lead ID": "CRM002",
        "Eventbrite Update": "Registered",
        "Exhibitor MIS": "Added",
        "Welcome Email": "Sent",
        "Welcome Msg": "Sent",
        "Canva Update": "Done",
        "Website Update": "Pending",
        "Social Media Post": "Pending",
        "Payment Status": "Pending",
        "Whatsapp_Permission": "Yes",
        "SMS_STATUS": "Sent",
        "Workflow-Identifier": "WF002",
        "EVERY-CATCH CRM": "Active"
    }
]

def run_tests():
    print("Running voicebot parser tests with all headers...")
    
    test_cases = [
        # New Column reading cases
        ("read pitch deck urls", "The pitch deck URLs in the spreadsheet are: https://deck1.com and https://deck2.com."),
        ("tell me the stand size column", "The stand sizes in the spreadsheet are: 3x3 and 3x3."),
        ("what are the amounts", "The amounts in the spreadsheet are: 50000 and 40000."),
        ("what is in the payment status column", "The payment statuses in the spreadsheet are: Partial and Pending."),
        ("read welcome messages", "The welcome message statuses in the spreadsheet are: Sent and Sent."),
        
        # Single person summary check including new fields
        ("tell me about Amit Sharma", "Pitch Deck URL: https://deck1.com"),
        ("tell me about Amit Sharma", "Every Catch CRM: Active"),
        ("tell me about Amit Sharma", "Stand Size: 3x3"),
        ("tell me about Amit Sharma", "Payment Status: Partial"),
        
        # Single person specific field lookups
        ("what is the canva update for Neha?", "Neha Patel's Canva update status is Done."),
        ("tell me the every catch status of Amit Sharma", "Amit Sharma's Every Catch CRM status is Active."),
        ("give me information about Amit Sharma", "Here's what I know about Amit Sharma:")
    ]
    
    failed = False
    for query, expected in test_cases:
        res = find_answer(query, MOCK_ROWS)
        if expected in res:
            print(f"[PASS] Query: '{query}' -> Expected: '{expected}' in response.")
        else:
            print(f"[FAIL] Query: '{query}'\n  Expected substring: '{expected}'\n  Got: '{res}'")
            failed = True
            
    if failed:
        print("\nSome tests failed!")
        sys.exit(1)
    else:
        print("\nAll tests passed successfully!")

if __name__ == "__main__":
    run_tests()
