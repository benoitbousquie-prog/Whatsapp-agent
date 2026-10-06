import os
import sqlite3
import resend
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from playwright.sync_api import sync_playwright

# ============================================================
# CONFIGURATION
# ============================================================

EMAIL_TO = "benoitbousquie@gmail.com"

# ============================================================
# ENVIRONNEMENT
# ============================================================

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
resend.api_key = os.getenv("RESEND_API_KEY")

# ============================================================
# GROUPES À SURVEILLER
# ============================================================

with open("groups.txt", "r", encoding="utf-8") as f:
    GROUPS = [
        line.strip()
        for line in f
        if line.strip()
    ]

print("Groups monitored:")

for group in GROUPS:
    print(" -", group)

# ============================================================
# BASE DE DONNÉES
# ============================================================

db = sqlite3.connect("whatsapp.db")

db.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_name TEXT NOT NULL,
    metadata TEXT,
    message TEXT,
    captured_at TEXT NOT NULL
)
""")

db.execute("""
CREATE TABLE IF NOT EXISTS briefing_state (
    group_name TEXT PRIMARY KEY,
    last_message_id INTEGER
)
""")

db.commit()

# ============================================================
# RÉCUPÉRATION DES MESSAGES WHATSAPP
# ============================================================

new_messages_by_group = {}

with sync_playwright() as p:

    context = p.chromium.launch_persistent_context(
        user_data_dir="./whatsapp_profile",
        headless=False
    )

    page = context.pages[0] if context.pages else context.new_page()

    page.goto("https://web.whatsapp.com/")

    page.wait_for_timeout(7000)

    for group_name in GROUPS:

        print("\n--------------------------------------")
        print("Group:", group_name)

        chat = page.get_by_text(
            group_name,
            exact=True
        )

        if chat.count() == 0:

            print("⚠️ Group not found")

            new_messages_by_group[group_name] = 0

            continue

        chat.first.click()

        page.wait_for_timeout(2500)

        messages = page.locator(
            '[data-pre-plain-text]'
        )

        new_messages = 0

        for i in range(messages.count()):

            message = messages.nth(i)

            metadata = message.get_attribute(
                "data-pre-plain-text"
            )

            text = message.inner_text()

            existing = db.execute(
                """
                SELECT id
                FROM messages
                WHERE group_name = ?
                AND metadata = ?
                AND message = ?
                """,
                (
                    group_name,
                    metadata,
                    text
                )
            ).fetchone()

            if existing:
                continue

            db.execute(
                """
                INSERT INTO messages
                (
                    group_name,
                    metadata,
                    message,
                    captured_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    group_name,
                    metadata,
                    text,
                    datetime.now().isoformat()
                )
            )

            new_messages += 1

        db.commit()

        new_messages_by_group[group_name] = new_messages

        print(
            "New messages:",
            new_messages
        )

    context.close()

# ============================================================
# ANALYSE DES NOUVEAUX MESSAGES
# ============================================================

briefs = []

