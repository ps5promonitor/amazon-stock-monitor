import os
import time
import requests

print("=== Amazon monitor START ===", flush=True)

ASIN = "B0G4RR4DM7"
URL = f"https://www.amazon.co.jp/dp/{ASIN}"

CHECK_INTERVAL = 30
MAX_RUNTIME = 55 * 60  # 55分

headers = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/18.0 Mobile/15E148 Safari/604.1"
    ),
    "Accept-Language": "ja-JP,ja;q=0.9",
}

token = os.environ.get("PUSHOVER_API_TOKEN")
user = os.environ.get("PUSHOVER_USER_KEY")

start_time = time.time()
check_count = 0

print(f"Target URL: {URL}", flush=True)
print("Settings loaded.", flush=True)
print("Amazon PS5 Pro monitor started.", flush=True)


def send_notification(message):
    if not token or not user:
        print("Pushover settings missing.", flush=True)
        return False

    try:
        result = requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": token,
                "user": user,
                "title": "🚨 PS5 Pro Amazon入荷！",
                "message": message,
                "url": URL,
                "url_title": "Amazonの商品ページを開く",
                "priority": 1,
            },
            timeout=20,
        )

        print(
            f"Pushover: HTTP {result.status_code}",
            flush=True
        )

        return result.status_code == 200

    except Exception as e:
        print("Pushover error:", e, flush=True)
        return False


while time.time() - start_time < MAX_RUNTIME:

    check_count += 1

    try:
        response = requests.get(
            URL,
            headers=headers,
            timeout=20
        )

        print(
            f"Check #{check_count}: HTTP {response.status_code}",
            flush=True
        )

        if response.status_code != 200:
            print("Amazon page unavailable.", flush=True)
            time.sleep(CHECK_INTERVAL)
            continue

        page = response.text

        # -----------------------------
        # 在庫判定
        # -----------------------------

        strong_stock_words = [
            "カートに入れる",
            "今すぐ買う",
        ]

        shipping_words = [
            "在庫あり",
            "通常1〜2日以内に発送",
            "通常2〜3日以内に発送",
            "通常1～2日以内に発送",
            "通常2～3日以内に発送",
        ]

        unavailable_words = [
            "現在在庫切れです",
            "現在お取り扱いできません",
            "一時的に在庫切れ",
        ]

        has_buy_button = any(
            word in page
            for word in strong_stock_words
        )

        has_shipping = any(
            word in page
            for word in shipping_words
        )

        unavailable = any(
            word in page
            for word in unavailable_words
        )

        # 購入ボタンがあり、
        # 明確な在庫切れ表示がない場合を候補とする
        in_stock = (
            has_buy_button
            and not unavailable
        )

        if in_stock:

            print(
                "POSSIBLE STOCK DETECTED!",
                flush=True
            )

            if has_shipping:
                message = (
                    "AmazonでPS5 Pro "
                    "CFI-7100B01の在庫を検知しました！\n"
                    "購入可能表示＋発送/在庫表示を確認。\n"
                    "すぐAmazonを確認してください。"
                )
            else:
                message = (
                    "AmazonでPS5 Pro "
                    "CFI-7100B01の購入可能表示を検知しました！\n"
                    "すぐAmazonを確認してください。"
                )

            sent = send_notification(message)

            if sent:
                print(
                    "Notification sent successfully.",
                    flush=True
                )

            # 通知後に監視終了
            break

        else:
            print(
                "No stock detected.",
                flush=True
            )

    except Exception as e:
        print(
            "Check error:",
            e,
            flush=True
        )

    print(
        f"Waiting {CHECK_INTERVAL} seconds...",
        flush=True
    )

    time.sleep(CHECK_INTERVAL)


print("Amazon monitor finished.", flush=True)
