import os
import re
import requests
import urllib3
from datetime import datetime, timedelta, timezone

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

GIST_ID = "b4674e2547e2720e4c7d27fdeebc0591"
GIST_FILENAME = "gistfile1.txt"

SOURCES = [
    {"url": "https://raptorcloudb.com", "prefix": "Raptor_"},
    {"url": "https://miacloud99.com", "prefix": "Mia_"},
    {"url": "https://nexacloudb.com", "prefix": "Nexa_"},
    {"url": "https://cloudjeto.com", "prefix": "Veenox_"}
]

def log_msg(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def process_links(raw_text, prefix):
    found = re.findall(r'vless://[^\s"\\]+', raw_text)
    processed = []
    for link in found:
        new_link = link.replace("6e9", "9e6")
        new_link = re.sub(r'[?&]alpn=[^&]+', '', new_link)
        new_link = new_link.replace('?&', '?').replace('&&', '&')
        if new_link.endswith('?'): new_link = new_link[:-1]
        
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

    all_final_links = []
    headers = {"User-Agent": "okhttp/4.9.0"}
    
    for source in SOURCES:
        try:
            response = requests.get(source['url'], headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            all_final_links.extend(process_links(response.text, source['prefix']))
        except Exception as e:
            log_msg(f"⚠️ Ошибка {source['url']}: {e}")

    # Удаляем дубли и добавляем время
    all_final_links = list(dict.fromkeys(all_final_links))
    
    # ПРИНУДИТЕЛЬНОЕ ВРЕМЯ (УРАЛ UTC+5)
    ural_time = datetime.now(timezone(timedelta(hours=5))).strftime('%d.%m.%Y %H:%M:%S')
    header_line = f"vless://00000000-0000-0000-0000-000000000000@127.0.0.1:0?type=none#🕒_Ural_Time:_{ural_time}"
    all_final_links.insert(0, header_line)
    
    log_msg(f"DEBUG: Время в Gist будет: {ural_time}")

    # Отправка
    res = requests.patch(
        f"https://api.github.com/gists/{GIST_ID}",
        headers={"Authorization": f"token {token}"},
        json={"files": {GIST_FILENAME: {"content": "\n".join(all_final_links)}}}
    )
    
    if res.status_code == 200:
        log_msg("🎉 Успех!")
    else:
        log_msg(f"❌ Ошибка API: {res.status_code}")

if __name__ == "__main__":
    main()
