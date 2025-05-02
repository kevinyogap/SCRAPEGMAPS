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
from urllib.parse import urlparse, parse_qs

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

def extract_coordinates(link):
    """
    Fungsi untuk mengekstrak koordinat (latitude, longitude) dari URL Google Maps
    """
    try:
        parsed_url = urlparse(link)
        query_params = parse_qs(parsed_url.query)
        
        # Biasanya koordinat ada di parameter 'q' dalam bentuk "latitude,longitude"
        if 'q' in query_params:
            coords = query_params['q'][0].split(',')
            if len(coords) == 2:
                latitude = float(coords[0])
                longitude = float(coords[1])
                return latitude, longitude
    except Exception as e:
        print(f"Error saat mengekstrak koordinat: {e}")
    
    return None, None

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
            
            # Set variabel untuk melacak jumlah hasil sebelumnya
            previous_count = 0
            same_count_iterations = 0
            max_same_count = 3  # Berhenti jika jumlah hasil sama selama 3 iterasi berturut-turut
            
            print("Memulai infinite scrolling...")
            while True:
                # Scroll ke bawah
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
                print("Scrolling ke bawah...")
                
                # Tunggu hasil baru dimuat
                time.sleep(3)
                
                # Ambil semua item saat ini
                items = driver.find_elements(By.CSS_SELECTOR, 'div.Nv2PK')
                current_count = len(items)
                
                print(f"Jumlah item saat ini: {current_count}")
                
                # Cek apakah ada item baru yang dimuat
                if current_count == previous_count:
                    same_count_iterations += 1
                    print(f"Tidak ada item baru yang dimuat. Percobaan ke-{same_count_iterations}/{max_same_count}")
                    
                    # Jika sudah beberapa kali tidak ada hasil baru, berarti sudah sampai bawah
                    if same_count_iterations >= max_same_count:
                        print("Sudah mencapai akhir hasil. Berhenti scrolling.")
                        break
                else:
                    # Reset counter jika ada item baru
                    same_count_iterations = 0
                    print(f"Ditemukan {current_count - previous_count} item baru")
                
                previous_count = current_count
            
            # Ambil semua item hasil pencarian setelah scrolling
            items = driver.find_elements(By.CSS_SELECTOR, 'div.Nv2PK')
            print(f"Total ditemukan {len(items)} hasil setelah infinite scrolling")
            
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
                    # Ambil judul/nama tempat
                    title_element = item.find_element(By.CSS_SELECTOR, ".qBF1Pd.fontHeadlineSmall")
                    data['title'] = title_element.text
                    print(f"  Judul: {data['title']}")
                except Exception as e:
                    print(f"  Error judul: {e}")
                    continue  # Skip jika tidak ada judul
                
                try:
                    # Ambil link Google Maps
                    link_element = item.find_element(By.CSS_SELECTOR, "a.hfpxzc")
                    data['link'] = link_element.get_attribute('href')
                    print(f"  Link: {data['link'][:50]}...")
                    
                    # Ekstrak koordinat dari link
                    latitude, longitude = extract_coordinates(data['link'])
                    data['latitude'] = latitude
                    data['longitude'] = longitude
                    print(f"  Koordinat: {latitude}, {longitude}")
                except Exception as e:
                    print(f"  Error link: {e}")
                
                results.append(data)
                print("-" * 40)  # Pembatas antar item
            
            print(f"Berhasil mengambil data dari {len(results)} tempat")
            
            # Beri waktu untuk melihat hasil sebelum menutup browser
            print("Menunggu 5 detik sebelum menutup browser...")
            time.sleep(5)
            
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
    keyword = "wisata dekat danau toba"  # Keyword pencarian
    
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
