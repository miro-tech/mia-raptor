import os
import json
import base64
import requests
import uuid
from datetime import datetime
from Crypto.Cipher import AES

# --- НАСТРОЙКИ ---
GIST_ID = "b4674e2547e2720e4c7d27fdeebc0591"
GIST_FILENAME = "gistfile1.txt"
API_BASE = "https://api.xbs54as9c6.ru"
USER_AGENT = "v1.7.7 Android/34 Samsung Galaxy S24"
API_AES_KEY = "fd9840a6e1f3c2a1ca6e55112679232add28c725dcfae34972db0c6a0e13cfaf"

SERVER_IPS = {
    'yy.xbs54as9c6.ru': {'selective': '158.160.5.176', 'fulltunnel': '46.243.211.17'},
    'tn.xbs54as9c6.ru': {'selective': '217.149.25.86', 'fulltunnel': '72.56.38.52'},
    'tg.xbs54as9c6.ru': {'selective': '141.105.66.189', 'fulltunnel': '91.218.245.82'}
}

def log_msg(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def decrypt_config(data_b64):
    encrypted = base64.b64decode(data_b64)
    nonce = encrypted[:12]
    ciphertext_with_tag = encrypted[12:]
    tag = ciphertext_with_tag[-16:]
    ciphertext = ciphertext_with_tag[:-16]
    
    key = bytes.fromhex(API_AES_KEY)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    try:
        decrypted = cipher.decrypt_and_verify(ciphertext, tag)
        return json.loads(decrypted)
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
