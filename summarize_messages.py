import os
import sqlite3
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

GROUP_NAME = "Benjamines Alevines TriCorrecas"

db = sqlite3.connect("whatsapp.db")

rows = db.execute(
    """
    SELECT metadata, sender, message
    FROM messages
    WHERE group_name = ?
    ORDER BY id DESC
    LIMIT 20
    """,
    (GROUP_NAME,)
).fetchall()

db.close()

if not rows:
    print("Aucun message à analyser.")
    exit()

conversation = ""

for metadata, sender, message in reversed(rows):
    conversation += f"{metadata} {message}\n"

prompt = f"""
Tu es mon assistant personnel chargé de surveiller mes groupes WhatsApp.

Je suis francophone.

Voici une conversation WhatsApp récente :

--- DEBUT ---
{conversation}
--- FIN ---

Analyse-la et réponds en français.

Je veux exactement les sections suivantes :

1. RÉSUMÉ
Résume les principaux sujets en 3 à 5 points maximum.

2. À FAIRE
Indique uniquement les actions que Benoît doit éventuellement faire.
S'il n'y en a aucune, écris "Aucune action".

3. IMPORTANT
Indique les informations qui pourraient réellement intéresser Benoît.

4. TRADUCTION
Si des messages importants sont en espagnol ou en anglais,
traduis-les en français.
Ne traduis pas les messages sans importance.

5. PRIORITÉ
Choisis UNE seule priorité :
🔴 URGENT
🟠 À SURVEILLER
🟢 AUCUNE ACTION

Sois concis. Ne répète pas inutilement les messages.
"""

response = client.responses.create(
    model="gpt-5.6",
    input=prompt
)

print("\n" + "=" * 70)
print("WHATSAPP BRIEF — " + GROUP_NAME)
print("=" * 70)
print(response.output_text)
print("=" * 70)
