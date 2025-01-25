import datetime

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_FILE: str = "rental_listings.db"
    FLAGGED_CSV_FILE: str = "flagged_listings.csv"

    # Reference date for anti-gouging check
    REFERENCE_DATE: datetime.date = datetime.date(year=2025, month=1, day=6)
    PRICE_INCREASE_THRESHOLD: float = 0.10  # 10% by law

    # Zillow rental search for Los Angeles County (has ~40k results)
    ZILLOW_BASE_URL: str = (
        "https://www.zillow.com/homes/for_rent/Los-Angeles-County-CA/"
    )


settings = Settings()
