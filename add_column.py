from database import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE businesses ADD COLUMN next_followup_date DATETIME"))
        conn.commit()
        print("Added next_followup_date column successfully.")
    except Exception as e:
        print(f"Migration error (might already exist): {e}")
