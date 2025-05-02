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
    # Tidak menggunakan mode headless agar bisa melihat browser
    chrome_options.add_argument('--start-maximized')  # Browser fullscreen
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument(f'--proxy-server=http://{proxy_address}')
    
    # Tambahkan window size yang cukup besar
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Konfigurasi service
    service = Service(ChromeDriverManager().install())
    
    # Inisialisasi driver
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    results = []
    
    try:
        # Buka Google Maps dengan keyword pencarian
        driver.get(f'https://www.google.com/maps/search/{keyword}/')
        print(f"Mencari: {keyword}")
        
        # Tambahkan delay agar Anda bisa melihat proses loading
        time.sleep(3)
        
        # Tunggu hingga halaman dimuat
        try:
            # Jika ada dialog atau popup, coba klik
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "form:nth-child(2)"))).click()
            print("Popup diklik")
        except Exception as e:
            print(f"Tidak ada popup atau error: {e}")
        
        # Tunggu feed hasil pencarian muncul
        try:
            print("Menunggu hasil pencarian dimuat...")
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="feed"]')))
            
            # Ambil div yang bisa di-scroll
            scrollable_div = driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
            
            # Scroll ke bawah untuk memuat lebih banyak hasil
            print("Scrolling untuk memuat lebih banyak hasil...")
            for i in range(3):  # Scroll 3 kali
                print(f"Scroll ke-{i+1}")
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
                time.sleep(3)  # Delay lebih lama agar bisa melihat proses scrolling
            
            # Tunggu sebentar setelah scrolling
            time.sleep(2)
            
            # Ambil semua item hasil pencarian
            items = driver.find_elements(By.CSS_SELECTOR, 'div[role="feed"] > div > div')
            print(f"Ditemukan {len(items)} hasil")
            
            # Highlight elemen yang diproses dengan JS untuk visualisasi
            highlight_js = """
            var original_style = arguments[0].getAttribute('style') || '';
            arguments[0].setAttribute('style', original_style + '; border: 2px solid red; background: yellow; padding: 2px;');
            setTimeout(function(){ 
                arguments[0].setAttribute('style', original_style); 
            }, 1000);
            """
            
            # Proses setiap item
            for i, item in enumerate(items):
                print(f"Memproses item {i+1}/{len(items)}")
                data = {}
                
                # Highlight item yang sedang diproses
                driver.execute_script(highlight_js, item)
                time.sleep(0.5)  # Beri waktu untuk melihat highlight
                
                try:
                    # Ambil judul/nama tempat
                    title_element = item.find_element(By.CSS_SELECTOR, ".fontHeadlineSmall")
                    data['title'] = title_element.text
                    print(f"  Judul: {data['title']}")
                except Exception as e:
                    print(f"  Error judul: {e}")
                    continue  # Skip jika tidak ada judul
                
                try:
                    # Ambil link Google Maps
                    link_element = title_element.find_element(By.XPATH, "./ancestor::a")
                    data['link'] = link_element.get_attribute('href')
                    print(f"  Link: {data['link'][:50]}...")
                except Exception as e:
                    print(f"  Error link: {e}")
                
                try:
                    # Ambil rating dan jumlah review
                    rating_element = item.find_element(By.CSS_SELECTOR, 'span[aria-label][role="img"]')
                    rating_text = rating_element.get_attribute('aria-label')
                    rating_match = re.search(r'([0-9]+[.,][0-9]+)', rating_text)
                    reviews_match = re.search(r'([0-9]+) review', rating_text)
                    
                    if rating_match:
                        data['rating'] = float(rating_match.group(1).replace(',', '.'))
                        print(f"  Rating: {data['rating']}")
                    if reviews_match:
                        data['reviews'] = int(reviews_match.group(1))
                        print(f"  Reviews: {data['reviews']}")
                except Exception as e:
                    print(f"  Error rating: {e}")
                
                try:
                    # Ambil text content untuk nomor telepon dan alamat
                    text_content = item.text
                    
                    # Pattern untuk nomor telepon Indonesia
                    phone_pattern = r'(\+62[ -]?[0-9]{1,3}[ -]?[0-9]{1,4}[ -]?[0-9]{1,4}|0[0-9]{1,3}[ -]?[0-9]{1,4}[ -]?[0-9]{1,4})'
                    phone_match = re.search(phone_pattern, text_content)
                    if phone_match:
                        data['phone'] = phone_match.group(0)
                        print(f"  Telepon: {data['phone']}")
                    
                    # Coba temukan alamat (pendekatan sederhana)
                    lines = text_content.split('\n')
                    for line in lines:
                        if ',' in line and len(line) > 10 and not line.startswith(('Buka', 'Tutup', 'Open')):
                            data['address'] = line
                            print(f"  Alamat: {data['address']}")
                            break
                except Exception as e:
                    print(f"  Error mencari telepon/alamat: {e}")
                
                results.append(data)
                print("-" * 40)  # Pembatas antar item
            
            print(f"Berhasil mengambil data dari {len(results)} tempat")
            
            # Beri waktu untuk melihat hasil sebelum menutup browser
            print("Menunggu 10 detik sebelum menutup browser...")
            time.sleep(10)
            
        except Exception as e:
            print(f"Error saat memproses hasil: {str(e)}")
    
    except Exception as e:
        print(f"Error saat mengakses Google Maps: {str(e)}")
    
    finally:
        # Tutup browser
        print("Menutup browser...")
        driver.quit()
    
    return results

def main():
    # Kata kunci yang akan dicari
    keyword = "wisata dekat danau toba"
    
    # Pilih proxy secara acak dari daftar
    proxy = random.choice(proxy_list)
    print(f"Proxy yang dipilih: {proxy}")
    
    # Lakukan scraping
    print("Memulai proses scraping...")
    results = scrape_google_maps(keyword, proxy)
    
    # Simpan hasil ke file JSON
    filename = f"gmaps_{keyword.replace(' ', '_')}_{int(time.time())}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"Hasil disimpan ke {filename}")
    print("Proses selesai!")

if __name__ == "__main__":
    main()