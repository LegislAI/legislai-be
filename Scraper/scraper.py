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
        test_payload = {"versionInfo":{"moduleVersion":"wlu6H+zzmet+EICoDqirUA","apiVersion":"A00rktBtkSvxDLsFy+6mgg"},"viewName":"Home.home","screenData":{"variables":{"ContagemLegConsolidada":"8671","ContagemJurisprudencia":"447894","UtilizadorGestorDeConteudo":"false","HasSerie1":"true","HasSerie2":"true","DataUltimaPublicacao":"2024-09-24","IsRendered":"true","IsMobile":"","ContagemLexionario":"2261","IsPageTracked":"true"}},"clientVariables":{"NewUser":"https://diariodarepublica.pt/dr/utilizador/registar","PesquisaAvancada":"https://diariodarepublica.pt/dr/pesquisa-avancada","Login":"https://diariodarepublica.pt/dr/utilizador/entrar","Data":"2024-09-23","DicionarioJuridicoId":"0","FullHTMLURL_EN":"https://diariodarepublica.pt/dr/en","ShowResult":"false","StartIndex":0,"EntityId_Filter":0,"BookId_Filter":0,"DiarioRepublicaId":"","paginaJson":"{\"Var\":[{\"Text\":[\"False\",\"True\",null,null,null,\"True\",\"True\"]}]}","Serie":"true","DiplomaConteudoId":"","Pesquisa":"","CookiePath":"/dr/","DataInicial_Filter":"1603-01-01","Query_Filter":"","UtilizadorPortalId":"0","t":"","Session_GUID":"e2862d00-ba82-44c8-a84e-becd7e261d64","DateTime":"2024-09-24T17:24:46.703Z","ActoLegislativoId_Filter":0,"FullHTMLURL":"https://diariodarepublica.pt/dr/home","TipoDeUtilizador":"","DataFinal_Filter":"1910-12-31","GUID":"","IsColecaoLegislacaoFilter":"true"}}
        url = f"{BASE_URL}/screenservices/dr/Home/home/DataActionGetDRByDataCalendario"
        headers = {"Content-Type": "application/json",
                   "Cookie" : "ConteudoDetalhe=; Tradutor=; Lexionario=; LegislacaoRegia=; en=; TradutorEN=; Abstract=; np=; PesquisaAvancada=; pr=; DataConsolidada=; LegCons=; osVisitor=5b9f7efb-fb75-4563-a1ba-a10c81a9b142; ASP.NET_SessionId=bbgute5l5xkymgpgblb20yz2; nr1Users=lid%3dAnonymous%3btuu%3d0%3bexp%3d0%3brhs%3dXBC1ss1nOgYW1SmqUjSxLucVOAg%3d%3bhmc%3dJtcVf7R%2feKL81mKfj9zspoL6b6Q%3d; nr2Users=crf%3dT6C%2b9iB49TLra4jEsMeSckDMNhQ%3d%3buid%3d0%3bunm%3d; _pk_id.1.6c73=129ec527c67fd0de.1726912850.; _hjSessionUser_886788=eyJpZCI6ImI2ZWQxMmYyLTBhMjYtNWQ1YS1hYWUwLTg4ODJkMjExY2M0NSIsImNyZWF0ZWQiOjE3MjY5MTI4NTA1NDMsImV4aXN0aW5nIjp0cnVlfQ==; _gid=GA1.2.829674098.1727198688; osVisit=5bcfb930-0629-42f4-b4d4-61ae2e55696b; _pk_ref.1.6c73=%5B%22%22%2C%22%22%2C1727206499%2C%22https%3A%2F%2Fwww.google.com%2F%22%5D; _pk_ses.1.6c73=1; _gat_UA-117523126-1=1; _hjSession_886788=eyJpZCI6ImFlMjVhNDAyLTA3YWUtNDc5YS1iNjI2LWU4MWE2M2U4NjgzMyIsImMiOjE3MjcyMDY0OTk2ODIsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowfQ==; _ga=GA1.1.1530382625.1726912850; _ga_TWL2S3RGK7=GS1.1.1727206498.9.1.1727206505.53.0.0; _ga_N4R698GP6Y=GS1.2.1727206499.6.1.1727206505.54.0.0"
                   }

        response = requests.post(url, json=test_payload, headers=headers)

        if response.status_code == 200:
            logging.info("Payload successfully sent.")
        else:
            logging.error(f"Failed to send payload. Status code: {response.status_code}")

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
