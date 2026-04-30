import requests, uuid, base64, json, time, os
from Crypto.Cipher import AES

# =========================
# НАСТРОЙКИ
# =========================
API = "https://api.xbs54as9c6.ru"
KEY = bytes.fromhex("fd9840a6e1f3c2a1ca6e55112679232add28c725dcfae34972db0c6a0e13cfaf")

GIST_ID = "b4674e2547e2720e4c7d27fdeebc0591"
GIST_FILENAME = "gistfile1.txt"

# 👉 если запускаешь в Termux — вставь токен сюда
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") or "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"

SERVER_IPS = {
    "yy.xbs54as9c6.ru": "46.243.211.17",
    "st.xbs54as9c6.ru": "158.160.5.176",
    "vw.xbs54as9c6.ru": "84.201.128.244",
    "tn.xbs54as9c6.ru": "5.42.116.247",
    "tg.xbs54as9c6.ru": "141.105.66.189",
}

headers = {
    "User-Agent": "v1.7.7 Android/34 Samsung Galaxy S24",
    "Content-Type": "application/json"
}

# =========================
# ПОЛУЧЕНИЕ ССЫЛОК
# =========================
def get_links():
    print("🚀 START REQUEST")

    device_id = str(uuid.uuid4())

    # регистрация
    r1 = requests.post(
        API + "/api/v2/devices/access",
        json={"device_id": device_id, "device_token": ""},
        headers=headers,
        timeout=10
    )

    print("REGISTER STATUS:", r1.status_code)

    # получение конфига
    r2 = requests.get(
        API + "/api/config",
        params={"device_id": device_id},
        headers=headers,
        timeout=10
    )

    print("CONFIG STATUS:", r2.status_code)

    if r2.status_code != 200:
        print("❌ API ERROR:", r2.text)
        return []

    data = base64.b64decode(r2.json()["data"])

    # decrypt
    nonce = data[:12]
    tag = data[-16:]
    ciphertext = data[12:-16]

    cipher = AES.new(KEY, AES.MODE_GCM, nonce=nonce)
    cipher.update(b"android")

    decrypted = cipher.decrypt_and_verify(ciphertext, tag)
    config = json.loads(decrypted.decode())

    singbox = json.loads(config.get("singbox_config", "{}"))

    links = []

    for outbound in singbox.get("outbounds", []):
        tag = outbound.get("tag", "")
        if "selective" not in tag and "fulltunnel" not in tag:
            continue

        server = outbound.get("server", "")
        ip = SERVER_IPS.get(server, server)
        port = outbound.get("server_port", 443)
        if isinstance(port, list):
            port = port[0]

        # hysteria2
        if outbound.get("type") == "hysteria2":
            password = outbound.get("password", "")
            tls = outbound.get("tls", {})
            sni = tls.get("server_name", "")
            insecure = "1" if tls.get("insecure") else "0"

            links.append(f"hysteria2://{password}@{ip}:{port}/?insecure={insecure}&sni={sni}#{tag}")

        # vless
        elif outbound.get("type") == "vless":
            uuid_ = outbound.get("uuid", "")
            tls = outbound.get("tls", {})
            transport = outbound.get("transport", {})

            if tls and "reality" in tls:
                reality = tls["reality"]
                pbk = reality.get("public_key", "")
                sid = reality.get("short_id", "")
                sni = tls.get("server_name", "")

                links.append(
                    f"vless://{uuid_}@{ip}:{port}?encryption=none&flow=xtls-rprx-vision"
                    f"&security=reality&sni={sni}&fp=chrome&pbk={pbk}&sid={sid}"
                    f"&type=tcp&headerType=none#{tag}"
                )
            else:
                path = transport.get("path", "")
                host = transport.get("headers", {}).get("Host", "")

                links.append(
                    f"vless://{uuid_}@{ip}:{port}?encryption=none"
                    f"&host={host}&path={path}&security=none&type=ws#{tag}"
                )

    print(f"✅ НАЙДЕНО: {len(links)} конфигов")
    return links


# =========================
# ОБНОВЛЕНИЕ GIST
# =========================
def update_gist(content):
    print("📤 ОБНОВЛЕНИЕ GIST...")

    url = f"https://api.github.com/gists/{GIST_ID}"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "User-Agent": "vpn-updater"
    }

    data = {
        "files": {
            GIST_FILENAME: {
                "content": content
            }
        }
    }

    r = requests.patch(url, headers=headers, json=data, timeout=10)

    print("STATUS:", r.status_code)
    print("RESPONSE:", r.text[:200])

    return r.status_code == 200


# =========================
# MAIN
# =========================
if not GITHUB_TOKEN:
    print("❌ НЕТ GITHUB_TOKEN")
    exit(1)

links = get_links()

if not links:
    print("❌ Нет конфигов")
    exit(1)

sub = base64.b64encode("\n".join(links).encode()).decode()

if update_gist(sub):
    print("✅ GIST УСПЕШНО ОБНОВЛЁН")
else:
    print("❌ Ошибка загрузки в Gist")
