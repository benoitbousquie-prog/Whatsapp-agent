import os
import sqlite3
import resend
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# -------------------------
# Configuration
# -------------------------

GROUP_NAME = "Benjamines Alevines TriCorrecas"
EMAIL_TO = "benoitbousquie@gmail.com"

# -------------------------
# Connexion aux services
# -------------------------

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

resend.api_key = os.getenv("RESEND_API_KEY")

# -------------------------
# Récupération des messages
# -------------------------

db = sqlite3.connect("whatsapp.db")

rows = db.execute(
    """
    SELECT metadata, message
    FROM messages
    WHERE group_name = ?
    ORDER BY id DESC
    LIMIT 30
    """,
    (GROUP_NAME,)
).fetchall()

db.close()

if not rows:
    print("Aucun message à analyser.")
    exit()

conversation = ""

for metadata, message in reversed(rows):
    conversation += f"{metadata} {message}\n"

# -------------------------
# Analyse par l'IA
# -------------------------

prompt = f"""
Tu es mon assistant personnel chargé de surveiller mes groupes WhatsApp.

Je suis francophone.

Voici les messages récents du groupe :

--- DEBUT ---
{conversation}
--- FIN ---

Analyse cette conversation et prépare un briefing très concis en français.

Utilise exactement cette structure :

🔴 À FAIRE
Les actions que Benoît doit faire.
S'il n'y en a aucune : "Aucune action."

🟠 IMPORTANT
Les informations que Benoît devrait connaître.

🌍 TRADUCTION
Traduis uniquement les messages importants qui sont en espagnol ou en anglais.

🟢 RIEN À FAIRE
Indique brièvement si la conversation est essentiellement du bavardage.

Termine par :

PRIORITÉ : URGENT / À SURVEILLER / AUCUNE ACTION

Ne répète pas inutilement les messages.
"""

response = client.responses.create(
    model="gpt-5.6",
    input=prompt
)

summary = response.output_text

# -------------------------
# Création de l'email HTML
# -------------------------

html = f"""
<html>
<body>
<h2>WhatsApp Brief</h2>

<p><strong>Groupe :</strong> {GROUP_NAME}</p>

<hr>

<pre style="font-family: Arial; white-space: pre-wrap;">
{summary}
</pre>

<hr>

<p style="color:gray;">
Brief généré automatiquement par ton WhatsApp Agent.
</p>

</body>
</html>
"""

# -------------------------
# Envoi de l'email
# -------------------------

params = {
    "from": "onboarding@resend.dev",
    "to": [EMAIL_TO],
    "subject": f"WhatsApp Brief — {GROUP_NAME}",
    "html": html
}

email = resend.Emails.send(params)

print("======================================")
print("WHATSAPP BRIEF ENVOYÉ")
print("======================================")
print(summary)
print("--------------------------------------")
print("Email envoyé à :", EMAIL_TO)
