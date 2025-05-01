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
import os
import requests
from urllib.parse import urlparse

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

def download_image(img_url, destination_folder, place_name):
    """
    Fungsi untuk mengunduh gambar dari URL dan menyimpannya
    """
    try:
        # Membuat folder jika belum ada
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)
            
        # Membersihkan nama file dari karakter yang tidak valid
        clean_name = re.sub(r'[\\/*?:"<>|]', "", place_name)
        
        # Mendapatkan ekstensi file dari URL
        parsed_url = urlparse(img_url)
        path = parsed_url.path
        file_extension = os.path.splitext(path)[1]
        
        # Jika tidak ada ekstensi, gunakan .jpg sebagai default
        if not file_extension:
            file_extension = ".jpg"
            
        # Membuat nama file unik
        file_name = f"{clean_name}_{int(time.time())}{file_extension}"
        file_path = os.path.join(destination_folder, file_name)
        
        # Mengunduh gambar
        response = requests.get(img_url, stream=True)
        if response.status_code == 200:
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            print(f"  Gambar berhasil disimpan: {file_path}")
            return file_path
        else:
            print(f"  Gagal mengunduh gambar. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"  Error saat mengunduh gambar: {e}")
        return None

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
    images_folder = "gmaps_images"
    
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
            
            # Ambil semua item hasil pencarian - berdasarkan struktur HTML yang Anda bagikan
            items = driver.find_elements(By.CSS_SELECTOR, 'div.Nv2PK')
            print(f"Ditemukan {len(items)} hasil")
            
            # Highlight elemen yang diproses dengan JS untuk visualisasi
            highlight_js = """
            var original_style = arguments[0].getAttribute('style') || '';
            arguments[0].setAttribute('style', original_style + '; border: 2px solid red; background: rgba(255, 255, 0, 0.3); padding: 2px;');
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
                    # Ambil judul/nama tempat - berdasarkan class yang Anda berikan
                    title_element = item.find_element(By.CSS_SELECTOR, ".qBF1Pd.fontHeadlineSmall")
                    data['title'] = title_element.text
                    print(f"  Judul: {data['title']}")
                except Exception as e:
                    print(f"  Error judul: {e}")
                    continue  # Skip jika tidak ada judul
                
                try:
                    # Ambil link Google Maps - berdasarkan selector yang Anda berikan
                    link_element = item.find_element(By.CSS_SELECTOR, "a.hfpxzc")
                    data['link'] = link_element.get_attribute('href')
                    print(f"  Link: {data['link'][:50]}...")
                except Exception as e:
                    print(f"  Error link: {e}")
                
                try:
                    # Ambil gambar
                    img_element = item.find_element(By.CSS_SELECTOR, "img[src^='https://lh3.googleusercontent.com']")
                    img_url = img_element.get_attribute('src')
                    data['image_url'] = img_url
                    print(f"  URL Gambar: {img_url[:50]}...")
                    
                    # Download gambar
                    if img_url:
                        img_path = download_image(img_url, images_folder, data['title'])
                        if img_path:
                            data['local_image_path'] = img_path
                except Exception as e:
                    print(f"  Error gambar: {e}")
                
                try:
                    # Ambil rating dan jumlah review - berdasarkan struktur yang Anda berikan
                    rating_element = item.find_element(By.CSS_SELECTOR, 'span.ZkP5Je[role="img"]')
                    aria_label = rating_element.get_attribute('aria-label')
                    print(f"  Rating text: {aria_label}")
                    
                    # Ekstrak rating dari aria-label atau dari span.MW4etd
                    try:
                        rating_span = rating_element.find_element(By.CSS_SELECTOR, 'span.MW4etd')
                        data['rating'] = float(rating_span.text.replace(',', '.'))
                    except:
                        # Jika tidak bisa mengambil dari span, ekstrak dari aria-label
                        rating_match = re.search(r'([0-9]+[.,][0-9]+)', aria_label)
                        if rating_match:
                            data['rating'] = float(rating_match.group(1).replace(',', '.'))
                    
                    # Ekstrak jumlah review dari aria-label atau dari span.UY7F9
                    try:
                        review_span = rating_element.find_element(By.CSS_SELECTOR, 'span.UY7F9')
                        review_text = review_span.text.strip('()')
                        data['reviews'] = int(review_text)
                    except:
                        # Jika tidak bisa mengambil dari span, ekstrak dari aria-label
                        reviews_match = re.search(r'([0-9]+) Reviews', aria_label)
                        if reviews_match:
                            data['reviews'] = int(reviews_match.group(1))
                    
                    print(f"  Rating: {data.get('rating', 'N/A')}")
                    print(f"  Reviews: {data.get('reviews', 'N/A')}")
                except Exception as e:
                    print(f"  Error rating: {e}")
                
                try:
                    # Ambil alamat - berdasarkan struktur yang Anda berikan
                    # Cari alamat dalam span setelah bullet point (·)
                    address_spans = item.find_elements(By.CSS_SELECTOR, '.W4Efsd span')
                    for i in range(len(address_spans) - 1):
                        if address_spans[i].text == '·' and i+1 < len(address_spans):
                            data['address'] = address_spans[i+1].text
                            print(f"  Alamat: {data['address']}")
                            break
                except Exception as e:
                    print(f"  Error alamat: {e}")
                
                try:
                    # Ambil waktu buka/tutup - berdasarkan struktur yang Anda berikan
                    open_time_element = item.find_element(By.CSS_SELECTOR, 'span[style*="color: rgba(25,134,57"]')
                    data['opening_hours'] = open_time_element.text
                    print(f"  Jam buka: {data['opening_hours']}")
                except Exception as e:
                    try:
                        # Coba cara alternatif untuk mencari waktu buka
                        spans = item.find_elements(By.CSS_SELECTOR, '.W4Efsd span')
                        for span in spans:
                            if 'Open' in span.text or 'Closed' in span.text or 'Buka' in span.text or 'Tutup' in span.text:
                                data['opening_hours'] = span.text
                                print(f"  Jam buka: {data['opening_hours']}")
                                break
                    except Exception as sub_e:
                        print(f"  Error jam buka: {e}, {sub_e}")
                
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
    keyword = "wisata dekat danau toba"  # Anda bisa ganti sesuai kebutuhan
    
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