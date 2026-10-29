import os

from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from core.config import HEADLESS, PAGE_LOAD_TIMEOUT


# ============================================================
# CREATE CHROME DRIVER
# ============================================================

def create_driver():
    options = webdriver.ChromeOptions()

    if HEADLESS:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # (hiari) tumia Chrome/Chromium maalum
    chrome_binary = os.getenv("CHROME_BINARY")
    if chrome_binary:
        options.binary_location = chrome_binary

    # (hiari) chromedriver maalum; vinginevyo Selenium Manager inaipata yenyewe
    chromedriver = os.getenv("CHROMEDRIVER")
    service = Service(chromedriver) if chromedriver else Service()

    driver = webdriver.Chrome(options=options, service=service)
    # Ukurasa usiomaliza kuload ndani ya muda huu unaripotiwa kama error
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)

    if not HEADLESS:
        driver.maximize_window()

    return driver
