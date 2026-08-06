import os
import re
import requests
import urllib3
from datetime import datetime, timedelta, timezone

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

GIST_ID = "b4674e2547e2720e4c7d27fdeebc0591"
GIST_FILENAME = "gistfile1.txt"

SOURCES = [
    {
        "url": "https://drive.google.com/uc?export=download&id=1sAzCBwrh_3tz-7c5qu-ih6ULoJiJINWo",
        "prefix": "Zero_"
    },
    {
        "url": "https://drive.google.com/uc?export=download&id=1_kkDxYC1q1iybT-EttXL3Zp_9tHKLumR",
        "prefix": "Nexa_"
    },
    {"url": "https://airhost1.com", "prefix": "Mia_"},
    {"url": "https://miamain1.com", "prefix": "Mia_"},
    {"url": "https://miagit1.com", "prefix": "Mia_"}
]


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def process_links(text, prefix):
    links = re.findall(r'vless://[^\s"\\]+', text)

    result = []

    for link in links:
        link = link.replace("6e9", "9e6")
        link = re.sub(r'[?&]alpn=[^&]+', '', link)

        link = (
            link
            .replace("?&", "?")
            .replace("&&", "&")
        )

        if link.endswith("?"):
            link = link[:-1]

        if "#" in link:
            base, name = link.split("#", 1)
            link = f"{base}#{prefix}{name}"
        else:
            link = f"{link}#{prefix}config"

        result.append(link)

    return result


def main():
    token = os.getenv("GIST_TOKEN")

    if not token:
        log("❌ GIST_TOKEN отсутствует")
        return

    all_links = []

    headers = {
        "User-Agent": "okhttp/4.9.0",
        "Accept": "application/json",
        "Connection": "Keep-Alive"
    }

    for source in SOURCES:
        try:
            log(f"Получаю {source['url']}")

            r = requests.get(
                source["url"],
                headers=headers,
                timeout=30,
                verify=False,
                allow_redirects=True
            )

            r.raise_for_status()

            log(f"Конечный URL: {r.url}")
            log(f"Content-Type: {r.headers.get('Content-Type')}")

            links = process_links(
                r.text,
                source["prefix"]
            )

            log(f"{source['url']} -> {len(links)} конфигов")

            all_links.extend(links)

        except Exception as e:
            log(f"⚠ Ошибка {source['url']}: {e}")

    all_links = list(dict.fromkeys(all_links))

    ural_time = datetime.now(
        timezone(timedelta(hours=5))
    ).strftime("%d.%m.%Y %H:%M:%S")

    header = (
        "vless://00000000-0000-0000-0000-000000000000"
        "@127.0.0.1:0?type=none"
        f"#🕒_Ural_Time:_{ural_time}"
    )

    all_links.insert(0, header)

    content = "\n".join(all_links)

    with open("configs.txt", "w", encoding="utf-8") as f:
        f.write(content)

    log(f"configs.txt создан: {len(all_links)} строк")

    try:
        response = requests.patch(
            f"https://api.github.com/gists/{GIST_ID}",
            headers={
                "Authorization": f"token {token}"
            },
            json={
                "files": {
                    GIST_FILENAME: {
                        "content": content
                    }
                }
            }
        )

        if response.status_code == 200:
            log("✅ Gist обновлён")
        else:
            log(f"❌ Gist ошибка {response.status_code}: {response.text}")

    except Exception as e:
        log(f"❌ Ошибка Gist: {e}")

    log("🎉 Готово")


if __name__ == "__main__":
    main()
