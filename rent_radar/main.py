import logging

from rent_radar.analysis import export_flagged_to_csv, find_flagged_listings
from rent_radar.db import init_db, insert_price_history, upsert_listing
from rent_radar.scraping import scrape_listing_detail, scrape_listing_summaries

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")


def main():
    init_db()

    # 1. Scrape summary listings (ACTIVE rentals in LA County)
    listings_summaries = scrape_listing_summaries()

    # 2. For each listing, upsert in DB and get detail (price history)
    for summary in listings_summaries:
        listing_id = upsert_listing(summary)

        # If the listing has a detail URL, scrape price history
        if summary["listing_url"]:
            ph = scrape_listing_detail(summary["listing_url"])
            insert_price_history(listing_id, ph)

    # 3. Identify flagged listings
    flagged_listings = find_flagged_listings()
    if flagged_listings:
        export_flagged_to_csv(flagged_listings)
    else:
        logging.info(
            "No listings exceed the 10% price increase threshold since provided date"
        )


if __name__ == "__main__":
    main()
