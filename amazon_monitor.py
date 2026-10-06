import os
import time
import requests

# ==============================
# 設定
# ==============================

ASIN = "B0G4RR4DM7"
PRODUCT_URL = f"https://www.amazon.co.jp/dp/{ASIN}"

CHECK_INTERVAL = 30
MAX_RUNTIME = 55 * 60

PUSHOVER_TOKEN = os.environ["PUSHOVER_API_TOKEN"]
PUSHOVER_USER = os.environ["PUSHOVER_USER_KEY"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/18.0 Mobile/15E148 Safari/604.1"
    ),
    "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
}

# ==============================
# Pushover
# ==============================

def send_notification(message):
    try:
        response = requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": PUSHOVER_TOKEN,
                "user": PUSHOVER_USER,
                "title": "PS5 Pro Amazon入荷",
                "message": message,
                "url": PRODUCT_URL,
                "url_title": "Amazonで確認",
                "priority": 1,
            },
            timeout=20,
        )

        print(
            f"Pushover HTTP {response.status_code}",
            flush=True
        )

        return response.status_code == 200

    except Exception as e:
        print(
            f"Pushover error: {e}",
            flush=True
        )
        return False


# ==============================
# 監視開始
# ==============================

print(
    "Amazon PS5 Pro monitor started.",
    flush=True
)

start_time = time.time()
check_count = 0

session = requests.Session()
session.headers.update(HEADERS)

while time.time() - start_time < MAX_RUNTIME:

    check_count += 1

    try:
        # キャッシュ回避用
        url = f"{PRODUCT_URL}?psc=1&t={int(time.time())}"

        response = session.get(
            url,
            timeout=20
        )

        print(
            f"Check #{check_count}: HTTP {response.status_code}",
            flush=True
        )

        if response.status_code != 200:
            print(
                "Amazon returned non-200 response.",
                flush=True
            )
            time.sleep(CHECK_INTERVAL)
            continue

        page = response.text
        page_lower = page.lower()
        
        print("PAGE PREVIEW:", page[:1000], flush=True)
        
        # --------------------------
        # 対象商品の確認
        # --------------------------

        correct_product = (
            ASIN.lower() in page_lower
            or "cfi-7100b01" in page_lower
        )

        # --------------------------
        # 137,980円の検出
        # --------------------------

        price_words = [
            "137,980",
            "137980",
            "￥137,980",
            "¥137,980",
            "137,980円",
            "137980.00",
        ]

        has_target_price = any(
            word.lower() in page_lower
            for word in price_words
        )

        # --------------------------
        # 購入可能要素
        # --------------------------

        has_buy_element = any([
            "add-to-cart-button" in page_lower,
            "buy-now-button" in page_lower,
            "addtocart" in page_lower,
        ])

        # --------------------------
        # Amazon販売の手掛かり
        # --------------------------

        has_amazon_seller = any([
            "amazon.co.jp" in page_lower,
            "ships from amazon.co.jp" in page_lower,
            "sold by amazon.co.jp" in page_lower,
            "販売元" in page and "amazon.co.jp" in page_lower,
        ])

        # --------------------------
        # ログ
        # --------------------------

        print(
            "CHECK:",
            f"product={correct_product}",
            f"price137980={has_target_price}",
            f"buy={has_buy_element}",
            f"amazon={has_amazon_seller}",
            f"html={len(page)}",
            flush=True,
        )

        # --------------------------
        # 通知判定
        # --------------------------
        #
        # 最重要条件：
        # 対象商品 + 137,980円
        #
        # Buy Boxは在庫切れでもHTMLに存在することが
        # 実測で分かったため、必須条件にはしない。
        #

        in_stock = (
            correct_product
            and has_target_price
        )

        if in_stock:

            print(
                "TARGET OFFER DETECTED!",
                flush=True
            )

            message = (
                "🚨 PS5 Pro CFI-7100B01 入荷候補！\n"
                "Amazonページで137,980円を検出しました。\n"
                "Amazonの出品をすぐ確認してください。"
            )

            if send_notification(message):

                print(
                    "Notification sent successfully.",
                    flush=True
                )

                break

        else:

            print(
                "No target offer detected.",
                flush=True
            )

    except Exception as e:

        print(
            f"Monitor error: {e}",
            flush=True
        )

    print(
        f"Waiting {CHECK_INTERVAL} seconds...",
        flush=True
    )

    time.sleep(CHECK_INTERVAL)


print(
    "Monitor finished.",
    flush=True
)
