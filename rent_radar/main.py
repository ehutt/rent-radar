import datetime
import logging

import pandas as pd

from rent_radar.analysis import (can_determine_price_change, exceeds_fmr_rate,
                                 exceeds_price_increase)
from rent_radar.clients import RentCastClient
from rent_radar.db import RentCastDB
from rent_radar.settings import Settings

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = Settings()

CITIES = [
    "Los%20Angeles",
    "Santa%20Monica",
    "Beverly%20Hills",
    "Pasadena",
    "Glendale",
]  # todo add more cities


def main():
    db = RentCastDB(settings.database_file)
    client = RentCastClient(settings.rent_cast_base_url, settings.rent_cast_api_key)
    fmr_data = pd.read_csv(settings.fmr_data_file)  # FMR data for LA county
    cities_list = pd.read_csv(settings.city_names_file)[
        "City"
    ].values  # List of cities in LA county

    access_date = datetime.date.today().strftime("%Y-%m-%d")
    for city in cities_list:
        search_city(city, client, db, fmr_data, access_date)

    logger.info("Detected %d violations", db.get_entry_count("properties", "id"))
    db.close()
    logger.info("Process complete.")


def format_city_name(city_name: str) -> str:
    return city_name.replace(" ", "%20")


def search_city(
    city_name: str,
    client: RentCastClient,
    db: RentCastDB,
    fmr_data: pd.DataFrame,
    access_date: str,
):
    logger.info("Starting search for %s", city_name)
    offset = 0
    while True:
        # 1. Scrape summary listings (ACTIVE rentals in specified city)
        listings = client.get_listing_batch(
            city=format_city_name(city_name.strip()),
            state="CA",
            offset=offset,
            limit=500,
        )
        if (
            len(listings) < 500
        ):  # if less than 500 results, we've reached the end of the listings
            break
        offset += 1
        # 2. Check for price gouging violations
        for listing in listings:
            # Check if listing exceeds the FMR rate
            fmr_rate_violation = exceeds_fmr_rate(
                listing, settings.max_fmr_rate, fmr_data
            )
            if fmr_rate_violation:
                # If violation, save to database
                db.upsert_listing(
                    listing, violation_type="fmr_rate", date_updated=access_date
                )
            if can_determine_price_change(listing["history"], settings.reference_date):
                # Check if listing exceeds the price increase threshold
                price_violation = exceeds_price_increase(
                    listing["history"],
                    settings.reference_date,
                    settings.price_increase_threshold,
                )
                if price_violation:
                    # If violation, save to database
                    db.upsert_listing(
                        listing,
                        violation_type="price_increase",
                        date_updated=access_date,
                    )


if __name__ == "__main__":
    main()
