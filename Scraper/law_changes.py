import json
import re
import time

from logging_config import logger
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

"""
payload = {
    "title": titulo_versao_inicial,
    "epigrafe": epigrafe_versao_inicial,
    "text": updated_content,
    "active_from": self.extract_date_from_text(update_div.text),
}"""


# URL_teste = "https://diariodarepublica.pt/dr/legislacao-consolidada/lei/2009-34546475"
URL_teste = (
    "https://diariodarepublica.pt/dr/legislacao-consolidada/decreto-lei/1999-34577575"
)


def parse_date(date_text):
    date_match = re.search(r"\d{4}-\d{2}-\d{2}", date_text)
    if date_match:
        return date_match.group(0)
    return None


def extract_law_info(text):
    sections = text.split("Artigo")[1:]

    laws_info = []

    for i, section in enumerate(sections):
        try:
            law_match = re.search(r"(\d+\.\d+)", section)
            if not law_match:
                continue

            law_number = law_match.group(1)

            final_date = None
            if "em vigor a partir de" in section:
                final_date = parse_date(section.split("em vigor a partir de")[1])

            if i == len(sections) - 1:
                initial_date = "1976-01-01"
            else:
                next_section = sections[i + 1]
                if "em vigor a partir de" in next_section:
                    initial_date = parse_date(
                        next_section.split("em vigor a partir de")[1]
                    )

            if law_number and initial_date and final_date:
                laws_info.append(
                    {
                        "law": f"law{law_number}",
                        "active_from": initial_date,
                        "final_date": final_date,
                    }
                )

        except Exception as e:
            logger.error(f"Error processing section: {str(e)}")
            continue

    return laws_info


def process_changes_in_new_tab(driver):
    original_window = driver.current_window_handle

    try:
        # Find and click changes link to open in new tab
        changes_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//span[contains(@style, 'color: rgb(51, 121, 183)') and contains(text(), 'VER ALTERAÇÕES')]",
                )
            )
        )
        driver.execute_script("arguments[0].click();", changes_link)

        try:
            changes_link.click()
        except:
            try:
                driver.execute_script("arguments[0].click();", changes_link)
            except Exception as e:
                logger.error(f"Failed to click: {e}")
                return None

        # Wait for the new tab to open and switch to it
        WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
        time.sleep(2)
        driver.switch_to.window(driver.window_handles[-1])

        logger.info("after switch to window")
        # Wait for content to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "b3-Conteudo"))
        )
        # Process changes here
        content = driver.find_element(By.ID, "b3-Conteudo")
        logger.info("after b3-content")
        # Extract dates and other information
        date_span = content.find_element(
            By.CSS_SELECTOR, "span[style*='font-size: 16px; margin-bottom: 0px;']"
        )
        logger.info("after span")
        text_content = date_span.text
        date_match = re.search(r"\d{4}-\d{2}-\d{2}", text_content)
        first_data = date_match.group(0) if date_match else ""
        dates_dic = []
        laws_changes = []
        date_span = driver.find_elements(
            By.XPATH, ".//span[contains(@style, 'color: rgb(177, 20, 28)')]"
        )

        logger.info("after data_span")
        for span in date_span:
            date_text = ""
            date_text = span.text if span else ""
            # Extract final date
            final_date = None
            if "em vigor a partir de" in date_text:
                final_date = parse_date(date_text.split("em vigor a partir de")[1])
            if "produz efeitos a partir de" in date_text:
                final_date = parse_date(
                    date_text.split("produz efeitos a partir de")[1]
                )
                dates_dic.append(final_date)
            dates_dic.append(first_data)
            i = 0
            articles = driver.find_elements(By.CLASS_NAME, "diploma-fragmento")
            for article in articles:
                text = article.text
                encoded_article = text.encode("utf-8")
                article_text = encoded_article.decode("utf-8")
                initial_date = dates_dic[i]
                final_date = dates_dic[i - 1]
                if i == 0:
                    final_date = "atual"
                i += 1
                if initial_date and final_date:
                    laws_changes.append(
                        {
                            "article_content": article_text,
                            "initial_date": initial_date,
                            "final_date": final_date,
                        }
                    )
        # Close the tab and switch back to original window
        driver.close()
        driver.switch_to.window(original_window)
        logger.info("after swtich to window")
        return laws_changes

    except Exception as e:
        logger.error(f"Error processing changes: {str(e)}")

        if len(driver.window_handles) > 1:
            driver.close()
        driver.switch_to.window(original_window)
        return None


def scrape_changes():
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(URL_teste)
        main_content = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    '//*[@id="$b21" and @data-block="LegislacaoConsolidada.DiplomaCompleto" and @class="OSBlockWidget"]',
                )
            )
        )
        article_sections = driver.find_elements(
            By.XPATH,
            '//div[@data-block="LegislacaoConsolidada.FragmentoDetailTextoCompleto"]',
        )

        logger.info(f"Found {len(article_sections)} articles")
        all_changes = []

        for i, section in enumerate(article_sections):
            if i < 10:
                article_text = section.text

                logger.info(f"\n=== Processing Article {i+1} ===")
                try:
                    changes_results = process_changes_in_new_tab(driver)

                    if changes_results:
                        # Combine article text with changes information
                        change_entry = {
                            "article_number": i + 1,
                            "article_text": article_text,
                            **changes_results,
                        }
                        all_changes.append(change_entry)

                except Exception as e:
                    logger.error(f"Error processing article {i+1}: {str(e)}")

        if all_changes:
            with open("all_changes.json", "w", encoding="utf-8") as f:
                json.dump(all_changes, f, ensure_ascii=False, indent=2)
            driver.back()
            time.sleep(5)  # Wait for main page to load
        else:
            logger.error("No data found")
            return None
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return None
    finally:
        driver.quit()


def main():
    logger.info("Starting scraper...")
    scrape_changes()


if __name__ == "__main__":
    main()
