import time
from typing import Any
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains


from rent_radar.scraping import paginate_search_results
from rent_radar.settings import settings

import logging

logger = logging.Logger(__name__)


def get_listing_summaries() -> list[dict[str, Any]]:
    driver = webdriver.Chrome()

    listings = []
    page_urls = paginate_search_results(settings.ZILLOW_BASE_URL, 20)

    for url in page_urls:
        page = driver.get(url)
        time.sleep(3)
        # look for human check
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
        # listing_card = driver.find_element(
        #     By.XPATH,
        #     "/html/body/div[1]/div/div[2]/div/div/div[1]/div[1]/ul/li[1]/div/div/article/div/div[1]",
        # )
        # logger.info(listing_card.text)

    driver.close()


get_listing_summaries()
