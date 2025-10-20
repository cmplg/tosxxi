# automation.py
import os
import time
import re
from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image, ImageDraw, ImageFont

def add_warning_text_to_image(image_path, text):
    try:
        img = Image.open(image_path); draw = ImageDraw.Draw(img)
        try: font = ImageFont.truetype("DejaVuSans-Bold.ttf", size=32)
        except IOError: font = ImageFont.load_default()
        posisi = (15, 15); text_color = "yellow"; background_color = "red"
        bbox = draw.textbbox(posisi, text, font=font); padding = 5
        rect_pos = (bbox[0] - padding, bbox[1] - padding, bbox[2] + padding, bbox[3] + padding)
        draw.rectangle(rect_pos, fill=background_color)
        draw.text(posisi, text, font=font, fill=text_color)
        img.save(image_path); return True
    except Exception as e:
        print(f"GAGAL menambahkan teks ke gambar: {e}"); return False

def find_red_log_labels(driver):
    red_labels = []
    try:
        red_cells = driver.find_elements(By.XPATH, "//td[contains(@style, 'color: red')] | //font[@color='red']/ancestor::td")
        for cell in red_cells:
            try:
                parent_row = cell.find_element(By.XPATH, "./ancestor::tr")
                label_cell = parent_row.find_element(By.XPATH, "./td[4]")
                label_text = label_cell.text.strip()
                if label_text and label_text not in red_labels: red_labels.append(label_text)
            except Exception: continue
    except Exception as e: print(f"Error saat mencari label merah: {e}")
    return red_labels

def take_screenshot(url, save_path, studio_name, status_callback):
    status_callback(f"Memproses: {studio_name} ({url})...")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless"); options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage"); options.add_argument("window-size=1920,1080")
    options.page_load_strategy = 'normal'
    
    driver = None
    try:
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(5)
        driver.get(url)
        
        status_callback(f"Mencari link 'Log' di {studio_name}...")
        log_button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.LINK_TEXT, "Log")))
        log_button.click()
        status_callback("Link 'Log' berhasil diklik.")
        time.sleep(5)
        
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        try:
            status_callback(f"Menunggu data log dimuat...")
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//table/tbody/tr")))
            
            status_callback(f"Memfilter log untuk tanggal {today_str}...")
            driver.find_element(By.XPATH, f"//*[contains(text(), '{today_str}')]")
            
            js_script = """
            var dateToKeep = arguments[0];
            var allRows = document.querySelectorAll('table tr');
            allRows.forEach(function(row) {
                if (row.cells && row.cells.length > 0 && !row.querySelector('th')) {
                    var safeTextContent = JSON.stringify(row.textContent);
                    if (!safeTextContent.includes(dateToKeep)) {
                        row.style.display = 'none';
                    }
                }
            });
            """
            driver.execute_script(js_script, today_str)
            status_callback("Log berhasil difilter.")
            time.sleep(1)
            
            total_height = driver.execute_script("return document.body.scrollHeight")
            screenshot_height = max(1080, total_height + 150)
            driver.set_window_size(1920, screenshot_height)
            status_callback(f"Menyesuaikan tinggi screenshot menjadi {screenshot_height}px.")
            time.sleep(2)
            
        except (NoSuchElementException, TimeoutException):
            status_callback(f"INFO: Tidak ada log yang ditemukan untuk tanggal {today_str} di {studio_name}")
            return "NO_LOGS", None
            
        safe_studio_name = re.sub(r'[\s/\\:*?"<>|()]', '_', studio_name)
        filename_base = f"{safe_studio_name}_{today_str}"
        screenshot_path = os.path.join(save_path, f"{filename_base}.png")
        
        driver.save_screenshot(screenshot_path)
        status_callback(f"Screenshot disimpan di: {os.path.basename(screenshot_path)}")
        
        red_logs = find_red_log_labels(driver)
        
        if red_logs:
            labels_str = ", ".join(red_logs)
            status_callback(f"PERINGATAN: Log merah terdeteksi pada: {labels_str}")
            warning_text = f"Terdapat log merah pada: {labels_str}"
            add_warning_text_to_image(screenshot_path, warning_text)
            new_path = os.path.join(save_path, f"WARNING_RED_{filename_base}.png")
            os.rename(screenshot_path, new_path)
            status_callback(f"File diubah namanya menjadi: {os.path.basename(new_path)}")
            return "WARNING", labels_str
        else:
            status_callback("Analisis selesai. Tidak ada log merah ditemukan.")
            return "SUCCESS", None

    except TimeoutException:
        status_callback(f"ERROR: Gagal menemukan link 'Log' di {studio_name} dalam waktu 20 detik.")
        return "ERROR", "Timeout saat mencari link Log"
    except Exception as e:
        status_callback(f"ERROR: Terjadi kesalahan tak terduga saat memproses {studio_name} - {e}")
        return "ERROR", str(e)
    finally:
        if driver:
            driver.quit()