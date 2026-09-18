import logging
from abc import ABC, abstractmethod
from time import sleep
from typing import Optional

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import Browser

from config.config_dataclass import WebSettings #type:ignore

logger = logging.getLogger(__name__)

class AbstractWebScraper[T](ABC):
    """Abstract base class for all web-based scrapers."""

    def __init__(
        self,
        url: Optional[str] = None,
        web_settings: Optional[WebSettings] = None,
    ) -> None:
        self.url = url
        self.web_settings = web_settings or WebSettings()

        self.headers = {
            "User-Agent": self.web_settings.user_agent
        }

    @abstractmethod
    def scrape(self) -> list[T]:
        """Scrape data and return a list of structured entries."""
        pass

    def retrieve_soup(
        self,
        url: Optional[str] = None,
    ) -> BeautifulSoup | None:
        """Fetch HTML from a URL and return a BeautifulSoup object."""

        url = url or self.url

        if url is None:
            raise ValueError("No URL provided for web request.")

        if self.web_settings.polite_delay:
            sleep(self.web_settings.polite_delay)

        try:
            logger.info("Retrieving SOUP from: %s", url)

            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.web_settings.timeout,
            )

            if response.status_code == 200:
                logger.debug(
                    "Request successful: %s",
                    response.status_code,
                )
                return BeautifulSoup(response.text, "html.parser")

            logger.warning(
                "Request failed with status: %s",
                response.status_code,
            )
            return None

        except requests.exceptions.RequestException as e:
            logger.error(
                "Network error occurred while fetching %s: %s",
                url,
                e,
            )
            return None

    def retrieve_rendered_soup(
        self,
        browser: Browser,
        url: str,
    ) -> BeautifulSoup:
        """Fetch rendered HTML using a Playwright browser."""

        logger.info("Retrieving RENDERED SOUP from: %s", url)

        page = browser.new_page()

        try:
            page.goto(
                url,
                wait_until="load",
                timeout=int(self.web_settings.timeout * 1000),
            )
            return BeautifulSoup(
                page.content(),
                "html.parser",
            )
        finally:
            page.close()