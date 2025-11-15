import sqlite3
import os

# Pfad zur Datenbankdatei
db_path = os.path.join(os.path.dirname(__file__), 'backend', 'parking.db')
email_to_delete = 'albert@gashis.ch'

if not os.path.exists(db_path):
    print(f"Fehler: Datenbankdatei nicht gefunden unter {db_path}")
    exit()

try:
    # Verbindung zur Datenbank herstellen
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Überprüfen, ob der Benutzer existiert
    cursor.execute("SELECT id FROM users WHERE email = ?", (email_to_delete,))
    user = cursor.fetchone()

    if user:
        # Benutzer löschen
        cursor.execute("DELETE FROM users WHERE email = ?", (email_to_delete,))
        conn.commit()
        print(f"Benutzer mit der E-Mail '{email_to_delete}' wurde erfolgreich gelöscht.")
    else:
        print(f"Benutzer mit der E-Mail '{email_to_delete}' wurde nicht in der Datenbank gefunden.")

except sqlite3.Error as e:
    print(f"Datenbankfehler: {e}")

finally:
    # Verbindung schliessen
    if 'conn' in locals() and conn:
        conn.close()
