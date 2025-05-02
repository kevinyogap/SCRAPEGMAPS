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

def get_detail_info(driver, item, data):
    """
    Fungsi untuk mengklik tempat dan mendapatkan informasi detail alamat
    """
    try:
        print("  Mengklik tempat untuk mendapatkan detail...")
        
        # Simpan handle window utama
        main_window = driver.current_window_handle
        
        # Coba klik pada elemen (kadang butuh scroll untuk memastikan elemen terlihat)
        try:
            # Scroll ke elemen
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item)
            time.sleep(1)
            
            # Highlight item yang akan diklik
            highlight_js = """
            var original_style = arguments[0].getAttribute('style') || '';
            arguments[0].setAttribute('style', original_style + '; border: 3px solid blue; background: rgba(0, 0, 255, 0.1);');
            """
            driver.execute_script(highlight_js, item)
            
            # Klik item
            item.click()
            print("  Item berhasil diklik")
        except Exception as e:
            print(f"  Error saat klik langsung: {e}")
            try:
                # Alternatif: klik link dalam item
                link = item.find_element(By.CSS_SELECTOR, "a.hfpxzc")
                driver.execute_script("arguments[0].click();", link)
                print("  Link berhasil diklik via JavaScript")
            except Exception as e2:
                print(f"  Error saat klik link: {e2}")
                return data  # Return data yang sudah ada jika gagal klik
        
        # Tunggu panel detail muncul (panel kanan)
        print("  Menunggu panel detail muncul...")
        detail_panel = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.m6QErb.DxyBCb.kA9KIf.dS8AEf"))
        )
        print("  Panel detail ditemukan")
        
        # Tunggu sedikit agar konten dimuat
        time.sleep(2)
        
        # Ambil alamat lengkap
        try:
            # Coba cari alamat di panel info (biasanya di bawah nama tempat)
            address_containers = driver.find_elements(By.CSS_SELECTOR, "div.Io6YTe")
            
            for container in address_containers:
                # Cek apakah ini elemen alamat dengan mencari icon lokasi di dekatnya
                parent = container.find_element(By.XPATH, "./..")
                if "fontBodyMedium" in container.get_attribute("class") and "AeaXub" in parent.get_attribute("class"):
                    data['address'] = container.text.strip()
                    print(f"  Alamat lengkap: {data['address']}")
                    break
                    
            # Alternatif: jika tidak menemukan alamat dengan cara di atas
            if 'address' not in data:
                # Coba cara kedua: button copy address
                address_button = driver.find_element(By.CSS_SELECTOR, "button[data-item-id='address']")
                if address_button:
                    # Ambil aria-label yang berisi alamat lengkap
                    data['address'] = address_button.get_attribute("aria-label").replace("Copy address: ", "")
                    print(f"  Alamat lengkap (dari button): {data['address']}")
            
            # Alternatif ketiga: cari div dengan class tertentu
            if 'address' not in data:
                address_div = driver.find_element(By.CSS_SELECTOR, "div.rogA2c div.fontBodyMedium")
                if address_div:
                    data['address'] = address_div.text.strip()
                    print(f"  Alamat lengkap (dari div): {data['address']}")
                    
        except Exception as e:
            print(f"  Error saat mengambil alamat lengkap: {e}")
            
        # Ambil informasi tambahan lainnya jika diperlukan
        try:
            # Cek apakah ada nomor telepon
            try:
                phone_button = driver.find_element(By.CSS_SELECTOR, "button[data-item-id='phone:tel']")
                if phone_button:
                    data['phone'] = phone_button.get_attribute("aria-label").replace("Copy phone number: ", "")
                    print(f"  Nomor telepon: {data['phone']}")
            except:
                # Cara alternatif mencari nomor telepon
                phone_elements = driver.find_elements(By.CSS_SELECTOR, "div.Io6YTe")
                for el in phone_elements:
                    if re.search(r'\+\d[\d\s-]{8,}', el.text):  # Pola nomor telepon
                        data['phone'] = el.text.strip()
                        print(f"  Nomor telepon: {data['phone']}")
                        break
            
            # Cek apakah ada website
            try:
                website_button = driver.find_element(By.CSS_SELECTOR, "a[data-item-id='authority']")
                if website_button:
                    data['website'] = website_button.get_attribute("href")
                    print(f"  Website: {data['website']}")
            except:
                pass
            
            # Cek jam operasional detail
            try:
                # Klik tombol untuk melihat jam operasional lengkap jika ada
                hours_button = driver.find_element(By.CSS_SELECTOR, "button[jsaction*='hours;']")
                if hours_button:
                    driver.execute_script("arguments[0].click();", hours_button)
                    time.sleep(1)
                    
                    # Ambil tabel jam operasional
                    hours_table = driver.find_element(By.CSS_SELECTOR, "table.eK4R0e")
                    rows = hours_table.find_elements(By.TAG_NAME, "tr")
                    
                    operating_hours = {}
                    for row in rows:
                        try:
                            day = row.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text
                            hours = row.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text
                            operating_hours[day] = hours
                        except:
                            continue
                    
                    data['detailed_hours'] = operating_hours
                    print(f"  Jam operasional detail diambil: {len(operating_hours)} hari")
                    
                    # Tutup dialog jam operasional
                    close_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Close']")
                    driver.execute_script("arguments[0].click();", close_button)
                    time.sleep(1)
            except Exception as e:
                print(f"  Error saat mengambil jam operasional detail: {e}")
                
            # Coba ambil koordinat
            try:
                # Koordinat biasanya ada di URL
                current_url = driver.current_url
                coords_match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', current_url)
                if coords_match:
                    data['latitude'] = float(coords_match.group(1))
                    data['longitude'] = float(coords_match.group(2))
                    print(f"  Koordinat: {data['latitude']}, {data['longitude']}")
            except Exception as e:
                print(f"  Error saat mengambil koordinat: {e}")
                
        except Exception as e:
            print(f"  Error saat mengambil info tambahan: {e}")
            
        # Kembali ke hasil pencarian
        print("  Kembali ke hasil pencarian...")
        driver.back()
        
        # Tunggu hasil pencarian dimuat kembali
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="feed"]'))
        )
        time.sleep(2)  # Beri waktu tambahan untuk memastikan halaman dimuat sempurna
        
    except Exception as e:
        print(f"  Error saat mendapatkan detail: {e}")
        # Pastikan kembali ke hasil pencarian jika terjadi error
        try:
            driver.back()
            time.sleep(2)
        except:
            print("  Gagal kembali ke hasil pencarian")
    
    return data

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
            
            # Batasi jumlah hasil yang akan diproses untuk testing
            max_results = 100000  # Ubah sesuai kebutuhan, gunakan angka kecil untuk testing
            
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
                
                # Jika sudah cukup banyak hasil untuk testing, hentikan scrolling
                if current_count >= max_results:
                    print(f"Sudah terkumpul {current_count} hasil (batas: {max_results}). Menghentikan scrolling.")
                    break
                
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
            
            # Batasi jumlah item yang akan diproses (untuk testing)
            items = items[:max_results]
            print(f"Akan memproses {len(items)} item pertama")
            
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
                except Exception as e:
                    print(f"  Error link: {e}")
                
                try:
                    # Ambil gambar
                    img_element = item.find_element(By.CSS_SELECTOR, "img[src^='https://lh3.googleusercontent.com']")
                    img_url = img_element.get_attribute('src')
                    data['image_url'] = img_url
                    print(f"  URL Gambar: {img_url[:50]}...")
                    
                    # # Download gambar
                    # if img_url:
                    #     img_path = download_image(img_url, images_folder, data['title'])
                    #     if img_path:
                    #         data['local_image_path'] = img_path
                except Exception as e:
                    print(f"  Error gambar: {e}")
                
                try:
                    # Ambil rating dan jumlah review
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
                    # Ambil waktu buka/tutup
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
                
                # Sekarang ambil detail dengan klik pada item
                data = get_detail_info(driver, item, data)
                
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