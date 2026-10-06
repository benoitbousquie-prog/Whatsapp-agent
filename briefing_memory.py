import sqlite3

db = sqlite3.connect("whatsapp.db")

db.execute("""
CREATE TABLE IF NOT EXISTS briefing_state (
    group_name TEXT PRIMARY KEY,
    last_message_id INTEGER
)
""")

db.commit()

GROUP_NAME = "Benjamines Alevines TriCorrecas"

# Vérifier si le groupe existe déjà dans la mémoire
row = db.execute(
    """
    SELECT last_message_id
    FROM briefing_state
    WHERE group_name = ?
    """,
    (GROUP_NAME,)
).fetchone()

if row is None:
    print("Aucun briefing précédent enregistré.")
else:
    print("Dernier message traité :", row[0])

db.close()
