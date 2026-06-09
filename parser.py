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

    # --- ПРИНУДИТЕЛЬНОЕ ВРЕМЯ УРАЛ (UTC+5) ---
    # Получаем время UTC, добавляем 5 часов
    from datetime import timedelta, timezone
    
    ural_offset = timezone(timedelta(hours=5))
    # Используем utcnow с явным указанием зоны
    ural_time = datetime.now(ural_offset).strftime('%d.%m.%Y %H:%M:%S')
    
    header_line = f"vless://00000000-0000-0000-0000-000000000000@127.0.0.1:0?type=none#🕒_Update_Ural:_{ural_time}"
    all_final_links.insert(0, header_line)
    # ----------------------------------------

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
