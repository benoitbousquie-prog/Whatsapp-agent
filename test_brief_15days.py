import os
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import OpenAI

# ============================================================
# CONFIGURATION
# ============================================================

EMAIL_TO = "yourname@gmail.com"

# ============================================================
# ENVIRONNEMENT
# ============================================================

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ============================================================
# BASE DE DONNÉES
# ============================================================

db = sqlite3.connect("whatsapp.db")

# ============================================================
# DATE LIMITE
# ============================================================

since = (
    datetime.now() - timedelta(days=15)
).isoformat()

# ============================================================
# GROUPES
# ============================================================

with open("groups.txt", "r", encoding="utf-8") as f:
    groups = [
        line.strip()
        for line in f
        if line.strip()
    ]

# ============================================================
# RÉCUPÉRATION DES MESSAGES
# ============================================================

for group_name in groups:

    rows = db.execute(
        """
        SELECT metadata, message, captured_at
        FROM messages
        WHERE group_name = ?
        AND captured_at >= ?
        ORDER BY id ASC
        """,
        (
            group_name,
            since
        )
    ).fetchall()

    if not rows:
        print(
            f"\n{group_name}: "
            "no messages in the last 15 days"
        )
        continue

    conversation = ""

    for metadata, message, captured_at in rows:

        conversation += (
            f"{metadata} {message}\n"
        )

    print(
        f"\n{group_name}: "
        f"{len(rows)} messages"
    )

    # ========================================================
    # PROMPT
    # ========================================================

    prompt = f"""
You are my personal assistant.

Create a concise but useful briefing in ENGLISH
based on the WhatsApp messages from the last 15 days.

I am French-speaking, but the entire briefing
must be in English.

GROUP:
{group_name}

MESSAGES:
{conversation}

Your objective is NOT to summarize every message.

Identify what is genuinely relevant to me.

Focus on:

- Actions I need to take
- Questions directed at me
- Decisions involving me
- Important dates
- Schedule changes
- Logistics
- Commitments
- Important information
- Things I should follow up on

Ignore:

- Greetings
- Jokes
- Casual conversation
- Reactions
- Emojis
- Repetitive messages
- Irrelevant chatter

Translate relevant Spanish or French messages
into natural English.

Use exactly this structure:

🔴 ACTION REQUIRED

🟠 IMPORTANT

🗓️ DATES / LOGISTICS

🌍 TRANSLATION

🟢 NOTHING REQUIRES ATTENTION

PRIORITY:
URGENT / TO WATCH / NO ACTION

Be concise.

Do not invent information.
Do not assume Benoît needs to act unless
the messages actually indicate it.
"""

    response = client.responses.create(
        model="gpt-5.6",
        input=prompt
    )

    print("\n")
    print("=" * 70)
    print(group_name)
    print("=" * 70)
    print(response.output_text)

db.close()
