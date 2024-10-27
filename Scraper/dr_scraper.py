#!/usr/bin/env python
import argparse
import copy
import datetime
import json
import logging
import os
import re
import subprocess
import uuid
from datetime import date
from datetime import timedelta
from time import sleep

import boto3
from botocore.exceptions import ClientError
from chromedriver_py import binary_path
from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("scraper_log.log"), logging.StreamHandler()],
)
LOG = logging.getLogger(__name__)

FULL_SCRAPER_BUCKET_NAME = "legislaifullscraperdata"
LAW_TYPE_BUCKET_NAME = "legislailawtypescraperdata"
DATA_SOURCE = "diario_da_republica"


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

    def zip_path(self, src_path: str = "data", dest_path: str = "data"):
        subprocess.run(["zip", "-r", f"{dest_path}", src_path])

    def upload_file(self, file_name, bucket_name, object_name=None):
        """Upload a file to an S3 bucket"""
        if not isinstance(file_name, (str, os.PathLike)):
            raise ValueError("Filename must be a string or a path-like object")

        if not os.path.isfile(file_name):
            raise ValueError(f"The file {file_name} does not exist")

        if object_name is None:
            object_name = os.path.basename(file_name)

        load_dotenv()
        LOG.info("Uploading files to S3")

        s3_client = boto3.client(
            "s3",
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            region_name=os.environ.get("AWS_REGION"),
        )

        # Ensure bucket exists or create it
        try:
            s3_client.head_bucket(Bucket=bucket_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={
                        "LocationConstraint": os.environ.get("AWS_REGION"),
                    },
                )
            else:
                logging.error(e)
                return False

        try:
            s3_client.upload_file(file_name, bucket_name, object_name)
        except ClientError as e:
            logging.error(e)
            return False

        return True

    def navigate_calendar(self):
        try:
            current_date = date.today()
            initial_date = datetime.datetime.strptime("2021-01-01", "%Y-%m-%d")
            date_to_fetch = current_date

            version = uuid.uuid4()

            # Use Year/Month folder structure
            year_folder = date_to_fetch.strftime("%Y")
            month_folder = date_to_fetch.strftime("%m")
            path_name = f"data/{DATA_SOURCE}/{year_folder}/{month_folder}/full_scraper_v{version}"

            if not os.path.exists(path_name):
                os.makedirs(path_name)

            while date_to_fetch >= initial_date.date():
                day_to_fetch = date_to_fetch.strftime("%d")
                month_to_fetch = date_to_fetch.strftime("%m")
                year_to_fetch = date_to_fetch.strftime("%Y")

                if date_to_fetch.weekday() < 5:
                    calendar = self.driver.find_element(By.CLASS_NAME, "calendar")
                    days = calendar.find_elements(By.TAG_NAME, "a")

                    for day in days:
                        day_title = day.get_attribute("title")
                        if (
                            f"Ir para o dia {year_to_fetch}-{month_to_fetch}-{day_to_fetch}"
                            == day_title
                        ):
                            LOG.info(
                                f"Navigating to date: {year_to_fetch}-{month_to_fetch}-{day_to_fetch}"
                            )

                            day.click()
                            WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.ID, "b3-Conteudo"))
                            )
                            sleep(1)

                            driver_clone = copy.copy(self.driver)
                            try:
                                self.scrape_articles(
                                    driver=driver_clone, theme=None, PATH=path_name
                                )
                            except Exception as e:
                                LOG.error(f"Error while scraping articles: {str(e)}")

                if date_to_fetch.day == 1:
                    try:
                        previous_month_button = self.driver.find_element(
                            By.XPATH, "//a[@title='Mês Anterior']"
                        )
                        previous_month_button.click()

                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.ID, "b6-Header"))
                        )

                        # Zip and upload previous month
                        zip_file_name = f"{path_name}.zip"
                        self.zip_path(src_path=path_name, dest_path=zip_file_name)
                        bucket_path = f"full_scraper/{DATA_SOURCE}/{year_folder}/{month_folder}/full_scraper_v{version}.zip"
                        self.upload_file(
                            file_name=zip_file_name,
                            bucket_name=FULL_SCRAPER_BUCKET_NAME,
                            object_name=bucket_path,
                        )

                        subprocess.run(["rm", zip_file_name])

                        # Update path for new month
                        date_to_fetch -= timedelta(days=1)
                        year_folder = date_to_fetch.strftime("%Y")
                        month_folder = date_to_fetch.strftime("%m")
                        path_name = f"data/{DATA_SOURCE}/{year_folder}/{month_folder}/full_scraper_v{version}"

                        if not os.path.exists(path_name):
                            os.makedirs(path_name)

                        LOG.info(f"Moved to previous month, new path: {path_name}")
                    except Exception as e:
                        LOG.error(f"Failed to navigate to previous month: {str(e)}")

                date_to_fetch -= timedelta(days=1)

        except Exception as e:
            LOG.error(f"Error while navigating the calendar: {str(e)}")
            back_up_path = f"data/{current_date}.zip"
            self.zip_path(src_path="data", dest_path=back_up_path)
            self.upload_file(
                back_up_path,
                FULL_SCRAPER_BUCKET_NAME,
                object_name=f"error_backup/{DATA_SOURCE}/{back_up_path}",
            )
            subprocess.run(["rm", f"data/{current_date}.zip"])
        finally:
            self.driver.quit()

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
                        continue
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


