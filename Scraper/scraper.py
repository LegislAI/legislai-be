#!/usr/bin/env python

import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    NoSuchElementException,
)
from chromedriver_py import binary_path
import logging
from time import sleep
import json

import argparse
import re
import datetime
from datetime import date, timedelta
import copy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("scraper_log.log"), logging.StreamHandler()],
)
LOG = logging.getLogger(__name__)


class DailyScraper:
    def __init__(
        self,
        URL: str = "https://diariodarepublica.pt/dr",
        PATH: str = "data",
        theme: str = None,
    ):
        # Prepare a folder to store the jsons
        if not os.path.exists(PATH):
            os.mkdir(PATH)

        self.scrape_page(URL, PATH, theme)

    def scrape_page(
        self,
        URL: str = "https://diariodarepublica.pt/dr",
        PATH: str = "data",
        theme: str = None,
    ):
        try:
            # Initialize the Chrome WebDriver
            driver = webdriver.Chrome()

            # Navigate to the CVE website
            driver.get(URL)

            # Wait for the page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "content"))
            )

            sleep(1)

            valid_articles_xpath = "//div[@class='int-links' and not(preceding-sibling::div[1][contains(@class, 'tabttitulo')])]"
            # Pega em todos os artigos válidos com o XPath
            articles = driver.find_elements(By.XPATH, valid_articles_xpath)
            for article in articles:
                if article.text != "":
                    link = article.find_element(By.TAG_NAME, "a").get_attribute("href")
                    logging.info(f"Processando link válido: {link}")
                    # just switch pages and then go back to the original page
                    driver.get(link)
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "b3-Conteudo"))
                    )
                    sleep(1)
                    date_container = driver.find_element(By.ID, "b7-DataPublicacao2")
                    date = date_container.find_elements(By.TAG_NAME, "span")[1].text

                    publicacao_type_div = driver.find_element(By.ID, "b7-Publicacao2")
                    publicacao_type = publicacao_type_div.find_elements(
                        By.TAG_NAME, "span"
                    )[1].text

                    publicacao_emissor_div = driver.find_element(By.ID, "b7-Emissor2")
                    publicacao_emissor = publicacao_emissor_div.find_elements(
                        By.TAG_NAME, "span"
                    )[1].text

                    article_name = driver.find_element(By.CLASS_NAME, "heading1").text

                    articleContent = driver.find_elements(By.TAG_NAME, "p")
                    article = "".join(
                        [
                            p.text.encode("utf-8").decode("utf-8") + "\n"
                            for p in articleContent
                        ]
                    )

                    payload = {
                        "article_title": article_name,
                        "publication_type": publicacao_type,
                        "publisher": publicacao_emissor,
                        "article_content": article,
                        "link": link,
                        "date": date,
                        "theme": theme,
                    }
                    # Lets replace the special characters
                    # Use utf8 formatting instead of the replace method
                    file_name = article_name.replace(" ", "_").replace("/", "_")
                    file_name.encode("utf-8").decode("utf-8")

                    payload = json.dumps(payload, ensure_ascii=False)

                    with open(f"{PATH}/{file_name}.json", "w") as f:
                        f.write(payload)

                    driver.back()
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "content"))
                    )
                    sleep(1)

        except Exception as e:
            LOG.error(f"An error occurred while scraping: {str(e)}")


