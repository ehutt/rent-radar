import pytest

from rent_radar.db import RentCastDB, flatten_dict, prepare_data_for_table


@pytest.fixture
def db():
    # Create an in-memory SQLite database for testing
    db = RentCastDB(":memory:")
    yield db
    db.close()


def test_init_tables(db):
    # Check if tables are created
    db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in db.cursor.fetchall()}
    assert "properties" in tables
    assert "history" in tables


def test_get_table_columns(db):
    columns = db._get_table_columns("properties")
    expected_columns = {
        "id",
        "violation_type",
        "date_updated",
        "formattedAddress",
        "addressLine1",
        "addressLine2",
        "city",
        "state",
        "zipCode",
        "county",
        "latitude",
        "longitude",
        "propertyType",
        "bedrooms",
        "bathrooms",
        "squareFootage",
        "lotSize",
        "yearBuilt",
        "status",
        "price",
        "listingType",
        "listedDate",
        "removedDate",
        "createdDate",
        "lastSeenDate",
        "daysOnMarket",
        "mlsName",
        "mlsNumber",
        "listingAgent_name",
        "listingAgent_phone",
        "listingAgent_email",
        "listingOffice_name",
        "listingOffice_phone",
    }
    assert columns == expected_columns


def test_upsert_listing(db):
    property_data = {
        "id": "1",
        "formattedAddress": "123 Main St",
        "city": "Anytown",
        "state": "CA",
        "history": {"2023-01-01": {"event": "listed", "price": 1000000}},
    }
    db.upsert_listing(property_data)
    db.cursor.execute("SELECT * FROM properties WHERE id='1';")
    property_row = db.cursor.fetchone()
    assert property_row is not None

    db.cursor.execute("SELECT * FROM history WHERE id='1' AND date='2023-01-01';")
    history_row = db.cursor.fetchone()
    assert history_row is not None


def test_get_entry_count(db):
    property_data = {
        "id": "1",
        "formattedAddress": "123 Main St",
        "city": "Anytown",
        "state": "CA",
    }
    db.upsert_listing(property_data)
    count = db.get_entry_count("properties", "id")
    assert count == 1


@pytest.mark.parametrize(
    "input_dict, exclude_keys, expected_output",
    [
        ({"a": {"b": 1, "c": 2}, "d": 3}, [], {"a_b": 1, "a_c": 2, "d": 3}),
        ({"a": {"b": 1, "c": 2}, "d": 3}, ["c"], {"a_b": 1, "d": 3}),
        ({}, [], {}),
        ({"a": 1, "b": 2}, [], {"a": 1, "b": 2}),
        (
            {"a": {"b": 1, "c": 2}, "d": 3, "e": {"f": 4, "g": 5}},
            ["c", "e"],
            {"a_b": 1, "d": 3},
        ),
    ],
)
def test_flatten_dict(input_dict, exclude_keys, expected_output):
    assert flatten_dict(input_dict, exclude_keys) == expected_output


@pytest.mark.parametrize(
    "data, table_columns, expected_output",
    [
        ({"a": 1, "b": 2, "c": 3}, ["a", "b"], {"a": 1, "b": 2}),
        ({"a": 1, "b": 2}, ["a", "b", "c"], {"a": 1, "b": 2, "c": None}),
        ({}, ["a", "b"], {"a": None, "b": None}),
        ({"a": 1, "b": 2}, [], {}),
        ({"a": 1, "b": 2, "c": 3}, ["d"], {"d": None}),
    ],
)
def test_prepare_data_for_table(data, table_columns, expected_output):
    assert prepare_data_for_table(data, table_columns) == expected_output
