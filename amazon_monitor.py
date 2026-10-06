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
        print(
            "DIAG:",
            "137980=", "137980" in page,
            "137,980=", "137,980" in page,
            "Amazon.co.jp=", "Amazon.co.jp" in page,
            "他の出品者=", "他の出品者" in page,
            "新品=", "新品" in page,
            "HTML length=", len(page),
            flush=True
        )
        # Amazon「他の出品者」側を診断
        offer_url = (
            "https://www.amazon.co.jp/gp/product/ajax/"
            "ref=dp_aod_ALL_mbc?asin=B0G4RR4DM7"
            "&pc=dp&experienceId=aodAjaxMain"
        )

        offer_response = requests.get(
            offer_url,
            headers=headers,
            timeout=20
        )

        offer_page = offer_response.text

        print(
            "OFFER DIAG:",
            "HTTP=", offer_response.status_code,
            "137980=", "137980" in offer_page,
            "137,980=", "137,980" in offer_page,
            "Amazon.co.jp=", "Amazon.co.jp" in offer_page,
            "新品=", "新品" in offer_page,
            "length=", len(offer_page),
            flush=True
            )
        # -----------------------------
        # 在庫判定
        # -----------------------------
        # Amazon新品 137,980円の瞬間入荷を優先検出
        target_price_words = [
            "137,980",
            "137980",
            "￥137,980",
            "¥137,980",
        ]

        has_target_price = any(
            word in page
            for word in target_price_words
        )

        has_buy_button = (
            "カートに入れる" in page
            or "今すぐ買う" in page
        )

        # 30秒ごとの判定をActionsログに表示
        print(
            f"Target price: {has_target_price} | "
            f"Buy button: {has_buy_button}",
            flush=True
        )

        # 137,980円の表示を検出
        in_stock = has_target_price

        if in_stock:
            print(
                "POSSIBLE STOCK DETECTED!",
                flush=True
            )

            message = (
                "🚨 Amazon PS5 Pro 入荷検知！\n"
                "CFI-7100B01で137,980円の表示を検出しました。\n"
                "Amazon新品の瞬間入荷の可能性があります。\n"
                "すぐAmazonの商品ページを確認してください！"
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
