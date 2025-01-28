import logging

import requests

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RentCastClient:
    """Client for calling the RentCast API."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json", "X-Api-Key": api_key}

    def get_listing_batch(
        self,
        city: str,
        offset: int = 0,
        state: str = "CA",
        limit: int = 500,
        status: str = "Active",
    ) -> list[dict]:
        """Get a batch of listings from the RentCast API with specified parameters."""
        logger.info(
            f"Getting listings for %s, %s, with offset %s...", city, state, offset
        )
        url = f"{self.base_url}city={city}&state={state}&status={status}&limit={limit}&offset={offset}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