class FullScraper:
    def __init__(self):
        self.BASE_PAGE_URL = "https://diariodarepublica.pt/dr/home"
        self.binary_path = binary_path
        # self.scraper = DailyScraper(PATH="data")
        if not os.path.exists("data"):
            os.mkdir("data")

        # Initialize the Chrome WebDriver
        svc = webdriver.ChromeService(executable_path=self.binary_path)
        self.driver = webdriver.Chrome(service=svc)
        self.driver.get(self.BASE_PAGE_URL)

        # Wait for the page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "content"))
        )
        sleep(1)

        self.navigate_calendar()

    def navigate_calendar(self):
        try:
            current_date = date.today()
            LOG.info(f"Starting to scrape from current date: {current_date}")

            initial_date = datetime.datetime.strptime("2021-01-01", "%Y-%m-%d")
            date_to_fetch = current_date

            while date_to_fetch >= initial_date.date():
                day_to_fetch = date_to_fetch.strftime("%d")
                month_to_fetch = date_to_fetch.strftime("%m")
                year_to_fetch = date_to_fetch.strftime("%Y")

                if date_to_fetch.weekday() < 5:  # Skip weekends
                    calendar = self.driver.find_element(By.CLASS_NAME, "calendar")
                    days = calendar.find_elements(By.TAG_NAME, "a")

                    for day in days:
                        day_title = day.get_attribute("title")
                        # Check if the day has the expected title format 'Ir para o dia yyyy-mm-dd'
                        if (
                            f"Ir para o dia {year_to_fetch}-{month_to_fetch}-{day_to_fetch}"
                            == day_title
                        ):
                            LOG.info(
                                f"Navigating to date: {year_to_fetch}-{month_to_fetch}-{day_to_fetch}"
                            )

                            # Click the link to navigate to the specific day's content
                            day.click()
                            WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.ID, "b3-Conteudo"))
                            )
                            sleep(1)

                            # Call method to scrape the articles for this date
                            driver_clone = copy.copy(self.driver)
                            try:
                                self.scrape_articles(
                                    driver=driver_clone, theme=None, PATH="data"
                                )
                            except Exception as e:
                                LOG.error(f"Error while scraping articles: {str(e)}")

                if date_to_fetch.day == 1:
                    # Roll back the month using the 'Mês Anterior' button
                    try:
                        previous_month_button = self.driver.find_element(
                            By.XPATH, "//a[@title='Mês Anterior']"
                        )
                        previous_month_button.click()
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.ID, "b6-Header"))
                        )
                        LOG.info(f"Moved to the previous month.")
                        sleep(1)
                    except Exception as e:
                        LOG.error(f"Failed to navigate to the previous month: {str(e)}")

                # Go to the previous day
                date_to_fetch = date_to_fetch - timedelta(days=1)

        except Exception as e:
            LOG.error(f"An error occurred while navigating the calendar: {str(e)}")

    def scrape_articles(self, driver: webdriver.Chrome, theme: str, PATH: str):
        try:
            valid_articles_xpath = "//div[@class='int-links' and not(preceding-sibling::div[1][contains(@class, 'tabttitulo')])]"
            articles = driver.find_elements(By.XPATH, valid_articles_xpath)

            for article in articles:
                if article.text != "":
                    link = article.find_element(By.TAG_NAME, "a").get_attribute("href")
                    LOG.info(f"Processing valid link: {link}")

                    # Switch pages and then go back to the original page
                    try:
                        driver.get(link)
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.ID, "b3-Conteudo"))
                        )
                        sleep(1)

                        date_container = driver.find_element(
                            By.ID, "b7-DataPublicacao2"
                        )
                        date = date_container.find_elements(By.TAG_NAME, "span")[1].text

                        publicacao_type_div = driver.find_element(
                            By.ID, "b7-Publicacao2"
                        )
                        publicacao_type = publicacao_type_div.find_elements(
                            By.TAG_NAME, "span"
                        )[1].text

                        publicacao_emissor_div = driver.find_element(
                            By.ID, "b7-Emissor2"
                        )
                        publicacao_emissor = publicacao_emissor_div.find_elements(
                            By.TAG_NAME, "span"
                        )[1].text

                        article_name = driver.find_element(
                            By.CLASS_NAME, "heading1"
                        ).text
                        article_content = driver.find_elements(By.TAG_NAME, "p")
                        article_text = "\n".join([p.text for p in article_content])

                        payload = {
                            "article_title": article_name,
                            "publication_type": publicacao_type,
                            "publisher": publicacao_emissor,
                            "article_content": article_text,
                            "link": link,
                            "date": date,
                            "theme": theme,
                        }

                        # Save the data to a file
                        file_name = article_name.replace(" ", "_").replace("/", "_")
                        payload_json = json.dumps(payload, ensure_ascii=False)

                        with open(f"{PATH}/{file_name}.json", "w") as f:
                            f.write(payload_json)

                        driver.back()
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "int-links"))
                        )
                        sleep(1)

                    except StaleElementReferenceException:
                        LOG.warning(
                            f"Stale element encountered for {link}. Retrying..."
                        )
                        driver.refresh()
                        self.scrape_articles(driver=driver, theme=theme, PATH=PATH)
                    except NoSuchElementException:
                        LOG.error(f"Element not found for {link}. Skipping...")
                        continue

        except Exception as e:
            LOG.error(f"Error scraping article: {link}. Error: {str(e)}")


