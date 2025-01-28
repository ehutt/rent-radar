import logging
import re
from datetime import date, datetime

import pandas as pd

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# FMR data columns
COLUMN_MAP = {
    1: "One-Bedroom",
    2: "Two-Bedroom",
    3: "Three-Bedroom",
    4: "Four-Bedroom",
}


def extract_numeric_price(price_str: str) -> float:
    """
    Convert text like '$2,500 ' into 2500.0
    """
    if not price_str:
        return 0.0
    cleaned = re.sub(r"[^\d\.]", "", price_str)
    return float(cleaned) if cleaned else 0.0


def can_determine_price_change(listing_history: dict, reference_date: date) -> bool:
    """
    Determine if it's even possible to measure a price change across `reference_date`.

    Conditions for True:
    1. At least two price events in `listing_history`.
    2. There is at least one event strictly before `reference_date`.
    3. There is at least one event strictly after `reference_date`.

    Otherwise returns False.
    """
    if not listing_history or len(listing_history) < 2:
        return False

    # Convert to list of (date_obj, price) and sort ascending
    events = []
    for date_str, data in listing_history.items():
        # parse 'YYYY-MM-DD'; handle partial date_str if needed
        dt = datetime.fromisoformat(date_str).date()
        price = data.get("price", None)
        if price is not None:
            events.append((dt, price))
    events.sort(key=lambda x: x[0])

    # If fewer than 2 valid (date, price) pairs remain, we can't compare anything
    if len(events) < 2:
        return False

    # Check if there's at least one event before the reference_date
    has_before = any(dt < reference_date for dt, price in events)
    # Check if there's at least one event after the reference_date
    has_after = any(dt > reference_date for dt, price in events)

    if not has_before or not has_after:
        return False

    return True


def exceeds_price_increase(
    listing_history: dict, reference_date: date, max_increase: float
) -> bool:
    """
    Given that we *can* determine a price change (checked via `can_determine_price_change`),
    find:
      - The 'latest' price (the event with the largest date overall).
      - The most recent price before the reference_date.
    Then see if the percentage increase is greater than max_increase.
    Returns True if exceeded, otherwise False.
    """
    # 1. Convert to list of (date_obj, price) tuples
    events = []
    for date_str, data in listing_history.items():
        dt = datetime.fromisoformat(date_str).date()
        price = data.get("price")
        if price is not None:
            events.append((dt, price))

    # 2. Sort by date ascending
    events.sort(key=lambda x: x[0])

    # 3. The "latest" price is the last in sorted order
    latest_dt, latest_price = events[-1]

    # 4. Find the most recent price before `reference_date`
    previous_price = None
    for dt, price in reversed(events):
        if dt < reference_date:
            previous_price = price
            break

    # Edge case guard (though `can_determine_price_change` should have filtered this out)
    if previous_price is None:
        return False

    # 5. Calculate percent increase
    if previous_price == 0:
        # Avoid division by zero
        return False

    price_diff = latest_price - previous_price
    percent_increase = price_diff / previous_price

    return percent_increase > max_increase


def exceeds_fmr_rate(listing: dict, fmr_rate: float, fmr_data: pd.DataFrame) -> bool:
    """
    Check if the current price of a listing exceeds the allowed percentage of the Fair Market Rent (FMR).
    Returns True if exceeded, otherwise False.
    """
    zip_code = listing.get("zipCode", None)
    price = listing.get("price", None)
    num_beds = listing.get("bedrooms", 1)
    if num_beds > 4:
        num_beds = 4  # FMR data only goes up to 4 bedrooms

    if zip_code is None or price is None:
        return False
    zip_code = int(zip_code)
    if zip_code not in fmr_data["ZIP Code"].values:
        logger.warning(f"ZIP code %s not found in FMR data", zip_code)
        return False
    fmr_price_str = fmr_data.loc[fmr_data["ZIP Code"] == zip_code][
        COLUMN_MAP[num_beds]
    ].values[0]
    fmr_price = extract_numeric_price(fmr_price_str)
    return price > (fmr_price * fmr_rate)
