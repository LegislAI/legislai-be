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


class Scrape:
    def __init__(self):
        BASE_THEME_URL = "https://www.segurancarodoviaria.pt/codigo-da-estrada/"
        PATH = "data/codigo_da_estrada"

        try:
            if not os.path.exists(PATH):
                os.mkdir(PATH)

            driver = webdriver.Chrome()
            driver.get(BASE_THEME_URL)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "container-fluid"))
            )

            sleep(1)

            titles = driver.find_elements(By.ID, "codigoestrada-content")
            for title in titles:
                title_button = title.find_element(By.TAG_NAME, "a")
                title_button.click()
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
                full_updates_div = updates_div.find_element(
                    By.CSS_SELECTOR, "[data-container]"
                )
                full_updates_link = full_updates_div.find_element(By.TAG_NAME, "a")
                updated_list = updates_div.find_element(By.CSS_SELECTOR, "[data-list]")
                updated_list = updated_list.find_elements(
                    By.CSS_SELECTOR, "[data-container]"
                )

                updates = []
                for updated_item in updated_list:
                    updates.append(self.parse_updated_section(updated_item))

                # alteracoes_completas_link.click()
                # WebDriverWait(driver, 10).until(
                #     EC.presence_of_element_located((By.ID, "b3-Conteudo"))
                # )

                # initial_date = re.search(r"\d{4}-\d{2}-\d{2}", dr_document).group(0)
                iterations = []
                # iterations = self.parse_alteration_page(
                #     driver, initial_date=initial_date
                # )

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
            LOG.error(f"An error occurred while parsing the alteration section: {e}")
            return None

    def parse_alteration_page(self, driver, initial_date: str) -> list:

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
    Scrape()


if __name__ == "__main__":
    main()
