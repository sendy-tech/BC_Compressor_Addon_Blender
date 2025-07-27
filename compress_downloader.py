import os
import urllib.request

TEXCONV_URL = "https://github.com/microsoft/DirectXTex/releases/latest/download/texconv.exe"

def download_and_extract_texconv(addon_dir):
    bin_dir = os.path.join(addon_dir, "bin")
    os.makedirs(bin_dir, exist_ok=True)

    texconv_exe_path = os.path.join(bin_dir, "texconv.exe")
    if os.path.exists(texconv_exe_path):
        return True

    try:
        print("[BC Compressor] Скачивание texconv.exe...")
        urllib.request.urlretrieve(TEXCONV_URL, texconv_exe_path)
        print("[BC Compressor] texconv.exe успешно установлен.")
        return True

    except Exception as e:
        print(f"[BC Compressor] Ошибка при загрузке texconv: {e}")
        return False
