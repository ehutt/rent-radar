import json
import logging
import re
from typing import Any

import requests
from bs4 import BeautifulSoup

from rent_radar.settings import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")


def get_soup(url: str, headers: dict = {}) -> BeautifulSoup | None:
    """
    Send a GET request and return a BeautifulSoup object.
    """
    if headers is None:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36",
            "Referer": "https://www.zillow.com/",
            "Accept-Language": "en-US,en;q=0.9",
        }
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        logging.warning(f"Request to {url} returned status code {resp.status_code}")
        logging.warning(resp.text)
        return None
    return BeautifulSoup(resp.text, "html.parser")


def is_la_county_address(address: str) -> bool:
    """
    Very naive check if an address is within LA County.
    Realistically, you'd use a more robust approach:
      - Checking city names or zip codes known to be in LA County
      - Using a geocoding API
    """
    # Example: if "Los Angeles" or nearby city in address, or a known LA County zip range
    # This is purely illustrative; LA County has many cities and zip codes.
    la_related_keywords = [
        "Los Angeles",
        "Burbank",
        "Glendale",
        "Santa Monica",
        "Long Beach",
        "Inglewood",
        "Pasadena",
        "Torrance",
        "Palmdale",
        # ... add more LA County cities
    ]
    # Check if any city name is in the address
    address_lower = address.lower()
    for k in la_related_keywords:
        if k.lower() in address_lower:
            return True
    return False


def _extract_numeric_price(price_str: str) -> float:
    """
    Convert text like '$2,500/mo' into 2500.0
    """
    if not price_str:
        return 0.0
    cleaned = re.sub(r"[^\d\.]", "", price_str)
    return float(cleaned) if cleaned else 0.0


def paginate_search_results(base_url: str, max_pages: int = 20) -> list[str]:
    """
    Collect all result-page URLs up to `max_pages`.
    Zillow typically uses query parameters like '?searchQueryState=...&page=X'
    This is a conceptual approach; the actual logic depends on how Zillow's pagination is structured.
    """
    page_urls = []
    for page in range(1, max_pages + 1):
        # Example query param for pagination; real pagination may differ
        url = f"{base_url}{page}_p/"
        page_urls.append(url)
    return page_urls


# -------------------------
# Parsing Listing Summaries
# -------------------------


def scrape_listing_summaries() -> list[dict[str, Any]]:
    """
    Conceptually fetch all active rental listings in LA County across multiple pages.
    We'll parse summary info: listing URL, address, current price, etc.
    """
    # todo add check that number of extracted listings matches number of returned search results
    listings = []
    # todo add some kind of batching to avoid loading all listings in memory at once? or is it fine?
    page_urls = paginate_search_results(settings.ZILLOW_BASE_URL, max_pages=20)

    for url in page_urls:
        soup = get_soup(url)
        if not soup:
            continue
        listing_cards = soup.find_all(
            "li",
            {
                "class": "ListItem-c11n-8-107-0__sc-13rwu5a-0 StyledListCardWrapper-srp-8-107-0__sc-wtsrtn-0 dAZKuw xoFGK"
            },
        )

        for card in listing_cards:
            # extract initial list of properties from search results

            listing_data = json.loads(card.find("script").text)
            listing_fields = ["name", "url"]
            address_fields = [
                "streetAddress",
                "addressLocality",
                "addressRegion",
                "postalCode",
            ]
            # addresses are not always in the same format, so we need to check if the address is in the 'address' or 'location' key
            if "address" in listing_data.keys():
                address_data = {
                    k: listing_data["address"].get(k, None) for k in address_fields
                }
            elif "location" in listing_data.keys():
                address_data = {
                    k: listing_data["location"][1]["address"].get(k, None)
                    for k in address_fields
                }
            else:
                address_data = {k: None for k in address_fields}
            listing_data_to_keep = {
                k: listing_data.get(k, None) for k in listing_fields
            }
            listing_data_to_keep.update(address_data)
            listings.append(listing_data_to_keep)
    return listings


# -------------------------
# Price History Scraping
# -------------------------


def scrape_listing_detail(listing_url: str) -> list[dict[str, Any]]:
    """
    Visit the detail page for a single listing to extract detailed price history.
    Returns a list of dicts, each with `date` (YYYY-MM-DD) and `price`.

    Example:
    - "Price history" might show something like:
      - 01/19/2025: $11,900
      - 12/04/2024: $7,900
    """
    raise NotImplementedError