for group_name in GROUPS:

    row = db.execute(
        """
        SELECT last_message_id
        FROM briefing_state
        WHERE group_name = ?
        """,
        (group_name,)
    ).fetchone()

    last_id = row[0] if row else 0

    rows = db.execute(
        """
        SELECT id, metadata, message
        FROM messages
        WHERE group_name = ?
        AND id > ?
        ORDER BY id ASC
        """,
        (
            group_name,
            last_id
        )
    ).fetchall()

    if not rows:
        continue

    conversation = ""

    for message_id, metadata, message in rows:

        conversation += (
            f"{metadata} {message}\n"
        )

    # ========================================================
    # AI PROMPT — ENGLISH BRIEFING
    # ========================================================

    prompt = f"""
You are my personal assistant responsible for monitoring
my WhatsApp groups.

I am French-speaking, but I want the entire briefing
to be written in ENGLISH.

Here are the new messages from the group:

GROUP:
{group_name}

--- START OF MESSAGES ---
{conversation}
--- END OF MESSAGES ---

Analyze only these new messages.

Your job is NOT simply to summarize everything.

Prioritize information that is actually relevant to me.

Identify:

1. Things I need to DO.
2. Things I need to KNOW.
3. Important dates, schedule changes, logistics,
   requests, decisions or commitments.
4. Messages where someone is directly asking me
   something or expecting an action from me.
5. Anything that could reasonably require my attention.

Ignore casual conversation, jokes, greetings,
reactions, congratulations, emojis and irrelevant
chatter unless they contain useful information.

If the messages are in Spanish or French,
translate the relevant information into natural English.

If the messages are already in English,
summarize them naturally without unnecessary translation.

Use exactly this structure:

🔴 ACTION REQUIRED
List only actions that Benoît needs to take.

If there are none:
"No action required."

🟠 IMPORTANT
Important information Benoît should know.

🗓️ DATES / LOGISTICS
Important dates, times, locations, schedule changes,
events or practical information.

🌍 TRANSLATION
Only include translations when they add value,
especially for important Spanish or French messages.

🟢 NOTHING REQUIRES ATTENTION
Use this section only if the conversation contains
mostly casual or irrelevant discussion.

PRIORITY:
URGENT / TO WATCH / NO ACTION

Be concise and practical.

Do not repeat the conversation.
Do not invent information.
Do not assume that Benoît needs to act unless the
messages actually indicate that he should.
"""

    response = client.responses.create(
        model="gpt-5.6",
        input=prompt
    )

    summary = response.output_text

    briefs.append(
        {
            "group": group_name,
            "summary": summary,
            "count": len(rows)
        }
    )

    # ========================================================
    # MÉMOIRE
    # ========================================================

    new_last_id = rows[-1][0]

    db.execute(
        """
        INSERT OR REPLACE INTO briefing_state
        (
            group_name,
            last_message_id
        )
        VALUES (?, ?)
        """,
        (
            group_name,
            new_last_id
        )
    )

    db.commit()

# ============================================================
# AUCUN NOUVEAU MESSAGE
# ============================================================

if not briefs:

    print("\n======================================")
    print("NO NEW MESSAGES")
    print("No email sent.")
    print("======================================")

    db.close()

    exit()

# ============================================================
# LISTE DES GROUPES
# ============================================================

group_status_html = ""

for group_name in GROUPS:

    matching_brief = next(
        (
            brief
            for brief in briefs
            if brief["group"] == group_name
        ),
        None
    )

    if matching_brief:

        count = matching_brief["count"]

        group_status_html += f"""
        <p>
        ✓ <strong>{group_name}</strong>
        — {count} new message(s)
        </p>
        """

    else:

        group_status_html += f"""
        <p>
        ○ <strong>{group_name}</strong>
        — no new messages
        </p>
        """

# ============================================================
# CONSTRUIRE LE BRIEFING
# ============================================================

html_sections = ""

plain_sections = ""

total_messages = 0

for brief in briefs:

    group = brief["group"]

    summary = brief["summary"]

    count = brief["count"]

    total_messages += count

    html_sections += f"""

    <h2>📱 {group}</h2>

    <p>
    <strong>New messages:</strong>
    {count}
    </p>

    <div style="
        font-family: Arial;
        white-space: pre-wrap;
        margin-bottom: 30px;
    ">
    {summary}
    </div>

    <hr>
    """

    plain_sections += f"""

====================================================
{group}
New messages: {count}
====================================================

{summary}

"""

# ============================================================
# EMAIL HTML
# ============================================================

html = f"""
<html>

<body>

<h1>📱 WhatsApp Brief</h1>

<p>

<strong>Groups monitored:</strong>
{len(GROUPS)}

<br>

<strong>Groups with activity:</strong>
{len(briefs)}

<br>

<strong>New messages:</strong>
{total_messages}

</p>

<hr>

<h2>📊 Group activity</h2>

{group_status_html}

<hr>

{html_sections}

<p style="color:gray;">
WhatsApp Agent — automatic briefing
</p>

</body>

</html>
"""

# ============================================================
# ENVOI EMAIL
# ============================================================

params = {

    "from": "onboarding@resend.dev",

    "to": [EMAIL_TO],

    "subject": "📱 WhatsApp Brief",

    "html": html
}

resend.Emails.send(params)

# ============================================================
# TERMINAL
# ============================================================

print("\n")

print("=" * 60)

print("WHATSAPP BRIEF SENT")

print("=" * 60)

print(
    f"Groups monitored: {len(GROUPS)}"
)

print(
    f"Groups with activity: {len(briefs)}"
)

print(
    f"Total new messages: {total_messages}"
)

print("=" * 60)

print(plain_sections)

print("=" * 60)

db.close()
