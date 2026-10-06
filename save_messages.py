import sqlite3
from datetime import datetime
from playwright.sync_api import sync_playwright

GROUP_NAME = "Benjamines Alevines TriCorrecas"

# Création de la base de données
db = sqlite3.connect("whatsapp.db")

db.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_name TEXT NOT NULL,
    metadata TEXT,
    sender TEXT,
    message TEXT,
    captured_at TEXT NOT NULL
)
""")

db.commit()

with sync_playwright() as p:

    context = p.chromium.launch_persistent_context(
        user_data_dir="./whatsapp_profile",
        headless=False
    )

    page = context.pages[0] if context.pages else context.new_page()

    page.goto("https://web.whatsapp.com/")
    page.wait_for_timeout(5000)

    chat = page.get_by_text(GROUP_NAME, exact=True)

    if chat.count() == 0:
        print("Groupe non trouvé.")
        input("Entrée pour fermer...")
        context.close()
        db.close()
        exit()

    chat.first.click()
    page.wait_for_timeout(3000)

    messages = page.locator('[data-pre-plain-text]')

    saved = 0

    for i in range(messages.count()):

        message = messages.nth(i)

        metadata = message.get_attribute("data-pre-plain-text")
        text = message.inner_text()

        # On évite de sauvegarder deux fois exactement le même message
        existing = db.execute(
            """
            SELECT id FROM messages
            WHERE group_name = ?
            AND metadata = ?
            AND message = ?
            """,
            (GROUP_NAME, metadata, text)
        ).fetchone()

        if existing:
            continue

        db.execute(
            """
            INSERT INTO messages
            (group_name, metadata, message, captured_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                GROUP_NAME,
                metadata,
                text,
                datetime.now().isoformat()
            )
        )

        saved += 1

    db.commit()

    print(f"\nMessages détectés : {messages.count()}")
    print(f"Nouveaux messages enregistrés : {saved}")

    input("\nAppuie sur Entrée pour fermer...")

    context.close()
    db.close()
