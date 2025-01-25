import logging
import time
from typing import Any

from click import option
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

from rent_radar.scraping import paginate_search_results
from rent_radar.settings import settings

logger = logging.Logger(__name__)


def get_listing_summaries() -> list[dict[str, Any]]:
    options = Options()
    ua = UserAgent()
    user_agent = ua.random
    print(user_agent)
    options.add_argument(f"user-agent={user_agent}")
    driver = webdriver.Chrome(options=options)

    listings = []
    page_urls = paginate_search_results(settings.ZILLOW_BASE_URL, 20)

    for url in page_urls:
        page = driver.get(url)
        time.sleep(3)
        # look for human check and handle if it exists
        button = driver.find_element(By.XPATH, "//*[contains(text(), 'Hold')]")
        if button:
            waiting = True
            while waiting:
                if button.is_displayed():
                    waiting = False
            # driver.implicitly_wait(10)
            ActionChains(driver).move_to_element(button).click_and_hold(
                button
            ).perform()
        listing_cards = driver.find_elements(
            By.CLASS_NAME,
            "div.StyledPropertyCardDataWrapper-c11n-8-107-0__sc-hfbvv9-0.cdQcZn.property-card-data",
        )
        logger.info(listing_cards)

    driver.close()


get_listing_summaries()
