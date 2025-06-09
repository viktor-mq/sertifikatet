import os
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from collections import defaultdict

BASE_URL = "https://lovdata.no"
PAGE_URL = "https://lovdata.no/dokument/SF/forskrift/2005-10-07-1219/KAPITTEL_2"
SAVE_DIR = "static/images/signs"

os.makedirs(SAVE_DIR, exist_ok=True)

def slugify(text, count_map):
    base = text.lower().replace(" ", "_").replace(".", "_").replace(",", "").replace("–", "-")
    base = ''.join(c for c in base if c.isalnum() or c == '_')
    count = count_map[base]
    count_map[base] += 1
    return f"{base}" if count == 0 else f"{base}_{count+1}"

def scrape_and_download():
    count_map = defaultdict(int)
    image_log = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36")
        page.goto(PAGE_URL, timeout=60000)
        page.wait_for_timeout(5000)  # vent 5 sekunder på at innhold lastes
        page_content = page.content()
        with open("debug_lovdata.html", "w", encoding="utf-8") as f:
            f.write(page_content)
        print("✅ Lagret HTML-innhold til debug_lovdata.html")
        browser.close()

        soup = BeautifulSoup(page_content, "html.parser")

        images = soup.find_all("img")
        print(f"🔍 Fant {len(images)} <img>-tagger totalt")

        current_category = "ukjent"

        for img in images:
            src = img.get("src", "")
            if ".gif" not in src:
                continue

            # Finn kategori fra overskrift over bildet
            heading = img.find_previous(["h3", "h4"])
            if heading:
                heading_text = heading.get_text(strip=True).lower()
                heading_text = heading_text.replace("de enkelte", "")
                for word in ["skilt", "tegn", "symboler"]:
                    heading_text = heading_text.replace(word, "")
                current_category = heading_text.split(".")[-1].strip().replace(" ", "_") or "ukjent"

            # Finn beskrivelse
            desc = ""
            if img.parent and img.parent.name == "td":
                id_text = img.parent.get_text(strip=True)
                desc_td = img.parent.find_next_sibling("td")
                if desc_td:
                    all_text = desc_td.get_text(separator=" ", strip=True)
                    if id_text in all_text:
                        desc = all_text.replace(id_text, "").strip()
                    else:
                        desc = all_text
            if not desc:
                desc = img.get("alt", "") or "skilt"

            # Klargjør mappe og filnavn
            category_folder = os.path.join(SAVE_DIR, current_category)
            os.makedirs(category_folder, exist_ok=True)

            full_url = urljoin(BASE_URL, src.split("?")[0])  # fjerne evt. timestamp
            original_name = os.path.basename(src).split("?")[0]
            clean_name = slugify(desc, count_map) + ".gif"
            save_path = os.path.join(category_folder, clean_name)

            try:
                import requests
                img_data = requests.get(full_url).content
                with open(save_path, "wb") as f:
                    f.write(img_data)
                image_log.append((original_name, clean_name, desc, current_category))
                print(f"Lagret {clean_name} i {current_category}/")
            except Exception as e:
                print(f"Feil ved nedlasting av {original_name}: {e}")
    return image_log

if __name__ == "__main__":
    scrape_and_download()
