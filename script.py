import os
import re
import requests
from datetime import datetime

# --- НАСТРОЙКИ ---
GIST_ID = "b4674e2547e2720e4c7d27fdeebc0591"
GIST_FILENAME = "gistfile1.txt"
TARGET_URL = "https://miacloud99.com"

def log_msg(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def fetch_and_update():
    # Получаем токен из переменных окружения (для GitHub Actions)
    token = os.getenv("GIST_TOKEN")
    if not token:
        log_msg("Ошибка: GIST_TOKEN не найден в секретах репозитория")
        return

    # 1. Запрос к сайту (имитация вашего curl)
    headers = {
        "User-Agent": "okhttp/4.9.0",
        "Accept": "application/json",
        "Connection": "Keep-Alive"
    }
    
    try:
        log_msg(f"Запрос к {TARGET_URL}...")
        # verify=False добавлен на случай проблем с SSL, как в вашем curl -v
        response = requests.get(TARGET_URL, headers=headers, timeout=30, verify=False)
        response.raise_for_status()
        raw_data = response.text
    except Exception as e:
        log_msg(f"Ошибка при запросе к сайту: {e}")
        return

    # 2. Поиск ссылок vless
    links = re.findall(r'vless://[^\s"\\]+', raw_data)
    
    # Удаление дубликатов
    links = list(dict.fromkeys(links))
    
    if not links:
        log_msg("Ссылки vless не найдены в ответе сервера")
        return

    log_msg(f"Найдено уникальных ссылок: {len(links)}")

    # 3. Подготовка текста (чистые ссылки через новую строку)
    final_content = "\n".join(links)

    # 4. Обновление Gist
    gist_url = f"https://api.github.com/gists/{GIST_ID}"
    gist_headers = {
        "Authorization": f"token {token}",
        "Content-Type": "application/json",
        "User-Agent": "Python-Updater"
    }
    payload = {
        "files": {
            GIST_FILENAME: {"content": final_content}
        }
    }

    try:
        res = requests.patch(gist_url, json=payload, headers=gist_headers)
        if res.status_code == 200:
            log_msg("✅ Gist успешно обновлен чистыми ссылками!")
        else:
            log_msg(f"❌ Ошибка GitHub API: {res.status_code} - {res.text}")
    except Exception as e:
        log_msg(f"❌ Ошибка при отправке в GitHub: {e}")

if __name__ == "__main__":
    fetch_and_update()
