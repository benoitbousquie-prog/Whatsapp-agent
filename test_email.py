import os
import resend
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")

params = {
    "from": "onboarding@resend.dev",
    "to": ["yourname@gmail.com"],
    "subject": "Test - WhatsApp Agent",
    "html": """
    <h2>WhatsApp Agent fonctionne !</h2>
    <p>Ceci est notre premier email automatique.</p>
    <p>La prochaine étape sera d'y envoyer le résumé de tes groupes WhatsApp.</p>
    """
}

email = resend.Emails.send(params)

print("Email envoyé !")
print(email)
