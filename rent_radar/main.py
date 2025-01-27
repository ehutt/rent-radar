import logging

from rent_radar.analysis import export_flagged_to_csv, find_flagged_listings
from rent_radar.clients import RentCastClient
from rent_radar.db import Database
from rent_radar.scraping import scrape_listing_detail, scrape_listing_summaries
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
    db = Database(settings.database_file)
    client = RentCastClient(settings.rent_cast_base_url, settings.rent_cast_api_key)

    # 1. Scrape summary listings (ACTIVE rentals in specified city) and add to DB
    test_city = "Los%20Angeles"  # todo add logic to loop through cities
    # todo add logic to get all results by incrementing offset - this just gets the first batch of 500 results
    listings = client.get_listing_batch(city=test_city, state="CA", offset=0, limit=500)
    db.upsert_batch(listings)

    # 2. Identify flagged listings
    # flagged_listings = find_flagged_listings()
    # if flagged_listings:
    #     export_flagged_to_csv(flagged_listings)
    # else:
    #     logging.info(
    #         "No listings exceed the 10% price increase threshold since provided date"
    #     )

    db.close()
    logger.info("Process complete.")


if __name__ == "__main__":
    main()
