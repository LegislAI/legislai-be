#!/usr/bin/python3

import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
from time import sleep
import json

import argparse
import requests

BASE_URL = "https://diariodarepublica.pt/dr"

class DailyScraper:
    def __init__(self):
        # Prepare a folder to store the jsons
        if not os.path.exists("data"):
            os.mkdir("data")

        try:
            # Initialize the Chrome WebDriver
            driver = webdriver.Chrome()

            # Navigate to the CVE website
            driver.get(BASE_URL)

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
                    publicacao_type = publicacao_type_div.find_elements(By.TAG_NAME, "span")[1].text

                    publicacao_emissor_div = driver.find_element(By.ID, "b7-Emissor2")
                    publicacao_emissor = publicacao_emissor_div.find_elements(By.TAG_NAME, "span")[1].text
                    
                    article_name = driver.find_element(By.CLASS_NAME, "heading1").text

                    articleContent = driver.find_elements(By.TAG_NAME, "p")
                    article = "".join([p.text.encode('utf-8').decode('utf-8') + "\n" for p in articleContent])

                    payload = {
                        "article_title": article_name,
                        "publication_type": publicacao_type, 
                        "publisher": publicacao_emissor,
                        ""
                        "article_content": article,
                        "link": link,
                        "date": date,
                        "theme" : None
                    }
                    # Lets replace the special characters
                    # Use utf8 formatting instead of the replace method
                    file_name = article_name.replace(" ", "_").replace("/", "_")
                    file_name.encode('utf-8').decode('utf-8')

                    payload = json.dumps(payload, ensure_ascii=False)

                    with open(f"data/{file_name}.json", "w") as f:
                        f.write(payload)

                    driver.back()
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "content"))
                    )
                    sleep(1)

        except Exception as e:
            logging.error(f"An error occurred while scraping: {str(e)}")

class FullScraper:
    def __init__(self):
        TYPE=""
        NUM=""
        YEAR=""
        DBID=""
        ARTICLE_URL=f"{BASE_URL}/{TYPE}/{NUM}-{YEAR}-{DBID}"
        BASE_PAGE_URL="https://diariodarepublica.pt/dr/screenservices/dr/Home/Serie1/DataActionGetDataAndApplicationSettings"

        try:
            # Initialize the Chrome WebDriver
            driver = webdriver.Chrome()

            # Navigate to the CVE website
            driver.post(BASE_PAGE_URL)

            print(driver.page_source)

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
                    publicacao_type = publicacao_type_div.find_elements(By.TAG_NAME, "span")[1].text

                    publicacao_emissor_div = driver.find_element(By.ID, "b7-Emissor2")
                    publicacao_emissor = publicacao_emissor_div.find_elements(By.TAG_NAME, "span")[1].text
                    
                    article_name = driver.find_element(By.CLASS_NAME, "heading1").text

                    articleContent = driver.find_elements(By.TAG_NAME, "p")
                    article = "".join([p.text.encode('utf-8').decode('utf-8') + "\n" for p in articleContent])

                    payload = {
                        "article_title": article_name,
                        "publication_type": publicacao_type, 
                        "publisher": publicacao_emissor,
                        ""
                        "article_content": article,
                        "link": link,
                        "date": date,
                        "theme" : None
                    }
                    # Lets replace the special characters
                    # Use utf8 formatting instead of the replace method
                    file_name = article_name.replace(" ", "_").replace("/", "_")
                    file_name.encode('utf-8').decode('utf-8')

                    payload = json.dumps(payload, ensure_ascii=False)

                    with open(f"data/{file_name}.json", "w") as f:
                        f.write(payload)

                    driver.back()
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "content"))
                    )
                    sleep(1)

        except Exception as e:
            logging.error(f"An error occurred while scraping: {str(e)}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run_type", type=str, required=False, help="Specify the type of run: 'daily' or 'full'")
    args = parser.parse_args()
    if args.run_type == "daily":
        DailyScraper()
    elif args.run_type == "full":
        FullScraper()
    else:
        logging.error("Please specify the type of run: 'daily' or 'full'")
        exit(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
