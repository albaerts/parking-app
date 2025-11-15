import os
import msal
import httpx
from dotenv import load_dotenv

load_dotenv()

AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
MAIL_FROM = os.getenv("MAIL_FROM")

# Treat literal "None" or empty strings as missing
def _is_missing(v: str) -> bool:
    return v is None or str(v).strip() == "" or str(v).strip().lower() == "none"

authority = None
app = None

if not _is_missing(AZURE_TENANT_ID) and not _is_missing(AZURE_CLIENT_ID) and not _is_missing(AZURE_CLIENT_SECRET):
    authority = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}"
    try:
        app = msal.ConfidentialClientApplication(
            client_id=AZURE_CLIENT_ID,
            authority=authority,
            client_credential=AZURE_CLIENT_SECRET,
        )
    except Exception as e:
        print(f"[graph_mailer] MSAL init skipped: {e}")
else:
    print("[graph_mailer] Missing Azure credentials; email sending disabled.")

def get_access_token():
    """Holt einen Access Token für die Microsoft Graph API oder None wenn nicht konfiguriert."""
    if not app:
        return None
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    if "access_token" not in result:
        raise Exception("Could not acquire token: " + result.get("error_description", "No error description"))
    return result["access_token"]

async def send_verification_email(recipient_email: str, verification_link: str):
    """
    Sendet eine Verifizierungs-E-Mail mit Microsoft Graph.
    """
    access_token = get_access_token()
    if access_token is None:
        print(f"[graph_mailer] Azure credentials missing; skipping real send. Would send to {recipient_email} link={verification_link}")
        return
    
    email_subject = "Verify Your Email for Gashis Parking"
    email_body = f"""
    <html>
        <body>
            <h2>Willkommen beim Gashis Parking System!</h2>
            <p>Bitte klicken Sie auf den folgenden Link, um Ihre E-Mail-Adresse zu verifizieren:</p>
            <p><a href="{verification_link}">E-Mail verifizieren</a></p>
            <p>Oder kopieren Sie diesen Link in Ihren Browser:</p>
            <p>{verification_link}</p>
            <p>Dieser Link ist 1 Stunde gültig.</p>
        </body>
    </html>
    """

    email_message = {
        "message": {
            "subject": email_subject,
            "body": {
                "contentType": "HTML",
                "content": email_body
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": recipient_email
                    }
                }
            ]
        },
        "saveToSentItems": "true"
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://graph.microsoft.com/v1.0/users/{MAIL_FROM}/sendMail",
            json=email_message,
            headers=headers
        )
        response.raise_for_status()
        print(f"Verification email sent to {recipient_email}")

