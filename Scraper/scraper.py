import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
from time import sleep
import json


class Scrapper:
    def __init__(self):
        # Prepare a folder to store the jsons
        if not os.path.exists("data"):
            os.mkdir("data")

        try:
            # Initialize the Chrome WebDriver
            driver = webdriver.Chrome()

            # Navigate to the CVE website
            driver.get("https://diariodarepublica.pt/dr/home")

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
                    dateContainer = driver.find_element(By.ID, "b7-DataPublicacao2")
                    date = dateContainer.find_elements(By.TAG_NAME, "span")[1].text
                    articleName = driver.find_element(By.CLASS_NAME, "heading1").text

                    articleContent = driver.find_elements(By.TAG_NAME, "p")
                    article = "".join([p.text + "\n" for p in articleContent])

                    payload = {
                        "articleName": articleName,
                        "articleContent": article,
                        "link": link,
                        "date": date,
                    }
                    # Lets replace the special characters
                    #Use utf8 formatting instead of the replace method
                    fileName = (
                        articleName.replace(" ", "_")
                        .replace("º", "o")
                        .replace("ª", "a")
                        .replace("/", "_")
                        .replace("ç", "c")
                        .replace("ã", "a")
                    )

                    payload = json.dumps(payload, ensure_ascii=False)

                    with open(f"data/{fileName}.json", "w") as f:
                        f.write(payload)

                    driver.back()
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "content"))
                    )
                    sleep(1)

        except Exception as e:
            logging.error(f"An error occurred while scraping: {str(e)}")


Scrapper()
