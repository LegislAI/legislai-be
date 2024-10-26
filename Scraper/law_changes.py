from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import json
import re
import time

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
            print(f"Error processing section: {str(e)}")
            continue

    return laws_info


def scrape_changes():
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(URL_teste)

        # Click VER ALTERAÇÕES
        changes_link = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//span[contains(@style, 'color: rgb(51, 121, 183)') and contains(text(), 'VER ALTERAÇÕES')]",
                )
            )
        )

        # Store initial URL
        initial_url = driver.current_url

        # Click and wait
        changes_link.click()
        time.sleep(3)

        # Check if URL changed
        if driver.current_url != initial_url:
            print("URL changed to:", driver.current_url)
        else:
            print("Same URL, looking for content changes")

        content = driver.find_element(By.ID, "b3-Conteudo")

        date_span = content.find_element(
            By.CSS_SELECTOR, "span[style*='font-size: 16px; margin-bottom: 0px;']"
        )
        text_content = date_span.text

        date_match = re.search(r"\d{4}-\d{2}-\d{2}", text_content)
        first_data = date_match.group(0) if date_match else ""
        print(first_data)

        laws_data = []
        articles = driver.find_elements(By.CLASS_NAME, "diploma-fragmento")
        for article in articles:
            text = article.text
            encoded_article = text.encode("utf-8")
            article_text = encoded_article.decode("utf-8")

            # Get date information
            date_span = WebDriverWait(article, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//span[contains(@style, 'color: rgb(177, 20, 28)')]")
                )
            )
            date_text = date_span.text if date_span else ""

            # Extract final date
            final_date = None
            if "em vigor a partir de" in date_text:
                final_date = parse_date(date_text.split("em vigor a partir de")[1])
            if len(laws_data) > 0:
                initial_date = laws_data[-1]["final_date"]
            else:
                initial_date = first_data

            if initial_date and final_date:
                laws_data.append(
                    {
                        "article_content": article_text,
                        "initial_date": initial_date,
                        "final_date": final_date,
                    }
                )

        if laws_data:
            with open("laws_changes.json", "w", encoding="utf-8") as f:
                json.dump(laws_data, f, ensure_ascii=False, indent=2)

            driver.back()
            time.sleep(5)  # Wait for main page to load
        else:
            print("No data found")
            return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None
    finally:
        driver.quit()


def main():
    print("Starting scraper...")
    result = scrape_changes()
    if result:
        print("\nExtracted information:")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
