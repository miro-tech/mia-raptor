import os
import re
import requests
import urllib3
from datetime import datetime

# Отключаем предупреждения об SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

GIST_ID = "b4674e2547e2720e4c7d27fdeebc0591"
GIST_FILENAME = "gistfile1.txt"
TARGET_URL = "https://miacloud99.com"

def fetch_and_update():
    token = os.getenv("GIST_TOKEN")
    if not token:
        print("❌ Ошибка: GIST_TOKEN не найден")
        return

    headers = {
        "User-Agent": "okhttp/4.9.0",
        "Accept": "application/json"
    }
    
    print(f"🚀 Запрос к {TARGET_URL}...")
    try:
        # Прямой запрос к сайту без регистрации
        response = requests.get(TARGET_URL, headers=headers, timeout=30, verify=False)
        # Если сайт вернул данные, ищем vless ссылки
        links = re.findall(r'vless://[^\s"\\]+', response.text)
        links = list(dict.fromkeys(links)) # Удаляем дубли
        
        if not links:
            print("❌ Ссылок vless не найдено")
            return

        print(f"✅ Найдено ссылок: {len(links)}")
        
        # Отправка в Gist
        gist_url = f"https://api.github.com/gists/{GIST_ID}"
        res = requests.patch(
            gist_url,
            headers={"Authorization": f"token {token}"},
            json={"files": {GIST_FILENAME: {"content": "\n".join(links)}}}
        )
        
        if res.status_code == 200:
            print("🎉 Gist успешно обновлен!")
        else:
            print(f"❌ Ошибка Gist API: {res.status_code}")

    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")

if __name__ == "__main__":
    fetch_and_update()
