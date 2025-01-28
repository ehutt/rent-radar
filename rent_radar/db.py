import logging
import sqlite3
from typing import Any

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def flatten_dict(d: dict[str:Any], exclude_keys: list[str], parent_key="", sep="_"):
    """Recursively flatten a dictionary, excluding keys in exclude_keys."""
    items = []
    for k, v in d.items():
        if k in exclude_keys:
            continue
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, exclude_keys, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def prepare_data_for_table(data, table_columns):
    """Filter and align data to match table columns."""
    return {key: data.get(key, None) for key in table_columns}


class RentCastDB:
    def __init__(self, database_file: str):
        """Initializes the SQLite database connection and creates the necessary tables if they do not exist."""
        self.database_file = database_file
        self.conn = sqlite3.connect(database_file)
        self.cursor = self.conn.cursor()
        self._init_tables()

    def _init_tables(self):
        """Create tables for properties and their price histories if they do not exist."""

        # Create the properties table
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS properties (
            id TEXT PRIMARY KEY,
            violation_type TEXT,
            date_updated TEXT,
            formattedAddress TEXT, 
            addressLine1 TEXT, 
            addressLine2 TEXT, 
            city TEXT, 
            state TEXT, 
            zipCode TEXT, 
            county TEXT, 
            latitude REAL, 
            longitude REAL, 
            propertyType TEXT, 
            bedrooms INTEGER, 
            bathrooms INTEGER, 
            squareFootage REAL, 
            lotSize REAL, 
            yearBuilt INTEGER, 
            status TEXT, 
            price REAL, 
            listingType TEXT, 
            listedDate TEXT, 
            removedDate TEXT, 
            createdDate TEXT, 
            lastSeenDate TEXT, 
            daysOnMarket INTEGER, 
            mlsName TEXT, 
            mlsNumber TEXT, 
            listingAgent_name TEXT, 
            listingAgent_phone TEXT, 
            listingAgent_email TEXT, 
            listingOffice_name TEXT, 
            listingOffice_phone TEXT
            )
        """
        )

        # Create the history table
        create_history_table_query = """
        CREATE TABLE IF NOT EXISTS history (
            id TEXT,
            date TEXT,
            event TEXT,
            price REAL,
            listingType TEXT,
            listedDate TEXT,
            removedDate TEXT,
            daysOnMarket INTEGER,
            PRIMARY KEY (id, date)
        )
        """
        self.cursor.execute(create_history_table_query)

    def _get_table_columns(self, table_name):
        """Fetch the column names of a table."""
        self.cursor.execute(f"PRAGMA table_info({table_name})")
        return {row[1] for row in self.cursor.fetchall()}  # row[1] is the column name

    def _add_missing_columns(self, table_name, data_columns):
        """Add missing columns to a table."""
        existing_columns = self._get_table_columns(table_name)
        missing_columns = data_columns - existing_columns

        for column in missing_columns:
            # Assume all new columns are TEXT (you can customize this if needed)
            self.cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column} TEXT")

    def get_entry_count(self, table_name, unique_column):
        """Get the count of unique entries in the specified table."""

        try:
            query = f"SELECT COUNT(DISTINCT {unique_column}) AS unique_entries FROM {table_name};"
            self.cursor.execute(query)
            result = self.cursor.fetchone()
            return result[0]  # Return the count
        except sqlite3.OperationalError as e:
            logging.exception(e)

    def upsert_listing(
        self,
        property_data: dict[str, Any],
        violation_type: str = "",
        date_updated: str = "",
    ) -> None:
        """
        Insert or update the property data.
        """
        # Flatten the dictionary excluding 'history'
        main_table_data = flatten_dict(property_data, exclude_keys=["history"])
        main_table_data.update(
            {"violation_type": violation_type, "date_updated": date_updated}
        )

        # Upsert into `properties` table
        self._upsert_one("properties", main_table_data)

        # Upsert history into `history` table
        history_data = property_data.get("history", {})
        for date, details in history_data.items():
            history_record = {"id": property_data["id"], "date": date, **details}
            self._upsert_one("history", history_record)
        self.conn.commit()

    def _upsert_one(self, table_name, data):
        data_columns = set(data.keys())

        # Add missing columns to the table
        self._add_missing_columns(table_name, data_columns)

        # Align data to the table schema
        prepared_data = prepare_data_for_table(
            data, self._get_table_columns(table_name)
        )

        # Build the upsert query dynamically
        columns = ", ".join(prepared_data.keys())
        placeholders = ", ".join(["?" for _ in prepared_data])
        if table_name == "history":
            update_clause = ", ".join(
                [
                    f"{col} = EXCLUDED.{col}"
                    for col in prepared_data.keys()
                    if col not in ["id", "date"]
                ]
            )
            upsert_query = f"""
                INSERT INTO {table_name} ({columns})
                VALUES ({placeholders})
                ON CONFLICT(id, date) DO UPDATE SET {update_clause}
            """
        else:
            update_clause = ", ".join(
                [f"{col} = EXCLUDED.{col}" for col in prepared_data.keys()]
            )
            upsert_query = f"""
                INSERT INTO {table_name} ({columns})
                VALUES ({placeholders})
                ON CONFLICT(id) DO UPDATE SET {update_clause}
            """
        self.cursor.execute(upsert_query, tuple(prepared_data.values()))

    def _upsert_many(self, table_name, batch):
        data_columns = set(batch[0].keys())
        for data in batch:
            data_columns.update(data.keys())
        self._add_missing_columns(table_name, data_columns)
        prepared_batch = [
            prepare_data_for_table(data, self._get_table_columns(table_name))
            for data in batch
        ]
        columns = ", ".join(data_columns)
        placeholders = ", ".join(["?" for _ in prepared_batch[0]])
        if table_name == "history":
            update_clause = ", ".join(
                [
                    f"{col} = EXCLUDED.{col}"
                    for col in prepared_batch[0].keys()
                    if col not in ["id", "date"]
                ]
            )
            upsert_query = f"""
                INSERT INTO {table_name} ({columns})
                VALUES ({placeholders})
                ON CONFLICT(id, date) DO UPDATE SET {update_clause}
            """
        else:
            update_clause = ", ".join(
                [f"{col} = EXCLUDED.{col}" for col in prepared_batch[0].keys()]
            )
            upsert_query = f"""
                INSERT INTO {table_name} ({columns})
                VALUES ({placeholders})
                ON CONFLICT(id) DO UPDATE SET {update_clause}
            """
        self.cursor.executemany(
            upsert_query, [tuple(d.values()) for d in prepared_batch]
        )
        self.conn.commit()

    def upsert_batch(self, batch: list[dict]):
        # Flatten and split the batch data
        property_data = []
        history_data = []
        for data in batch:
            flattened_data = flatten_dict(data, exclude_keys=["history"])
            property_data.append(flattened_data)
            for date, details in data.get("history", {}).items():
                history_data.append({"id": data["id"], "date": date, **details})
        # Upsert properties in a single query
        if property_data:
            self._upsert_many("properties", property_data)

        # Upsert history in a single query
        if history_data:
            self._upsert_many("history", history_data)

        # Commit after processing the batch
        self.conn.commit()

    def close(self):
        """Closes the database connection."""
        self.conn.close()
