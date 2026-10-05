import os
import time
import requests

print("=== Amazon monitor START ===", flush=True)

ASIN = "B0G4RR4DM7"
URL = f"https://www.amazon.co.jp/dp/{ASIN}"

print(f"Target URL: {URL}", flush=True)

CHECK_INTERVAL = 30
MAX_RUNTIME = 60 * 60

print("Settings loaded.", flush=True)

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

print("Amazon PS5 Pro monitor started.")

while time.time() - start_time < MAX_RUNTIME:
    check_count += 1

    try:
        response = requests.get(
            URL,
            headers=headers,
            timeout=20
        )

        print(
            f"Check #{check_count}: "
            f"HTTP {response.status_code}"
        )

        page = response.text

        stock_words = [
            "カートに入れる",
            "今すぐ買う",
            "在庫あり",
            "通常1～2日以内に発送",
            "通常2～3日以内に発送",
        ]

        in_stock = any(word in page for word in stock_words)

        if in_stock:
            print("POSSIBLE STOCK DETECTED!")

            if token and user:
                result = requests.post(
                    "https://api.pushover.net/1/messages.json",
                    data={
                        "token": token,
                        "user": user,
                        "title": "🚨 PS5 Pro Amazon在庫検知",
                        "message": (
                            "AmazonでPS5 Pro "
                            "CFI-7100B01の在庫を検知しました！"
                        ),
                        "url": URL,
                        "url_title": "Amazonの商品ページを開く",
                    },
                    timeout=20,
                )

                print(
                    "Pushover:",
                    result.status_code
                )

            break

        print("No stock detected.")

    except Exception as e:
        print("Check error:", e)

    print(f"Waiting {CHECK_INTERVAL} seconds...")
    time.sleep(CHECK_INTERVAL)

print("Amazon monitor finished.")
