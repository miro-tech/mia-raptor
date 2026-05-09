import os
import re
import requests
import base64
from datetime import datetime

# --- НАСТРОЙКИ ---
GIST_ID = "b4674e2547e2720e4c7d27fdeebc0591"
GIST_FILENAME = "gistfile1.txt"
TARGET_URL = "https://miacloud99.com"

def log_msg(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def fetch_and_update():
    token = os.getenv("GIST_TOKEN")
    if not token:
        log_msg("Ошибка: GIST_TOKEN не найден")
        return

    # 1. Выполняем запрос (аналог вашего curl)
    headers = {
        "User-Agent": "okhttp/4.9.0",
        "Accept": "application/json",
        "Connection": "Keep-Alive"
    }
    
    try:
        log_msg(f"Запрос к {TARGET_URL}...")
        response = requests.get(TARGET_URL, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.text
    except Exception as e:
        log_msg(f"Ошибка запроса: {e}")
        return

    # 2. Ищем vless ссылки (ваш регулярный запуск)
    links = re.findall(r'vless://[^\s"\\]+', data)
    
    # Очистка от дубликатов с сохранением порядка
    links = list(dict.fromkeys(links))
    
    if not links:
        log_msg("Ссылки vless не найдены в ответе")
        return

    log_msg(f"Найдено ссылок: {len(links)}")

    # 3. Формируем контент (чистые ссылки через перенос строки)
    # Если нужен Base64 (как в подписках), расскомментируйте нижнюю строку:
    # final_content = base64.b64encode("\n".join(links).encode()).decode()
    final_content = "\n".join(links)

    # 4. Обновляем Gist через GitHub API
    gist_url = f"https://api.github.com/gists/{GIST_ID}"
    gist_headers = {
        "Authorization": f"token {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "files": {
            GIST_FILENAME: {"content": final_content}
        }
    }

    res = requests.patch(gist_url, json=payload, headers=gist_headers)
    
    if res.status_code == 200:
        log_msg("Gist успешно обновлен!")
    else:
        log_msg(f"Ошибка GitHub API: {res.status_code} - {res.text}")

if __name__ == "__main__":
    fetch_and_update()
    except Exception as e:
        log_msg(f"Ошибка дешифровки: {e}")
        return None

def parse_config(config_json):
    links = []
    singbox = json.loads(config_json.get('singbox_config', '{}'))
    outbounds = singbox.get('outbounds', [])

    for out in outbounds:
        tag = out.get('tag', '')
        mode = 'selective' if 'selective' in tag else 'fulltunnel' if 'fulltunnel' in tag else None
        if not mode: continue

        domain = out.get('server', '')
        port = out.get('server_port', 443)
        if isinstance(port, list): port = port[0]
        
        # Определение IP
        ip = SERVER_IPS.get(domain, {}).get(mode, domain)
        
        if out['type'] == 'hysteria2':
            pw = out.get('password', '')
            sni = out.get('tls', {}).get('server_name', '')
            ins = '1' if out.get('tls', {}).get('insecure') else '0'
            links.append(f"hysteria2://{pw}@{ip}:{port}/?insecure={ins}&sni={sni}#{tag}")
            
        elif out['type'] == 'vless':
            uid = out.get('uuid', '')
            tls = out.get('tls', {})
            sni = tls.get('server_name', '')
            
            if 'reality' in tls:
                pbk = tls['reality'].get('public_key', '')
                sid = tls['reality'].get('short_id', '')
                links.append(f"vless://{uid}@{ip}:{port}?encryption=none&flow=xtls-rprx-vision&security=reality&sni={sni}&fp=chrome&pbk={pbk}&sid={sid}&type=tcp#{tag}")
            else:
                path = out.get('transport', {}).get('path', '')
                host = out.get('transport', {}).get('headers', {}).get('Host', '')
                links.append(f"vless://{uid}@{ip}:{port}?encryption=none&host={host}&path={path}&security=none&type=ws#{tag}")
    
    return list(set(links))

def main():
    token = os.getenv("GIST_TOKEN")
    if not token:
        log_msg("Ошибка: GIST_TOKEN не найден в секретах")
        return

    device_id = str(uuid.uuid4())
    headers = {'User-Agent': USER_AGENT, 'Content-Type': 'application/json'}
    
    # Регистрация
    reg = requests.post(f"{API_BASE}/api/v2/devices/access", 
                        json={"device_id": device_id, "device_token": ""}, 
                        headers=headers, verify=False)
    
    if reg.status_code != 200: return log_msg("Регистрация провалена")

    # Получение конфига
    conf_res = requests.get(f"{API_BASE}/api/config?device_id={device_id}", headers=headers, verify=False)
    if conf_res.status_code != 200: return log_msg("Конфиг не получен")
    
    data = decrypt_config(conf_res.json()['data'])
    if not data: return
    
    links = parse_config(data)
    if not links: return log_msg("Ссылок не найдено")

    # Обновление Gist
    content = base64.b64encode("\n".join(links).encode()).decode()
    gist_headers = {"Authorization": f"token {token}", "Content-Type": "application/json"}
    patch_data = {"files": {GIST_FILENAME: {"content": content}}}
    
    res = requests.patch(f"https://api.github.com/gists/{GIST_ID}", json=patch_data, headers=gist_headers)
    
    if res.status_code == 200:
        log_msg(f"Успешно! Обновлено {len(links)} конфигов.")
    else:
        log_msg(f"Ошибка Gist: {res.status_code}")

if __name__ == "__main__":
    main()
