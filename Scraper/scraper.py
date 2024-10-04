#!/usr/bin/env python

import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
from time import sleep
import json

import argparse
import re

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class DailyScraper:
    def __init__(
        self, URL: str = "https://diariodarepublica.pt/dr", PATH: str = "data"
    ):
        # Prepare a folder to store the jsons
        if not os.path.exists(PATH):
            os.mkdir(PATH)

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

            # tableOfContent = driver.find_element(By.ID, "b3-Conteudo")
            articles = driver.find_elements(By.CLASS_NAME, "int-links")
            for i in articles:
                logging.info(i.text)
            for article in articles[1:]:
                if article.text != "":
                    link = article.find_element(By.TAG_NAME, "a").get_attribute("href")
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
                        "" "article_content": article,
                        "link": link,
                        "date": date,
                        "theme": None,
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
        TYPE = ""
        NUM = ""
        YEAR = ""
        DBID = ""
        ARTICLE_URL = f"{BASE_URL}/{TYPE}/{NUM}-{YEAR}-{DBID}"
        BASE_PAGE_URL = "https://diariodarepublica.pt/dr/screenservices/dr/Home/Serie1/DataActionGetDataAndApplicationSettings"

        try:
            # Initialize the Chrome WebDriver
            driver = webdriver.Chrome()

            # Navigate to the CVE website
            driver.get(BASE_PAGE_URL)

            print(driver.page_source)

            # Wait for the page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "content"))
            )

            sleep(1)

            # tableOfContent = driver.find_element(By.ID, "b3-Conteudo")
            articles = driver.find_elements(By.CLASS_NAME, "int-links")
            for i in articles:
                LOG.info(i.text)
            for article in articles[1:]:
                if article.text != "":
                    link = article.find_element(By.TAG_NAME, "a").get_attribute("href")
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
                        "" "article_content": article,
                        "link": link,
                        "date": date,
                        "theme": None,
                    }
                    # Lets replace the special characters
                    # Use utf8 formatting instead of the replace method
                    file_name = article_name.replace(" ", "_").replace("/", "_")
                    file_name.encode("utf-8").decode("utf-8")

                    payload = json.dumps(payload, ensure_ascii=False)

                    with open(f"data/{file_name}.json", "w") as f:
                        f.write(payload)

                    driver.back()
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "content"))
                    )
                    sleep(1)

        except Exception as e:
            LOG.error(f"An error occurred while scraping: {str(e)}")


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
                # Find elements with the specific data-block attribute
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
                            num_pages = len(buttons)

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

            date_container = driver.find_element(By.ID, "Input_Date3")
            date = date_container.text

            publicacao_type_div = driver.find_element(By.ID, "b7-Publicacao2")
            publicacao_type = publicacao_type_div.find_elements(By.TAG_NAME, "span")[
                1
            ].text

            publicacao_emissor_div = driver.find_element(By.ID, "b7-Emissor2")
            publicacao_emissor = publicacao_emissor_div.find_elements(
                By.TAG_NAME, "span"
            )[1].text

            document_name = driver.find_element(By.CLASS_NAME, "heading1").text

            content_divs = driver.find_elements(
                By.CSS_SELECTOR,
                '[data-block="LegislacaoConsolidada.FragmentoDetailTextoCompleto"]',
            )

            articleContent = driver.find_elements(By.TAG_NAME, "p")
            article = "".join(
                [p.text.encode("utf-8").decode("utf-8") + "\n" for p in articleContent]
            )

            payload = {
                "article_title": document_name,
                "publication_type": publicacao_type,
                "publisher": publicacao_emissor,
                "article_content": article,
                "link": article_url,
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