class LawTypeScraper:
    def __init__(self):
        BASE_THEME_URL = (
            "https://diariodarepublica.pt/dr/legislacao-consolidada-destaques"
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

            theme_divs = driver.find_elements(By.CLASS_NAME, "ThemeGrid_MarginGutter")
            self.scrape_article(
                PATH="data",
                article_url="https://diariodarepublica.pt/dr/legislacao-consolidada/lei/2009-34546475",
                theme="Lei do trabalho",
            )

        except Exception as e:
            LOG.error(f"An error occurred while scraping: {str(e)}")
            exit()
        finally:
            driver.quit()

    def scrape_article(self, article_url: str, theme: str, PATH: str):
        try:
            driver = webdriver.Chrome()
            driver.get(article_url)

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "b3-Conteudo"))
            )

            sleep(2)
            content = driver.find_element(By.ID, "b3-Conteudo")

            date_version_wrapper = content.find_element(By.CLASS_NAME, "input-date")
            date_version = date_version_wrapper.find_element(
                By.TAG_NAME, "input"
            ).get_attribute("value")

            heading = content.find_element(By.ID, "Cabecalho")
            law_name = (
                heading.find_element(By.ID, "ConteudoTitle")
                .find_elements(By.TAG_NAME, "div")[0]
                .text
            )
            body = driver.find_element(By.ID, "ConteudoGeral")
            dr_document = body.find_element(By.ID, "Modificado").text

            payload = {
                "document_name": theme,
                "law_name": law_name,
                "dr_document": dr_document,
                "link": article_url,
                "date_of_fetch": date_version,
                "theme": theme,
                "sections": {},
            }

            content_div = body.find_element(
                By.CSS_SELECTOR,
                '[data-block="LegislacaoConsolidada.DiplomaCompleto"]',
            )

            last_book_number = ""
            last_book_title = ""
            last_title_name = ""
            last_book_chapter_number = ""
            last_book_chapter_name = ""

            try:

                diploma_div = content_div.find_element(
                    By.CSS_SELECTOR, "[data-container]"
                )
                titulo = diploma_div.find_element(
                    By.CLASS_NAME, "Fragmento_Titulo"
                ).text
                texto = diploma_div.find_element(By.CLASS_NAME, "Fragmento_Texto").text

                updates_div = diploma_div.find_element(
                    By.CSS_SELECTOR,
                    '[data-block="LegislacaoConsolidada.AlteracoesByFragmentoId"]',
                )
                updated_list = updates_div.find_element(By.CSS_SELECTOR, "[data-list]")
                updated_list = updated_list.find_elements(
                    By.CSS_SELECTOR, "[data-container]"
                )
                full_updates_div = updates_div.find_element(
                    By.CSS_SELECTOR, "[data-container]"
                )
                full_updates_link = full_updates_div.find_element(By.TAG_NAME, "a")

                updates = []
                for updated_item in updated_list:
                    updates.append(self.parse_updated_section(updated_item))
                try:
                    # WebDriverWait(driver, 10).until(
                    #     EC.presence_of_element_located((By.ID, "b3-Conteudo"))
                    # )

                    copy_of_driver = webdriver.Chrome()
                    driver.get(article_url)
                    initial_date = re.search(r"\d{4}-\d{2}-\d{2}", dr_document).group(0)
                    iterations = []
                    iterations = self.parse_alteration_page(
                        copy_of_driver, full_updates_link, initial_date=initial_date
                    )


                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "b3-Conteudo"))
                    )
                    
                except Exception as e:
                    LOG.warning(f"Could not fetch alterations: {e}")
                    iterations = [] 

                sleep(5)

                diploma_payload = {
                    "title": titulo,
                    "text": texto,
                    "updates": updates,
                    "previous_iterations": iterations,
                }

                last_book_title = titulo

                payload["sections"]["diploma"] = diploma_payload
            except Exception as e:
                LOG.warning(f"No diploma or alteration found: {e}")

            try:
                content = content_div.find_elements(
                    By.CSS_SELECTOR,
                    '[data-block="LegislacaoConsolidada.FragmentoDetailTextoCompleto"]',
                )
                for section in content:
                    try:
                        section_title = section.find_element(
                            By.CLASS_NAME, "Fragmento_Titulo"
                        )
                    except:
                        LOG.warning("Could not fetch title")
                        continue
                    try:
                        section_epigrafe = section.find_element(
                            By.CLASS_NAME, "Fragmento_Epigrafe"
                        )
                    except:
                        LOG.warning("Could not fetch epigrafe")
                        continue

                    book_regex = r"Livro (.*)"
                    title_regex = r"Título (.*)"
                    chapter_regex = r"Capítulo (.*)"
                    article_regex = r"Artigo (.*)"
                    if re.search(book_regex, section_title.text):
                        LOG.info(f"Found book...")
                        last_book_number = section_title.text
                        last_book_title = section_epigrafe.text
                    elif re.search(title_regex, section_title.text):
                        LOG.info("Updating book title...")
                        last_title_name = section_epigrafe.text
                    elif re.search(chapter_regex, section_title.text):
                        LOG.info("Updating book chapter")
                        last_book_chapter_number = section_title.text
                        last_book_chapter_name = section_epigrafe.text
                    elif re.search(article_regex, section_title.text):
                        LOG.info("Found new article")
                        section_text = section.find_element(
                            By.CLASS_NAME, "Fragmento_Texto"
                        )
                        try:
                            updates_div = section.find_element(
                                By.CSS_SELECTOR,
                                '[data-block="LegislacaoConsolidada.AlteracoesByFragmentoId"]',
                            )
                            full_updates_div = updates_div.find_element(
                                By.CSS_SELECTOR, "[data-container]"
                            )
                            alteracoes_completas_link = full_updates_div.find_element(
                                By.TAG_NAME, "a"
                            )
                            updates_list = updates_div.find_element(
                                By.CSS_SELECTOR, "[data-list]"
                            )
                            updates_list = updates_list.find_elements(
                                By.CSS_SELECTOR, "[data-container]"
                            )

                            for update_item in updates_list:
                                updates.append(self.parse_updated_section(update_item))
                        except:
                            LOG.warning(f"Article was not updated")
                            updates = []

                        # alteracoes_completas_link_copy = copy.copy(alteracoes_completas_link)

                        # alteracoes_completas_link.click()
                        # WebDriverWait(driver, 10).until(
                        #     EC.presence_of_element_located((By.ID, "b3-Conteudo"))
                        # )
                        section_name = (
                            f"{last_title_name}>{last_book_chapter_number}:{last_book_chapter_name}>{section_title.text}".encode(
                                "utf-8"
                            )
                            .decode("utf-8")
                            .replace(" ", "_")
                            .replace("/", "_")
                        )
                        section_payload = {
                            "book_number": last_book_number.encode("utf-8").decode(
                                "utf-8"
                            ),
                            "book_title": last_book_title.encode("utf-8").decode(
                                "utf-8"
                            ),
                            "chapter": f"{last_title_name}>{last_book_chapter_number}:{last_book_chapter_name}",
                            "title": section_title.text.encode("utf-8").decode("utf-8"),
                            "epigrafe": section_epigrafe.text.encode("utf-8").decode(
                                "utf-8"
                            ),
                            "text": section_text.text.encode("utf-8").decode("utf-8"),
                            "updates": updates,
                            "previous_iterations": [],
                        }

                        payload["sections"][section_name] = section_payload

            except Exception as e:
                LOG.warning(f"No sections found: {e}")

        except Exception as e:
            LOG.error(f"An error occurred while scraping: {e}")
        finally:
            driver.quit()

            # payload = json.dumps(payload, ensure_ascii=False)
            with open(f"{PATH}.json", "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=4)

            LOG.info("Finished scraping the document")

    def parse_updated_section(self, element) -> dict:
        try:
            link_element = element.find_element(By.TAG_NAME, "a")
            url = link_element.get_attribute("href")

            full_text = link_element.text

            alteration_text = element.text
            if "em vigor a partir de" in alteration_text:
                active_from = alteration_text.split("em vigor a partir de")[-1].strip()
            else:
                active_from = "Not specified"

            return {"text": full_text, "url": url, "active_from": active_from}

        except Exception as e:
            print(f"An error occurred while parsing the alteration section: {e}")
            return None

    def parse_alteration_page(self, driver, element, initial_date: str) -> list:


        element.click()

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "b3-Conteudo"))
        )

        sleep(1)

        content = driver.find_element(By.ID, "b3-Conteudo")
        alteracoes_div = content.find_element(
            By.CSS_SELECTOR,
            '[data-block="LegislacaoConsolidada.FragmentoVerDiferencas"]',
        )
        versao_inicial = alteracoes_div.find_element(By.ID, "b20-b1-VersaoInicial")
        titulo_versao_inicial = ""
        epigrafe_versao_inicial = ""
        content = {"versions": []}
        try:
            titulo_versao_inicial = versao_inicial.find_element(
                By.CLASS_NAME, "Fragmento_Titulo"
            ).text
            epigrafe_versao_inicial = versao_inicial.find_element(
                By.CLASS_NAME, "Fragmento_Epigrafe"
            ).text
            payload = {
                "title": titulo_versao_inicial,
                "epigrafe": epigrafe_versao_inicial,
                "text": versao_inicial.find_element(
                    By.CLASS_NAME, "Fragmento_Texto"
                ).text,
                "active_from": initial_date,
            }
            content["versions"].append(payload)
        except Exception as e:
            LOG.error(f"An error occurred while scraping: {str(e)}")

        try:
            subsequent_versions = alteracoes_div.find_elements(
                By.XPATH, ".//div[@id='b20-b1-VersoesSeguintes']/div/div"
            )

            for version in subsequent_versions:

                article = version.find_element(
                    By.XPATH, ".//div[contains(@id, 'DetalheArtigo')]"
                )
                update_div = version.find_element(
                    By.XPATH, ".//div[contains(@id, 'AlteradoPor')]"
                )

                updated_content = article.find_element(
                    By.CLASS_NAME, "Fragmento_Texto"
                ).text

                payload = {
                    "title": titulo_versao_inicial,
                    "epigrafe": epigrafe_versao_inicial,
                    "text": updated_content,
                    "active_from": self.extract_date_from_text(update_div.text),
                }
                content["versions"].append(payload)

        except Exception as e:
            LOG.error(f"An error occurred while scraping: {str(e)}")

        return content

    def extract_date_from_text(self, text):
        if "em vigor a partir de" in text:
            return text.split("em vigor a partir de")[-1].strip()
        else:
            return "Date not specified"


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
    elif args.run_type == "law_type":
        LawTypeScraper()
    else:
        LOG.error("Please specify the type of run: 'daily', 'full' or 'theme'")
        exit(1)


if __name__ == "__main__":
    main()
