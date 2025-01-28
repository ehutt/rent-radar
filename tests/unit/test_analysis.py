from datetime import date

import pandas as pd
import pytest

from rent_radar.analysis import (
    can_determine_price_change,
    exceeds_fmr_rate,
    exceeds_price_increase,
    extract_numeric_price,
)


@pytest.mark.parametrize(
    "price_str, expected",
    [
        # Empty or None-like input
        ("", 0.0),
        (
            None,
            0.0,
        ),  # even though the function expects string, let's see how it behaves
        # Simple currency strings
        ("$2,500", 2500.0),
        ("$2,500.25", 2500.25),
        ("2500", 2500.0),
        ("  $3,100  ", 3100.0),  # with extra spaces
        # Mixed with non-digit characters
        ("$3,100 / month", 3100.0),
        ("Monthly rent: $3,200.99", 3200.99),
        # Non-numeric
        ("abc", 0.0),
        ("$$$,,,   ", 0.0),
    ],
)
def test_extract_numeric_price(price_str, expected):
    """
    Test extraction of numeric amounts from various currency-like strings.
    """
    result = extract_numeric_price(price_str)
    assert result == pytest.approx(
        expected
    ), f"For input '{price_str}', expected {expected} but got {result}"


@pytest.fixture
def fmr_data():
    """
    Provide a sample FMR DataFrame with ZIP Code plus columns for
    1,2,3,4-Bedroom. (strings that look like currency).
    """
    data = {
        "ZIP Code": [90064, 90065],
        "One-Bedroom": ["$2,000", "$2,100"],
        "Two-Bedroom": ["$2,500", "$2,600"],
        "Three-Bedroom": ["$3,000", "$3,100"],
        "Four-Bedroom": ["$3,500 ", "$3,600"],
    }
    return pd.DataFrame(data)


@pytest.mark.parametrize(
    "listing, fmr_rate, expected",
    [
        # 1) Missing zipCode => False
        ({"price": 2100, "bedrooms": 1}, 1.0, False),
        # 2) Missing price => False
        ({"zipCode": 90064, "bedrooms": 1}, 1.0, False),
        # 3) Exactly matches the FMR => not strictly greater => False
        ({"zipCode": 90064, "price": 2000, "bedrooms": 1}, 1.0, False),
        # 4) Price is just above the FMR => True
        ({"zipCode": 90064, "price": 2001, "bedrooms": 1}, 1.0, True),
        # 5) Two-Bedroom example, bigger difference
        (
            {"zipCode": 90064, "price": 3000, "bedrooms": 2},
            1.0,
            True,
        ),  # FMR=2500 => listing=3000 => True
        # 6) Listing has 5 bedrooms => fallback to 4 => $3,500 => 1.0 => 3500 => listing=3501 => True
        ({"zipCode": 90064, "price": 3501, "bedrooms": 5}, 1.0, True),
        # 7) Over FMR but with smaller rate => e.g., FMR=3500 => fmr_rate=0.9 => threshold=3150 => listing=3200 => True
        ({"zipCode": 90064, "price": 3200, "bedrooms": 4}, 0.9, True),
        # 8) Over FMR but with large rate => e.g., FMR=2000 => fmr_rate=1.5 => threshold=3000 => listing=2999 => False
        ({"zipCode": 90064, "price": 2999, "bedrooms": 1}, 1.5, False),
        # 9) Another zip in data => 90065 => One-Bedroom = $2100 => listing=2100 => not strictly greater => False
        ({"zipCode": 90065, "price": 2100, "bedrooms": 1}, 1.0, False),
        # 10) 90065 => One-Bedroom => $2100 => listing=2101 => strictly greater => True
        ({"zipCode": 90065, "price": 2101, "bedrooms": 1}, 1.0, True),
    ],
)
def test_exceeds_fmr_rate(listing, fmr_rate, expected, fmr_data):
    """
    Test whether a given listing's price exceeds the FMR * fmr_rate.
    Uses the fmr_data fixture as sample data for FMR amounts.
    """
    result = exceeds_fmr_rate(listing, fmr_rate, fmr_data)
    assert (
        result == expected
    ), f"For listing={listing}, fmr_rate={fmr_rate}, expected {expected} but got {result}"


