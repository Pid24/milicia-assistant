import os
import requests
import zipfile
import shutil

# Model English US kecil (~40MB). Meskipun asisten berbahasa Indonesia,
# wake word "Milicia" cukup dekat dengan kata English "militia" sehingga
# model ini bisa mendeteksinya. Matching dilakukan secara fonetik di voice.py.
MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
MODEL_DIR = "vosk_model"
ZIP_PATH = "vosk_temp.zip"

def download_and_extract():
    if os.path.exists(MODEL_DIR):
        print(f"Folder '{MODEL_DIR}' sudah ada. Lewati unduhan.")
        return

    print("Mengunduh Vosk Speech Model (sekitar 40MB)...")
    try:
        response = requests.get(MODEL_URL, stream=True)
        response.raise_for_status()
        
        with open(ZIP_PATH, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print("Unduhan selesai! Mengekstrak file...")
        
        with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
            zip_ref.extractall(".")
            
        extracted_folder = "vosk-model-small-en-us-0.15"
        if os.path.exists(extracted_folder):
            os.rename(extracted_folder, MODEL_DIR)
            
        if os.path.exists(ZIP_PATH):
            os.remove(ZIP_PATH)
        print("Instalasi sistem Telinga Offline (Vosk) Berhasil!")
        
    except Exception as e:
        print(f"Gagal mengunduh atau mengekstrak model: {e}")

if __name__ == "__main__":
    download_and_extract()
