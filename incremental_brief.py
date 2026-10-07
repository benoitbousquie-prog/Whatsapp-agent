import os
import sqlite3
import resend
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

GROUP_NAME = "Benjamines Alevines TriCorrecas"
EMAIL_TO = "yourname@gmail.com"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
resend.api_key = os.getenv("RESEND_API_KEY")

db = sqlite3.connect("whatsapp.db")

# Dernier message déjà inclus dans un briefing
row = db.execute(
    """
    SELECT last_message_id
    FROM briefing_state
    WHERE group_name = ?
    """,
    (GROUP_NAME,)
).fetchone()

last_id = row[0] if row else 0

# Nouveaux messages uniquement
rows = db.execute(
    """
    SELECT id, metadata, message
    FROM messages
    WHERE group_name = ?
    AND id > ?
    ORDER BY id ASC
    """,
    (GROUP_NAME, last_id)
).fetchall()

if not rows:
    print("Aucun nouveau message. Aucun email envoyé.")
    db.close()
    exit()

conversation = ""

for message_id, metadata, message in rows:
    conversation += f"{metadata} {message}\n"

prompt = f"""
Tu es mon assistant personnel chargé de surveiller mes groupes WhatsApp.

Je suis francophone.

Voici UNIQUEMENT les nouveaux messages reçus depuis mon dernier briefing
dans le groupe "{GROUP_NAME}":

--- DEBUT ---
{conversation}
--- FIN ---

Analyse ces messages et prépare un briefing très concis en français.

Utilise exactement cette structure :

🔴 À FAIRE
Les actions que Benoît doit faire.
S'il n'y en a aucune : "Aucune action."

🟠 IMPORTANT
Les informations que Benoît devrait connaître.

🌍 TRADUCTION
Traduis uniquement les messages importants en espagnol ou en anglais.

🟢 RIEN À FAIRE
Si les messages sont essentiellement du bavardage, indique-le brièvement.

Termine par :

PRIORITÉ : URGENT / À SURVEILLER / AUCUNE ACTION

Sois très concis et ne répète pas inutilement les messages.
"""

response = client.responses.create(
    model="gpt-5.6",
    input=prompt
)

summary = response.output_text

# Mise à jour de la mémoire
new_last_id = rows[-1][0]

db.execute(
    """
    INSERT OR REPLACE INTO briefing_state
    (group_name, last_message_id)
    VALUES (?, ?)
    """,
    (GROUP_NAME, new_last_id)
)

db.commit()
db.close()

# Email
html = f"""
<html>
<body>
<h2>WhatsApp Brief</h2>

<p><strong>Groupe :</strong> {GROUP_NAME}</p>

<hr>

<div style="font-family: Arial; white-space: pre-wrap;">
{summary}
</div>

<hr>

<p style="color:gray;">
Nouveaux messages analysés : {len(rows)}
</p>

</body>
</html>
"""

params = {
    "from": "onboarding@resend.dev",
    "to": [EMAIL_TO],
    "subject": f"WhatsApp Brief — {GROUP_NAME}",
    "html": html
}

resend.Emails.send(params)

print("\n======================================")
print("WHATSAPP BRIEF ENVOYÉ")
print("======================================")
print(summary)
print("--------------------------------------")
print(f"Nouveaux messages analysés : {len(rows)}")
print(f"Dernier ID traité : {new_last_id}")
