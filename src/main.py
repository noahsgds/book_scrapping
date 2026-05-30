import requests
from bs4 import BeautifulSoup
import json
import urllib3
import re
import time
import logging
from pathlib import Path
from datetime import datetime

# Désactive les alertes SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)
BASE_URL = "https://books.toscrape.com/catalogue/"

def get_soup(url, retries=3):
    for i in range(retries):
        try:
            # J'ai augmenté le timeout à 20s pour éviter les erreurs de lecture
            response = requests.get(url, verify=False, timeout=20) 
            response.encoding = "utf-8"
            
            if response.status_code == 404:
                return "404"
                
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ Tentative {i+1}/{retries} échouée pour {url}. Erreur: {e}")
            time.sleep(2)
    return None

def get_books_links() -> list:
    links = []
    page = 1
    consecutive_failures = 0
    
    while True:
        url = f"{BASE_URL}page-{page}.html"
        logger.info(f"📑 Scan de la page : {url}")
        soup = get_soup(url)
        
        if soup == "404":
            logger.info("🏁 Fin du catalogue atteinte (Page 404). Passage au scraping...")
            break
            
        if not soup:
            consecutive_failures += 1
            if consecutive_failures >= 3:
                logger.error("🛑 Connexion perdue. Arrêt du scan.")
                break
            page += 1
            continue
            
        books_on_page = soup.select("article.product_pod h3 a")
        if not books_on_page:
            break
            
        consecutive_failures = 0 
        for tag in books_on_page:
            links.append(BASE_URL + tag["href"].replace("../", ""))
            
        page += 1
        time.sleep(0.3)
        
    return list(set(links))

# --- DOUBLON CORRIGÉ ICI ---
def scrape_book(url) -> dict | None:
    soup = get_soup(url)
    if not soup or soup == "404":
        return None

    rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
    
    table = {}
    for r in soup.select("table tr"):
        if r.th and r.td:
            table[r.th.text] = r.td.text
            
    title_tag = soup.find("h1")
    title = clean(title_tag.text) if title_tag else "N/A"
    if title == "N/A":
        logger.warning(f"⚠️ Titre introuvable : {url}")
        
    category_tags = soup.select("ul.breadcrumb li")
    rating_tag = soup.find("p", class_="star-rating")
    desc_tag = soup.find("div", id="product_description")
    desc_p = desc_tag.find_next("p") if desc_tag else None

    price_tag = soup.find("p", class_="price_color")
    price_match = re.search(r"[\d.]+", price_tag.text) if price_tag else None
    if not price_match:
        logger.warning(f"⚠️ Prix introuvable : '{title}' ({url})")
        price = 0.0
    else:
        price = float(price_match.group())

    stock_tag = soup.find("p", class_="instock availability")
    stock_match = re.search(r"\d+", stock_tag.text) if stock_tag else None
    if not stock_match:
        logger.warning(f"⚠️ Stock introuvable : '{title}' ({url})")
        stock = 0
    else:
        stock = int(stock_match.group())

    return {
        "upc":         table.get("UPC", "N/A"),
        "title":       title,
        "category":    clean(category_tags[-2].text) if category_tags and len(category_tags) > 1 else "N/A",
        "rating":      rating_map.get(rating_tag["class"][1], 0) if rating_tag and len(rating_tag.get("class", [])) > 1 else 0,
        "price":       price,
        "stock":       stock,
        "description": clean(desc_p.text) if desc_p else "N/A",
        "nb_reviews":  int(table.get("Number of reviews", 0)),
        "link":        url,
    }

def clean(text):
    if not text: return None
    return text.encode("utf-8", "ignore").decode("utf-8").strip()

def main():
    run_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    Path("data").mkdir(exist_ok=True)

    links = get_books_links()
    if not links:
        logger.error("❌ Aucun lien trouvé. Abandon.")
        return None

    # 🛑 MODE TEST RAPIDE : On ne prend que les 5 premiers livres pour vérifier que ça sauvegarde
    links = links[:5] 

    books = []
    for link in links:
        book = scrape_book(link)
        if book:
            books.append(book)
            logger.info(f"✅ {book['title']}")
        time.sleep(0.2)

    if books:
        with open(f"data/books_{run_date}.json", "w", encoding="utf-8") as f:
            json.dump(books, f, ensure_ascii=False, indent=2)
        return run_date
    return None

if __name__ == "__main__":
    main()