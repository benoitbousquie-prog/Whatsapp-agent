import os
import sqlite3
import resend
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import OpenAI

# ============================================================
# CONFIGURATION
# ============================================================

EMAIL_TO = "benoitbousquie@gmail.com"

# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
resend.api_key = os.getenv("RESEND_API_KEY")

# ============================================================
# DATABASE
# ============================================================

db = sqlite3.connect("whatsapp.db")

# ============================================================
# DATE RANGE
# ============================================================

since = (
    datetime.now() - timedelta(days=15)
).isoformat()

# ============================================================
# GROUPS
# ============================================================

with open("groups.txt", "r", encoding="utf-8") as f:
    groups = [
        line.strip()
        for line in f
        if line.strip()
    ]

# ============================================================
# COLLECT ALL MESSAGES
# ============================================================

all_conversations = ""

group_counts = {}

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

    group_counts[group_name] = len(rows)

    if not rows:
        continue

    all_conversations += (
        f"\n\n"
        f"====================================================\n"
        f"GROUP: {group_name}\n"
        f"====================================================\n"
    )

    for metadata, message, captured_at in rows:

        all_conversations += (
            f"{metadata} {message}\n"
        )

# ============================================================
# NO MESSAGES
# ============================================================

if not all_conversations.strip():

    print("No messages found in the last 15 days.")

    db.close()

    exit()

# ============================================================
# AI BRIEFING
# ============================================================

prompt = f"""
You are my personal assistant.

Create a concise, high-value briefing based on
WhatsApp messages from the last 15 days.

I am French-speaking, but the ENTIRE briefing
must be written in ENGLISH.

There are several WhatsApp groups.

Your goal is NOT to summarize everything.

Your goal is to tell me:

"What happened in the last 15 days that I
actually need to know or act upon?"

Prioritize:

- Actions Benoît needs to take
- Questions directed at Benoît
- Decisions involving Benoît
- Important dates
- Schedule changes
- Logistics
- Commitments
- Things Benoît promised to do
- Things Benoît needs to remember
- Important family or children's information
- Important sports / school information
- Any potentially urgent matter

Ignore:

- Greetings
- Jokes
- Casual conversation
- Emojis
- Reactions
- Repetitive messages
- Arguments or chatter that require no action
- Information that is clearly irrelevant

Translate important Spanish or French messages
into natural English.

IMPORTANT:

If several messages discuss the same topic,
combine them into one clear item.

Do not repeat information.

Do not invent information.

Do not assume Benoît needs to act unless the
messages actually indicate that he should.

Organize the briefing using exactly this structure:

# 🔴 ACTION REQUIRED

Things Benoît should actually do.

For each action, explain briefly:
- What?
- When?
- Why?

If there are none:
"No action required."

# 🟠 IMPORTANT TO KNOW

Information Benoît should be aware of.

# 🗓️ DATES & LOGISTICS

Important dates, times, locations,
schedule changes or practical information.

# 👨‍👩‍👧 FAMILY / SCHOOL / ACTIVITIES

Only if relevant information exists.

# 🌍 IMPORTANT TRANSLATIONS

Only translate messages where the original
Spanish or French wording contains information
that Benoît needs to understand.

# 🟢 NOTHING REQUIRES ATTENTION

Use this section only if appropriate.

# PRIORITY

Choose one:

🔴 URGENT
🟠 TO WATCH
🟢 NO ACTION

Then give a ONE-SENTENCE overall assessment.

Here are the WhatsApp messages:

{all_conversations}
"""

print("Generating 15-day briefing...")

response = client.responses.create(
    model="gpt-5.6",
    input=prompt
)

briefing = response.output_text

# ============================================================
# GROUP SUMMARY
# ============================================================

group_summary = ""

for group_name in groups:

    count = group_counts.get(
        group_name,
        0
    )

    group_summary += f"""
    <li>
    <strong>{group_name}</strong>
    — {count} messages
    </li>
    """

# ============================================================
# EMAIL
# ============================================================

html = f"""
<html>

<body style="font-family: Arial, sans-serif;">

<h1>📱 WhatsApp — 15-Day Briefing</h1>

<p>
<strong>Period:</strong>
Last 15 days
</p>

<h2>Groups monitored</h2>

<ul>
{group_summary}
</ul>

<hr>

<div style="
    white-space: pre-wrap;
    font-family: Arial, sans-serif;
    line-height: 1.5;
">

{briefing}

</div>

<hr>

<p style="color: gray;">
Generated automatically by WhatsApp Agent
</p>

</body>

</html>
"""

params = {
    "from": "onboarding@resend.dev",
    "to": [EMAIL_TO],
    "subject": "📱 WhatsApp — 15-Day Briefing",
    "html": html
}

print("Sending email...")

resend.Emails.send(params)

print()
print("=" * 60)
print("15-DAY BRIEFING SENT")
print("=" * 60)

db.close()
