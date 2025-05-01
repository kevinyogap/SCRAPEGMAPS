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
    """
    Fungsi untuk scraping Google Maps dengan keyword tertentu menggunakan proxy
    """
    print(f"Menggunakan proxy: {proxy_address}")
    
    # Konfigurasi Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Jalankan di mode headless
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument(f'--proxy-server=http://{proxy_address}')
    
    # Konfigurasi service
    service = Service(ChromeDriverManager().install())
    
    # Inisialisasi driver
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    results = []
    
    try:
        # Buka Google Maps dengan keyword pencarian
        driver.get(f'https://www.google.com/maps/search/{keyword}/')
        print(f"Mencari: {keyword}")
        
        # Tunggu hingga halaman dimuat
        try:
            # Jika ada dialog atau popup, coba klik
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "form:nth-child(2)"))).click()
        except Exception:
            pass
        
        # Tunggu feed hasil pencarian muncul
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="feed"]')))
            
            # Ambil div yang bisa di-scroll
            scrollable_div = driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
            
            # Scroll ke bawah untuk memuat lebih banyak hasil
            print("Scrolling untuk memuat lebih banyak hasil...")
            for i in range(5):  # Scroll 5 kali
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
                time.sleep(2)  # Tunggu konten dimuat
            
            # Ambil semua item hasil pencarian
            items = driver.find_elements(By.CSS_SELECTOR, 'div[role="feed"] > div > div')
            print(f"Ditemukan {len(items)} hasil")
            
            # Proses setiap item
            for i, item in enumerate(items):
                data = {}
                
                try:
                    # Ambil judul/nama tempat
                    title_element = item.find_element(By.CSS_SELECTOR, ".fontHeadlineSmall")
                    data['title'] = title_element.text
                except Exception:
                    continue  # Skip jika tidak ada judul
                
                try:
                    # Ambil link Google Maps
                    link_element = title_element.find_element(By.XPATH, "./ancestor::a")
                    data['link'] = link_element.get_attribute('href')
                except Exception:
                    pass
                
                try:
                    # Ambil rating dan jumlah review
                    rating_element = item.find_element(By.CSS_SELECTOR, 'span[aria-label][role="img"]')
                    rating_text = rating_element.get_attribute('aria-label')
                    rating_match = re.search(r'([0-9]+[.,][0-9]+)', rating_text)
                    reviews_match = re.search(r'([0-9]+) review', rating_text)
                    
                    if rating_match:
                        data['rating'] = float(rating_match.group(1).replace(',', '.'))
                    if reviews_match:
                        data['reviews'] = int(reviews_match.group(1))
                except Exception:
                    pass
                
                try:
                    # Ambil text content untuk nomor telepon dan alamat
                    text_content = item.text
                    
                    # Pattern untuk nomor telepon Indonesia
                    phone_pattern = r'(\+62[ -]?[0-9]{1,3}[ -]?[0-9]{1,4}[ -]?[0-9]{1,4}|0[0-9]{1,3}[ -]?[0-9]{1,4}[ -]?[0-9]{1,4})'
                    phone_match = re.search(phone_pattern, text_content)
                    if phone_match:
                        data['phone'] = phone_match.group(0)
                    
                    # Coba temukan alamat (pendekatan sederhana)
                    lines = text_content.split('\n')
                    for line in lines:
                        if ',' in line and len(line) > 10 and not line.startswith(('Buka', 'Tutup', 'Open')):
                            data['address'] = line
                            break
                except Exception:
                    pass
                
                results.append(data)
            
            print(f"Berhasil mengambil data dari {len(results)} tempat")
            
        except Exception as e:
            print(f"Error saat memproses hasil: {str(e)}")
    
    except Exception as e:
        print(f"Error saat mengakses Google Maps: {str(e)}")
    
    finally:
        # Tutup browser
        driver.quit()
    
    return results

def test_proxies():
    """Fungsi untuk menguji semua proxy dan memilih yang berfungsi"""
    working_proxies = []
    test_url = "https://www.google.com"
    
    for proxy in proxy_list:
        print(f"Menguji proxy: {proxy}")
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument(f'--proxy-server=http://{proxy}')
        
        driver = None
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_page_load_timeout(10)
            
            start_time = time.time()
            driver.get(test_url)
            response_time = time.time() - start_time
            
            if "Google" in driver.title:
                working_proxies.append({
                    "proxy": proxy,
                    "response_time": round(response_time, 2)
                })
                print(f"✓ Proxy berfungsi! Response time: {round(response_time, 2)}s")
            else:
                print("✗ Proxy tidak berfungsi (halaman salah)")
        except Exception as e:
            print(f"✗ Proxy error: {str(e)}")
        finally:
            if driver:
                driver.quit()
    
    return working_proxies

def main():
    # Kata kunci yang akan dicari
    keyword = "restoran jakarta"
    
    # Uji semua proxy terlebih dahulu
    print("Menguji daftar proxy...")
    working_proxies = test_proxies()
    
    if not working_proxies:
        print("Tidak ada proxy yang berfungsi! Menggunakan tanpa proxy...")
        # Gunakan tanpa proxy sebagai fallback
        results = scrape_google_maps(keyword, None)
    else:
        # Pilih proxy terbaik (tercepat)
        best_proxy = min(working_proxies, key=lambda x: x["response_time"])
        print(f"Menggunakan proxy terbaik: {best_proxy['proxy']} ({best_proxy['response_time']}s)")
        
        # Lakukan scraping
        results = scrape_google_maps(keyword, best_proxy['proxy'])
    
    # Simpan hasil ke file JSON
    filename = f"gmaps_{keyword.replace(' ', '_')}_{int(time.time())}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"Hasil disimpan ke {filename}")

if __name__ == "__main__":
    main()