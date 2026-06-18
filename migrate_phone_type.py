"""Add phone_type column to businesses and backfill it for existing rows.
Safe to run multiple times."""
from database import engine, SessionLocal
from sqlalchemy import text
from services.phone_utils import classify_phone

# 1) Add the column if it doesn't already exist
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE businesses ADD COLUMN phone_type VARCHAR(20) DEFAULT 'unknown'"))
        conn.commit()
        print("Added phone_type column.")
    except Exception as e:
        print(f"Column add skipped (likely already exists): {e}")

# 2) Backfill existing rows from their stored phone numbers
db = SessionLocal()
try:
    rows = db.execute(text("SELECT id, phone FROM businesses")).fetchall()
    updated = 0
    for row_id, phone in rows:
        ptype = classify_phone(phone)
        db.execute(
            text("UPDATE businesses SET phone_type = :pt WHERE id = :id"),
            {"pt": ptype, "id": row_id},
        )
        updated += 1
    db.commit()

    # Report a quick summary so you can see how many of your leads are landlines
    summary = db.execute(
        text("SELECT phone_type, COUNT(*) FROM businesses GROUP BY phone_type")
    ).fetchall()
    print(f"Backfilled {updated} rows.")
    print("Breakdown:", {pt: count for pt, count in summary})
finally:
    db.close()
