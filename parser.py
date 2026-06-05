import os
import re
import requests
import urllib3
from datetime import datetime

# Отключаем предупреждения об SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- НАСТРОЙКИ ---
GIST_ID = "b4674e2547e2720e4c7d27fdeebc0591"
GIST_FILENAME = "gistfile1.txt"

# Источники и их настройки
SOURCES = [
    {"url": "https://raptorcloudb.com", "prefix": "Raptor_"},
    {"url": "https://miacloud99.com", "prefix": "Mia_"},
    {"url": "https://nexacloudb.com", "prefix": "Nexa_"},
    {"url": "https://cloudjeto.com", "prefix": "Veenox_"}
]

def log_msg(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def process_links(raw_text, prefix):
    # 1. Ищем все vless ссылки
    found = re.findall(r'vless://[^\s"\\]+', raw_text)
    processed = []

    for link in found:
        # 2. Меняем в UUID строку "6e9" на "9e6"
        new_link = link.replace("6e9", "9e6")

        # 3. Удаляем alpn=...
        # Регулярка ищет alpn=, берет все символы до следующего & или конца строки
        new_link = re.sub(r'[?&]alpn=[^&]+', '', new_link)
        
        # Исправляем возможный двойной разделитель ?& или && после удаления
        new_link = new_link.replace('?&', '?')
        # Если alpn был первым параметром, после удаления может остаться ? в конце или &&
        new_link = new_link.replace('&&', '&')
        if new_link.endswith('?'):
            new_link = new_link[:-1]

        # 4. Добавляем префикс к названию (тегу после #)
        if "#" in new_link:
            base_url, tag = new_link.split("#", 1)
            new_link = f"{base_url}#{prefix}{tag}"
        else:
            new_link = f"{new_link}#{prefix}config"
            
        processed.append(new_link)
    
    return processed

def main():
    token = os.getenv("GIST_TOKEN")
    if not token:
        log_msg("❌ Ошибка: GIST_TOKEN не найден")
        return

    headers = {
        "User-Agent": "okhttp/4.9.0",
        "Accept": "application/json",
        "Connection": "Keep-Alive"
    }
    
    all_final_links = []

    for source in SOURCES:
        try:
            log_msg(f"🚀 Запрос к {source['url']}...")
            response = requests.get(source['url'], headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            
            links = process_links(response.text, source['prefix'])
            log_msg(f"✅ Получено из {source['url']}: {len(links)} ссылок")
            all_final_links.extend(links)
            
        except Exception as e:
            log_msg(f"⚠️ Ошибка при обработке {source['url']}: {e}")

    if not all_final_links:
        log_msg("❌ Ссылок не найдено ни в одном источнике")
        return

    # Удаляем дубликаты
    all_final_links = list(dict.fromkeys(all_final_links))

    # Обновление Gist
    log_msg(f"📤 Отправка {len(all_final_links)} ссылок в Gist...")
    gist_url = f"https://api.github.com/gists/{GIST_ID}"
    try:
        res = requests.patch(
            gist_url,
            headers={"Authorization": f"token {token}", "Content-Type": "application/json"},
            json={"files": {GIST_FILENAME: {"content": "\n".join(all_final_links)}}}
        )
        
        if res.status_code == 200:
            log_msg("🎉 Gist успешно обновлен!")
        else:
            log_msg(f"❌ Ошибка Gist API: {res.status_code} - {res.text}")
    except Exception as e:
        log_msg(f"❌ Ошибка GitHub: {e}")

if __name__ == "__main__":
    main()
