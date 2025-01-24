from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_FILE = 'rental_listings.db'
    FLAGGED_CSV_FILE = 'flagged_listings.csv'

    # Reference date for anti-gouging check
    REFERENCE_DATE = datetime.date(2025, 1, 6)
    PRICE_INCREASE_THRESHOLD = 0.10  # 10% by law

    # Zillow rental search for Los Angeles County (has ~40k results)
    ZILLOW_BASE_URL = 'https://www.zillow.com/homes/for_rent/Los-Angeles-County-CA/'

