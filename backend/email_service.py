"""
Email Service mit Provider-Auswahl
Standard: Microsoft Graph (Client Credentials)
Optional: SMTP (z. B. Microsoft 365 SMTP AUTH)
"""
import os
from typing import Optional
import requests

PROVIDER = os.getenv("EMAIL_PROVIDER", "graph").lower()  # "graph", "smtp" oder "console"


class GraphEmailService:
    def __init__(self):
        import msal  # lazy import, nur wenn Provider genutzt wird
        self._msal = msal
        self.client_id = os.getenv("AZURE_CLIENT_ID")
        self.client_secret = os.getenv("AZURE_CLIENT_SECRET")
        self.tenant_id = os.getenv("AZURE_TENANT_ID")
        self.mail_from = os.getenv("MAIL_FROM", "parking@gashis.ch")

        if not all([self.client_id, self.client_secret, self.tenant_id, self.mail_from]):
            raise ValueError("Azure Graph credentials missing (AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID, MAIL_FROM)")

    def _get_access_token(self) -> str:
        authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        app = self._msal.ConfidentialClientApplication(
            self.client_id,
            authority=authority,
            client_credential=self.client_secret,
        )
        result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        if "access_token" in result:
            return result["access_token"]
        else:
            raise Exception(f"Could not acquire token: {result.get('error_description')}")

    def send_email(self, to_email: str, subject: str, html_body: str, from_name: Optional[str] = "Parking System") -> bool:
        token = self._get_access_token()
        email_msg = {
            "message": {
                "subject": subject,
                "body": {"contentType": "HTML", "content": html_body},
                "toRecipients": [{"emailAddress": {"address": to_email}}],
                "from": {"emailAddress": {"address": self.mail_from, "name": from_name}},
            },
            "saveToSentItems": "true",
        }
        graph_url = f"https://graph.microsoft.com/v1.0/users/{self.mail_from}/sendMail"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        response = requests.post(graph_url, headers=headers, json=email_msg)
        if response.status_code == 202:
            print(f"✅ Email sent successfully to {to_email}")
            return True
        else:
            raise Exception(f"Graph API error: {response.status_code} - {response.text}")


class SmtpEmailService:
    def __init__(self):
        # Minimal SMTP-Konfiguration (TLS oder STARTTLS)
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.mail_from = os.getenv("MAIL_FROM", self.smtp_user or "parking@gashis.ch")
        self.use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")

        if not all([self.smtp_host, self.smtp_user, self.smtp_password]):
            raise ValueError("SMTP settings missing (SMTP_HOST, SMTP_USER, SMTP_PASSWORD)")

    def send_email(self, to_email: str, subject: str, html_body: str, from_name: Optional[str] = "Parking System") -> bool:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{from_name} <{self.mail_from}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html", _charset="utf-8"))

        if self.use_tls and self.smtp_port == 465:
            # SMTPS (implicit TLS)
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.mail_from, [to_email], msg.as_string())
        else:
            # STARTTLS (587)
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.mail_from, [to_email], msg.as_string())

        print(f"✅ SMTP Email sent successfully to {to_email}")
        return True


# Singleton-Instanz
_email_service = None


def get_email_service():
    """Gibt den E-Mail-Service (Graph, SMTP oder Console) zurück, gesteuert via EMAIL_PROVIDER."""
    global _email_service
    if _email_service is None:
        if PROVIDER == "smtp":
            _email_service = SmtpEmailService()
        elif PROVIDER == "console":
            class ConsoleEmailService:
                def send_email(self, to_email: str, subject: str, html_body: str, from_name: Optional[str] = "Parking System") -> bool:
                    print("================ EMAIL (console) ================")
                    print(f"From: {from_name}")
                    print(f"To:   {to_email}")
                    print(f"Subj: {subject}")
                    print("Body:")
                    print(html_body)
                    print("=================================================")
                    return True
            _email_service = ConsoleEmailService()
        else:
            _email_service = GraphEmailService()
    return _email_service
