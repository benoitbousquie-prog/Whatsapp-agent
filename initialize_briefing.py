import sqlite3

GROUP_NAME = "Benjamines Alevines TriCorrecas"

db = sqlite3.connect("whatsapp.db")

row = db.execute(
    """
    SELECT MAX(id)
    FROM messages
    WHERE group_name = ?
    """,
    (GROUP_NAME,)
).fetchone()

last_message_id = row[0]

db.execute(
    """
    INSERT OR REPLACE INTO briefing_state
    (group_name, last_message_id)
    VALUES (?, ?)
    """,
    (GROUP_NAME, last_message_id)
)

db.commit()
db.close()

print("Mémoire initialisée.")
print("Dernier message traité :", last_message_id)