class ThemeScraper:
    def __init__(self):
        BASE_THEME_URL = (
            f"https://diariodarepublica.pt/dr/legislacao-consolidada-destaques"
        )
        SELECT_THEME_DIV_ID = "ConteudoBotao"
        PATH = "theme_data"

        try:

            if not os.path.exists(PATH):
                os.mkdir(PATH)

            driver = webdriver.Chrome()
            driver.get(BASE_THEME_URL)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, SELECT_THEME_DIV_ID))
            )

            sleep(1)

            driver.find_element(By.ID, SELECT_THEME_DIV_ID).click()

            sleep(1)

            theme_divs = driver.find_elements(By.CLASS_NAME, "ThemeGrid_MarginGutter")

            # Iterate through each found element
            for element in theme_divs:
                theme_name = element.get_attribute("title")
                theme_link = element.get_attribute("href")

                LOG.info(f"Scraping theme: {theme_name}")
                self.scrape_page(
                    PATH=f"{PATH}/{theme_name}",
                    THEME_URL=theme_link,
                    THEME_NAME=theme_name,
                )

        except Exception as e:
            LOG.error(f"An error occurred while scraping: {str(e)}")

        finally:
            driver.quit()

    def scrape_page(self, PATH: str, THEME_URL: str, THEME_NAME: str):
        try:
            if not os.path.exists(PATH):
                os.mkdir(PATH)
            driver = webdriver.Chrome()
            driver.get(THEME_URL)

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "b3-Conteudo"))
            )

            sleep(1)
            current_page = 1
            num_pages = 2
            LOG.info(f"Scraping page: {THEME_URL}")

            for current_page in range(1):
                articles_divs = driver.find_elements(
                    By.CSS_SELECTOR, '[data-block="LegislacaoConsolidada.ItemPesquisa"]'
                )

                # Iterate over the found elements
                for article in articles_divs:
                    # Scrape the content inside each element
                    header = article.find_element(By.CLASS_NAME, "title")
                    link_to_article = header.find_element(
                        By.TAG_NAME, "a"
                    ).get_attribute("href")

                    self.scrape_article(
                        article_url=link_to_article, theme=THEME_NAME, PATH=PATH
                    )

                if num_pages == 1:
                    # Verify if there are more than one page
                    try:
                        pagination = driver.find_element(By.ID, "b8-PaginationWrapper")
                    except:
                        pagination = None
                    if pagination:
                        pagination_container = pagination.find_element(
                            By.ID, "b8-PaginationContainer"
                        )
                        if pagination_container:
                            page_divs = pagination_container.find_element(
                                By.ID, "b8-PaginationList"
                            )
                            buttons = page_divs.find_elements(By.TAG_NAME, "button")
                            num_pages += len(buttons)

                LOG.info(f"Scraped page: {current_page}/{num_pages-1}")

        except Exception as e:
            LOG.error(f"An error occurred while scraping: {str(e)}")

        finally:
            driver.quit()

    def scrape_article(self, article_url: str, theme: str, PATH: str):
        try:
            driver = webdriver.Chrome()
            driver.get(article_url)

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "b3-Conteudo"))
            )

            sleep(1)

            # Fetch article metadata
            date_container = driver.find_element(By.ID, "Input_Date3")
            date = date_container.get_attribute("value")

            publicacao_type_div = driver.find_elements(By.CLASS_NAME, "heading1")
            document_name = publicacao_type_div[0].text
            publicacao_type = publicacao_type_div[1].text

            source_document_div = driver.find_elements(
                By.CLASS_NAME, "ThemeGrid_Width10"
            )
            source_document = (
                source_document_div[1].find_element(By.TAG_NAME, "span").text
            )

            payload = {
                "article_title": document_name,
                "publication_type": publicacao_type,
                "source_document": source_document,
                "link": article_url,
                "date": date,
                "theme": theme,
                "sections": [],
            }

            content_divs = driver.find_elements(
                By.CSS_SELECTOR,
                '[data-block="LegislacaoConsolidada.FragmentoDetailTextoCompleto"]',
            )

            part_regex = r"Parte\s+[IVXLCDM]+"
            chapter_regex = r"Capítulo\s+[IVXLCDM]+"
            article_regex = r"Artigo\s+\d+\.\º"

            current_part = None
            current_chapter = None
            section_counter = 0

            current_part = {"part": f"Seção {section_counter}", "chapters": []}
            payload["sections"].append(current_part)

            for content in content_divs:
                lines = content.text.split("\n")

                for line in lines:

                    if re.match(part_regex, line):
                        if current_part:
                            payload["sections"].append(current_part)
                        section_counter += 1
                        current_part = {"part": line, "chapters": []}
                        current_chapter = None

                    elif re.match(chapter_regex, line):
                        if current_chapter and current_part:
                            current_part["chapters"].append(current_chapter)
                        current_chapter = {"chapter": line, "articles": []}

                    elif re.match(article_regex, line):
                        article_entry = {"article": line, "content": ""}

                        if current_chapter:
                            current_chapter["articles"].append(article_entry)

                        else:
                            current_part["chapters"].append(
                                {"chapter": None, "articles": [article_entry]}
                            )

                    elif current_chapter and current_chapter["articles"]:
                        current_chapter["articles"][-1]["content"] += line + "\n"
                    elif (
                        current_part
                        and current_part["chapters"]
                        and current_part["chapters"][-1]["articles"]
                    ):
                        current_part["chapters"][-1]["articles"][-1]["content"] += (
                            line + "\n"
                        )

            if current_chapter and current_part:
                current_part["chapters"].append(current_chapter)
            if current_part not in payload["sections"]:
                payload["sections"].append(current_part)

            file_name = document_name.replace(" ", "_").replace("/", "_")
            file_path = f"{PATH}/{file_name}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=4)

            LOG.info(f"Scraped article saved to {file_path}")

        except Exception as e:
            LOG.error(f"An error occurred while scraping: {str(e)}")

        finally:
            driver.quit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run_type",
        type=str,
        required=False,
        help="Specify the type of run: 'daily' or 'full'",
    )
    args = parser.parse_args()
    if args.run_type == "daily":
        DailyScraper()
    elif args.run_type == "full":
        FullScraper()
    elif args.run_type == "theme":
        ThemeScraper()
    else:
        LOG.error("Please specify the type of run: 'daily', 'full' or 'theme'")
        exit(1)


if __name__ == "__main__":
    main()
