from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import random
import re

# Daftar proxy yang akan digunakan
proxy_list = [
    "103.39.49.98:8080",
    "146.196.110.13:3888",
    "27.112.66.98:8181",
    "103.135.24.2:8080",
    "43.247.36.126:8080",
    "122.144.4.134:63123",
    "103.135.48.210:8080",
    "119.110.69.102:57788",
    "103.162.16.47:8080",
    "103.162.16.115:8080"
]

def scrape_google_maps(keyword, proxy_address):
    print(f"Menggunakan proxy: {proxy_address}")
    
    chrome_options = Options()
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument(f'--proxy-server=http://{proxy_address}')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    results = []

    try:
        driver.get(f'https://www.google.com/maps/search/{keyword}/')
        print(f"Mencari: {keyword}")
        time.sleep(5)

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="feed"]'))
            )
            scrollable_div = driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')

            # Scroll banyak kali sampai semua tempat keluar
            last_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
            scroll_attempt = 0
            max_scroll_attempts = 30  # Atur maksimal scroll 30 kali

            print("Mulai scrolling untuk load semua hasil...")
            while scroll_attempt < max_scroll_attempts:
                driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
                time.sleep(2)
                
                new_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
                
                if new_height == last_height:
                    print("Scroll mencapai batas, tidak ada hasil baru.")
                    break
                last_height = new_height
                scroll_attempt += 1
                print(f"Scroll ke-{scroll_attempt}")

            time.sleep(3)  # Tunggu terakhir setelah scrolling selesai

            items = driver.find_elements(By.CSS_SELECTOR, 'div.Nv2PK')
            print(f"Total tempat ditemukan: {len(items)}")

            highlight_js = """
            var original_style = arguments[0].getAttribute('style') || '';
            arguments[0].setAttribute('style', original_style + '; border: 2px solid red; background: rgba(255, 255, 0, 0.3); padding: 2px;');
            setTimeout(function(){ 
                arguments[0].setAttribute('style', original_style); 
            }, 1000);
            """

            for i, item in enumerate(items):
                print(f"Memproses item {i+1}/{len(items)}")
                data = {}

                try:
                    driver.execute_script(highlight_js, item)
                    time.sleep(0.2)

                    title_element = item.find_element(By.CSS_SELECTOR, ".qBF1Pd.fontHeadlineSmall")
                    data['title'] = title_element.text
                except:
                    continue

                try:
                    link_element = item.find_element(By.CSS_SELECTOR, "a.hfpxzc")
                    data['link'] = link_element.get_attribute('href')
                except:
                    data['link'] = None

                try:
                    rating_element = item.find_element(By.CSS_SELECTOR, 'span.ZkP5Je[role="img"]')
                    aria_label = rating_element.get_attribute('aria-label')
                    rating_match = re.search(r'([0-9]+[.,][0-9]+)', aria_label)
                    if rating_match:
                        data['rating'] = float(rating_match.group(1).replace(',', '.'))
                    else:
                        data['rating'] = None
                except:
                    data['rating'] = None

                try:
                    address_spans = item.find_elements(By.CSS_SELECTOR, '.W4Efsd span')
                    for i in range(len(address_spans) - 1):
                        if address_spans[i].text == '·' and i+1 < len(address_spans):
                            data['address'] = address_spans[i+1].text
                            break
                    else:
                        data['address'] = None
                except:
                    data['address'] = None

                try:
                    open_time_element = item.find_element(By.CSS_SELECTOR, 'span[style*="color: rgba(25,134,57"]')
                    data['opening_hours'] = open_time_element.text
                except:
                    try:
                        spans = item.find_elements(By.CSS_SELECTOR, '.W4Efsd span')
                        for span in spans:
                            if 'Buka' in span.text or 'Tutup' in span.text:
                                data['opening_hours'] = span.text
                                break
                        else:
                            data['opening_hours'] = None
                    except:
                        data['opening_hours'] = None

                results.append(data)

            print(f"Berhasil mengambil data dari {len(results)} tempat.")
            print("Menunggu 5 detik sebelum menutup browser...")
            time.sleep(5)

        except Exception as e:
            print(f"Error saat loading hasil: {e}")

    except Exception as e:
        print(f"Error saat membuka Google Maps: {e}")

    finally:
        driver.quit()
        print("Browser ditutup.")

    return results

def main():
    keyword = "wisata dekat danau toba"
    proxy = random.choice(proxy_list)
    print(f"Proxy yang dipilih: {proxy}")

    print("Mulai scraping...")
    results = scrape_google_maps(keyword, proxy)

    filename = f"gmaps_{keyword.replace(' ', '_')}_{int(time.time())}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Hasil disimpan ke {filename}")
    print("Selesai scraping!")

if __name__ == "__main__":
    main()
