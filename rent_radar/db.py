import sqlite3
from typing import Any

from rent_radar.settings import settings


def init_db():
    """
    Initializes the SQLite database with a table for rental listings if it does not exist.
    """
    conn = sqlite3.connect(settings.DATABASE_FILE)
    c = conn.cursor()

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,             -- Zillow name
            source TEXT,           -- Zillow, Apartments, Redfin etc.
            streetAddress TEXT,
            addressLocality TEXT,
            postalCode TEXT,
            listing_url TEXT,
            landlord TEXT,
            parcel_id TEXT,             
            status TEXT,                  -- "ACTIVE" or "INACTIVE"
            last_scraped TEXT             -- track when we last scraped
        )
    """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER,
            date TEXT,
            price REAL,
            FOREIGN KEY (listing_id) REFERENCES listings (id)
        )
    """
    )

    conn.commit()
    conn.close()


def upsert_listing(listing_data: dict[str, Any]) -> int:
    """
    Insert or update the listing in the 'listings' table.
    Returns the listing's DB primary key (id).
    """
    raise NotImplementedError


def insert_price_history(listing_id: int, price_history: list[dict[str, Any]]):
    """
    Insert each entry in the price_history into the 'price_history' table, if not duplicate.
    """
    conn = sqlite3.connect(settings.DATABASE_FILE)
    c = conn.cursor()

    for record in price_history:
        # Check if we already have a record for this date for this listing
        c.execute(
            """
            SELECT id FROM price_history
            WHERE listing_id = ? AND date = ?
        """,
            (listing_id, record["date"]),
        )
        row = c.fetchone()

        if row:
            # We can optionally update the price if needed
            c.execute(
                """
                UPDATE price_history
                SET price = ?
                WHERE id = ?
            """,
                (record["price"], row[0]),
            )
        else:
            c.execute(
                """
                INSERT INTO price_history (listing_id, date, price)
                VALUES (?, ?, ?)
            """,
                (listing_id, record["date"], record["price"]),
            )

    conn.commit()
    conn.close()
