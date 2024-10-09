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

import re
import datetime
from datetime import date, timedelta
import copy
import uuid
import subprocess

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("scraper_log.log"), logging.StreamHandler()],
)
LOG = logging.getLogger(__name__)

FULL_SCRAPER_BUCKET_NAME = "legislaifullscraperdata"
DATA_SOURCE = "dgsi"


class FullScraper:
    def __init__(self):
        LOG.info(
            f"""
                 ########################################
                    Starting scraping {DATA_SOURCE}...
                 ########################################"""
        )

        self.BASE_PAGE_URL = f"https://www.dgsi.pt/"
        self.binary_path = binary_path
        if not os.path.exists("data"):
            os.mkdir("data")

        # Initialize the Chrome WebDriver
        svc = webdriver.ChromeService(executable_path=self.binary_path)
        self.driver = webdriver.Chrome(service=svc)
        self.driver.get(self.BASE_PAGE_URL)

        # Wait for the page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table"))
        )
        sleep(1)

        self.navigate_databases()

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

    def navigate_databases(self):
        try:

            version = uuid.uuid4()

            # Use Year/Month folder structure
            # year_folder = date_to_fetch.strftime('%Y')
            # month_folder = date_to_fetch.strftime('%m')
            path_name = f"data/{DATA_SOURCE}"

            if not os.path.exists(path_name):
                os.makedirs(path_name)

            # Get the databases table
            databases_table = self.driver.find_elements(By.CSS_SELECTOR, "table")[1]

            # Get the table body
            databases_body = databases_table.find_element(By.TAG_NAME, "tbody")
            databases_name = databases_body.find_element(By.TAG_NAME, "b")
            print(databases_name.text)

            databases_table = databases_body.find_element(By.TAG_NAME, "table")
            databases_table_body = databases_table.find_element(By.TAG_NAME, "tbody")

            databases_table_rows = databases_table_body.find_elements(By.TAG_NAME, "tr")

            # TODO: rever regex para só capturar o nome da base de dados ex: supremo tribunal de justiça
            for row in databases_table_rows:
                try:
                    database_content = row.find_element(By.TAG_NAME, "a")
                    database_name = database_content.text
                    database_link = database_content.get_attribute("href")
                    acordaos_regex = r"Acórdãos do (.*) [\(.*\)]*"
                    jurisprudencia_regex = r"Jurisprudência (.*) [\(.*\)]*"
                    acordaos_match = re.match(acordaos_regex, database_name)
                    jurisprudencia_match = re.match(jurisprudencia_regex, database_name)
                    if acordaos_match or jurisprudencia_match:
                        print(database_name, database_link)
                        self.driver.get(database_link)
                        database_name_path = (
                            database_name.encode("ascii", "ignore")
                            .decode("ascii")
                            .replace(" ", "_")
                            .lower()
                        )
                        path_name = f"data/{DATA_SOURCE}/{database_name_path}"
                        self.scrape_articles(
                            driver=self.driver, database=database_name, PATH=path_name
                        )
                        # print(jurisprudencia_match.group(1) if jurisprudencia_match else "")

                except NoSuchElementException:
                    continue

            # databases_rows = databases_body.find_elements(By.TAG_NAME, "tr")

            # while date_to_fetch >= initial_date.date():
            #     day_to_fetch = date_to_fetch.strftime("%d")
            #     month_to_fetch = date_to_fetch.strftime("%m")
            #     year_to_fetch = date_to_fetch.strftime("%Y")

            #     if date_to_fetch.weekday() < 5:
            #         calendar = self.driver.find_element(By.CLASS_NAME, "calendar")
            #         days = calendar.find_elements(By.TAG_NAME, "a")

            #         for day in days:
            #             day_title = day.get_attribute("title")
            #             if (
            #                 f"Ir para o dia {year_to_fetch}-{month_to_fetch}-{day_to_fetch}"
            #                 == day_title
            #             ):
            #                 LOG.info(
            #                     f"Navigating to date: {year_to_fetch}-{month_to_fetch}-{day_to_fetch}"
            #                 )

            #                 day.click()
            #                 WebDriverWait(self.driver, 10).until(
            #                     EC.presence_of_element_located((By.ID, "b3-Conteudo"))
            #                 )
            #                 sleep(1)

            #                 driver_clone = copy.copy(self.driver)
            #                 try:
            #                     self.scrape_articles(
            #                         driver=driver_clone, theme=None, PATH="data"
            #                     )
            #                 except Exception as e:
            #                     LOG.error(f"Error while scraping articles: {str(e)}")

            #     if date_to_fetch.day == 1:
            #         try:
            #             previous_month_button = self.driver.find_element(
            #                 By.XPATH, "//a[@title='Mês Anterior']"
            #             )
            #             previous_month_button.click()

            #             WebDriverWait(self.driver, 10).until(
            #                 EC.presence_of_element_located((By.ID, "b6-Header"))
            #             )

            #             # Zip and upload previous month
            #             zip_file_name = f"{path_name}.zip"
            #             self.zip_path(src_path=path_name, dest_path=zip_file_name)
            #             bucket_path = f"full_scraper/{year_folder}/{month_folder}/full_scraper_v{version}.zip"
            #             self.upload_file(file_name=zip_file_name, bucket_name=FULL_SCRAPER_BUCKET_NAME, object_name=bucket_path)

            #             # Update path for new month
            #             date_to_fetch -= timedelta(days=1)
            #             year_folder = date_to_fetch.strftime('%Y')
            #             month_folder = date_to_fetch.strftime('%m')
            #             path_name = f"data/{year_folder}/{month_folder}/full_scraper_v{version}"

            #             LOG.info(f"Moved to previous month, new path: {path_name}")
            #         except Exception as e:
            #             LOG.error(f"Failed to navigate to previous month: {str(e)}")

            #     date_to_fetch -= timedelta(days=1)

        except Exception as e:
            LOG.error(f"Error while navigating the databases: {str(e)}")
            # back_up_path = f"data/{current_date}.zip"
            # self.zip_path(src_path="data", dest_path=back_up_path)
            # self.upload_file(back_up_path, FULL_SCRAPER_BUCKET_NAME, object_name=f"error_backup/{back_up_path}")
        finally:
            self.driver.quit()

    def scrape_articles(self, driver: webdriver.Chrome, database: str, PATH: str):
        try:
            if "e-Justice" in database:
                return

            LOG.info(f"Scraping articles for database: {database}")

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


def main():
    FullScraper()


if __name__ == "__main__":
    main()
