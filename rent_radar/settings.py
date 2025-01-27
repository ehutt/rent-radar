import datetime
from datetime import date

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_file: str = "listings.db"
    flagged_csv_file: str = "flagged_listings.csv"

    # Reference date for anti-gouging check
    reference_date: date = datetime.date(year=2025, month=1, day=6)
    price_increase_threshold: float = 0.10  # 10% by law

    # RentCast API
    rent_cast_api_key: str
    rent_cast_base_url: str = "https://api.rentcast.io/v1/listings/rental/long-term?"

    model_config = SettingsConfigDict(env_prefix="RENT_RADAR_", env_file=".env")