@pytest.mark.parametrize(
    "listing_history, reference_date, expected",
    [
        # 1) Empty history => False
        ({}, date(2025, 1, 6), False),
        # 2) Only one event => False
        (
            {
                "2025-01-05": {"price": 2000},
            },
            date(2025, 1, 6),
            False,
        ),
        # 3) Two events, both BEFORE reference_date => cannot find a date AFTER => False
        (
            {
                "2024-01-10": {"price": 2100},
                "2024-05-15": {"price": 2500},
            },
            date(2025, 1, 6),
            False,
        ),
        # 4) Two events, both AFTER reference_date => cannot find a date BEFORE => False
        (
            {
                "2025-02-01": {"price": 2200},
                "2025-03-01": {"price": 2300},
            },
            date(2025, 1, 6),
            False,
        ),
        # 5) Exactly 2 events, one before and one after => True
        (
            {
                "2024-12-31": {"price": 2000},
                "2025-01-10": {"price": 2200},
            },
            date(2025, 1, 6),
            True,
        ),
        # 6) Three events, with some before and some after => True
        (
            {
                "2024-12-01": {"price": 1800},
                "2025-01-05": {"price": 2000},
                "2025-01-07": {"price": 2100},
            },
            date(2025, 1, 6),
            True,
        ),
        # 7) 2 valid events, but 1 has no "price" => effectively only 1 price => False
        (
            {
                "2025-01-05": {"price": 2000},
                "2025-01-10": {"some_other_key": 9999},  # no "price"
            },
            date(2025, 1, 6),
            False,
        ),
    ],
)
def test_can_determine_price_change(listing_history, reference_date, expected):
    """
    Test can_determine_price_change for a variety of scenarios:
    - No events
    - Only one event
    - Events all before or all after the reference date
    - At least 2 events on both sides of the reference date
    """
    result = can_determine_price_change(listing_history, reference_date)
    assert result == expected, (
        f"Expected {expected}, but got {result} for history={listing_history} "
        f"and reference_date={reference_date}"
    )


@pytest.mark.parametrize(
    "listing_history, reference_date, max_increase, expected",
    [
        # 1) Two events crossing reference_date, but no real difference => 0% => False
        (
            {
                "2024-12-31": {"price": 2000},
                "2025-01-07": {"price": 2000},
            },
            date(2025, 1, 6),
            0.10,
            False,
        ),
        # 2) Two events crossing reference_date => 10% => equals threshold => NOT exceeding => False
        (
            {
                "2024-12-31": {"price": 2000},
                "2025-01-07": {"price": 2200},  # 2000 -> 2200 = 10% increase
            },
            date(2025, 1, 6),
            0.10,
            False,  # must be strictly greater to return True
        ),
        # 3) Two events crossing reference_date => 11% => exceeding 10% => True
        (
            {
                "2024-12-31": {"price": 2000},
                "2025-01-07": {"price": 2220},  # 2000 -> 2220 = 11%
            },
            date(2025, 1, 6),
            0.10,
            True,
        ),
        # 4) Multiple events, the "most recent price before reference_date" is not the penultimate date
        #   e.g. last date: 1/14/2025 => price=22500
        #   a date after reference_date => 1/10/2025 => price=22000 (but 1/10 is after 1/6)
        #   an older date => 2/13/2023 => price=20000
        # => The "most recent price before reference_date=1/6/2025" is 2/13/2023 => 20000
        # => The difference is (22500 - 20000)/20000 = 12.5% => True
        (
            {
                "2023-02-13": {"price": 20000},
                "2025-01-10": {"price": 22000},  # This is after 1/6, so not "before"
                "2025-01-14": {"price": 22500},
            },
            date(2025, 1, 6),
            0.10,
            True,
        ),
        # 5) Price of 0 => Avoid division by zero => function returns False
        (
            {
                "2024-12-31": {"price": 0},
                "2025-01-07": {"price": 1000},
            },
            date(2025, 1, 6),
            0.10,
            False,
        ),
        # 6) If there's no event strictly before the reference date (but can_determine would be false),
        #   we might still test the function's behavior: it should return False.
        (
            {
                "2025-01-07": {"price": 2000},
                "2025-01-08": {"price": 2500},
            },
            date(2025, 1, 6),
            0.10,
            False,
        ),
    ],
)
def test_check_excessive_increase(
    listing_history, reference_date, max_increase, expected
):
    """
    Test exceeds_price_increase in scenarios where:
    - There's a small/large/0 difference across the reference date
    - Edge case of exactly threshold vs. over threshold
    - Price=0 scenario
    - Missing necessary date on one side => no 'previous_price' => return False
    """
    result = exceeds_price_increase(listing_history, reference_date, max_increase)
    assert result == expected, (
        f"For listing_history={listing_history}, reference_date={reference_date}, "
        f"max_increase={max_increase}, expected {expected} but got {result}"
    )
