"""
イオシス買取価格スクレイパー

イオシスのiPhone買取価格リストからデータを取得する
"""

import json
import time
from datetime import datetime
from pathlib import Path
import re
import requests
from bs4 import BeautifulSoup
from models import get_all_model_capacity_combinations

# 設定
BASE_URL = "https://k-tai-iosys.com"
PRICELIST_URL = f"{BASE_URL}/pricelist/smartphone/iphone/"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "raw" / "iosys"
SLEEP_INTERVAL = 2  # リクエスト間隔（秒）

# HTTPヘッダー
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
}


def normalize_model_name(name):
    """
    イオシスのモデル名を標準形式に変換
    例: "iPhoneXR" → "iPhone XR"
         "iPhone12Pro" → "iPhone 12 Pro"
         "iPhone17 256GB" → "iPhone 17"
         "iPhoneX 256GB" → "iPhone X"
    """
    # まず容量を削除（数字モデルと混同しないように先に処理）
    name = re.sub(r'\s+\d+GB$', '', name)

    # XR, XS, XS Maxの処理（数字パターンより先に処理）
    name = name.replace("iPhoneXR", "iPhone XR")
    name = name.replace("iPhoneXSMax", "iPhone XS Max")
    name = name.replace("iPhoneXS", "iPhone XS")
    name = name.replace("iPhoneX", "iPhone X")
    name = name.replace("XSMax", "XS Max")

    # SEの処理
    name = name.replace("iPhoneSE", "iPhone SE")

    # "Pro Max"の処理（数字パターンより先に処理）
    name = name.replace("ProMax", "Pro Max")

    # スペースがない数字モデルの処理（iPhone12 → iPhone 12）
    # ただし、X, XR, XS, SEは除外
    if not any(x in name for x in ["iPhone X", "iPhone SE"]):
        name = re.sub(r'(iPhone)(\d+)', r'\1 \2', name)
        name = re.sub(r'(iPhone\s+\d+)(Pro|Plus|mini)', r'\1 \2', name)

    return name.strip()


def extract_capacity(element):
    """
    テーブル行から容量を抽出
    """
    # <th>内の容量表示を探す
    th = element.find("th")
    if th:
        text = th.get_text(strip=True)
        # "256GB"のようなパターンを抽出
        match = re.search(r'(\d+GB)', text)
        if match:
            return match.group(1)
    return None


def parse_price(price_text):
    """
    価格テキストから数値を抽出
    例: "116,000円" → 116000
    """
    if not price_text or "---" in price_text or "円" not in price_text:
        return None

    try:
        # 数値のみを抽出
        price_text = re.sub(r'[^\d]', '', price_text)
        return int(price_text) if price_text else None
    except ValueError:
        return None


class IosysScraper:
    """イオシススクレイパークラス"""

    def __init__(self):
        self.base_url = BASE_URL
        self.pricelist_url = PRICELIST_URL
        self.headers = HEADERS
        self.output_dir = OUTPUT_DIR

    def scrape_all_models(self):
        """
        全モデルの買取価格を取得

        Returns:
            list: 全モデルの買取価格データのリスト（フラット化）
        """
        all_products_dict = scrape_iosys_pricelist()

        # 辞書をフラットなリストに変換
        all_products_list = []
        for products in all_products_dict.values():
            all_products_list.extend(products)

        return all_products_list


def scrape_iosys_pricelist():
    """
    イオシスのiPhone買取価格リストをスクレイピング
    """
    print("=== イオシス買取価格収集開始 ===\n")
    print(f"URL: {PRICELIST_URL}\n")

    try:
        response = requests.get(PRICELIST_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "lxml")

        # 価格データを抽出
        all_products = {}  # {(model, capacity): [products]}

        # 価格リストのテーブルを探す
        tables = soup.find_all("table", class_="table")

        if not tables:
            print("警告: 価格リストのテーブルが見つかりませんでした")
            return {}

        for table in tables:
            rows = table.find_all("tr")

            for row in rows:
                try:
                    # モデル名を取得
                    name_elem = row.find("span", class_="name")
                    if not name_elem:
                        continue

                    # テキストを取得し、改行や余分なスペースを除去
                    raw_name = name_elem.get_text(strip=True)
                    # 連続する空白文字（改行、タブ、スペース）を1つのスペースに置換
                    raw_name = re.sub(r'\s+', ' ', raw_name)
                    model_name = normalize_model_name(raw_name)

                    # 容量を取得
                    capacity = extract_capacity(row)
                    if not capacity:
                        continue

                    # 価格情報を取得
                    td = row.find("td")
                    if not td:
                        continue

                    # 未使用品価格
                    s_price_elem = td.find("span", class_="s-price")
                    unused_price = parse_price(s_price_elem.get_text() if s_price_elem else "")

                    # 中古品価格（上限）
                    a_price_elem = td.find("span", class_="a-price")
                    used_high_price = parse_price(a_price_elem.get_text() if a_price_elem else "")

                    # 中古品価格（下限）
                    c_price_elem = td.find("span", class_="c-price")
                    used_low_price = parse_price(c_price_elem.get_text() if c_price_elem else "")

                    # キャリア情報
                    carrier_elem = row.find("span", class_="carrer")
                    carrier = carrier_elem.get_text(strip=True) if carrier_elem else "SIMフリー"

                    # 商品名を構築
                    product_name = f"{carrier} {model_name} {capacity}"

                    # データを作成
                    key = (model_name, capacity)
                    if key not in all_products:
                        all_products[key] = []

                    # 未使用品
                    if unused_price:
                        all_products[key].append({
                            "product_name": product_name,
                            "model": model_name,
                            "capacity": capacity,
                            "condition": "未使用品",
                            "buyback_price": unused_price,
                            "carrier": carrier,
                            "url": PRICELIST_URL,
                            "site": "イオシス",
                            "scraped_at": datetime.now().isoformat()
                        })

                    # 中古品（上限）
                    if used_high_price:
                        all_products[key].append({
                            "product_name": product_name,
                            "model": model_name,
                            "capacity": capacity,
                            "condition": "中古品（上限）",
                            "buyback_price": used_high_price,
                            "carrier": carrier,
                            "url": PRICELIST_URL,
                            "site": "イオシス",
                            "scraped_at": datetime.now().isoformat()
                        })

                    # 中古品（下限）
                    if used_low_price:
                        all_products[key].append({
                            "product_name": product_name,
                            "model": model_name,
                            "capacity": capacity,
                            "condition": "中古品（下限）",
                            "buyback_price": used_low_price,
                            "carrier": carrier,
                            "url": PRICELIST_URL,
                            "site": "イオシス",
                            "scraped_at": datetime.now().isoformat()
                        })

                except Exception as e:
                    print(f"警告: 行の解析エラー: {e}")
                    continue

        return all_products

    except requests.exceptions.RequestException as e:
        print(f"エラー: リクエスト失敗: {e}")
        return {}
    except Exception as e:
        print(f"エラー: 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        return {}


def save_to_json(all_products):
    """
    データをJSONファイルに保存
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total_count = 0
    for (model, capacity), products in all_products.items():
        if not products:
            continue

        # ファイル名作成
        model_safe = model.replace(" ", "_")
        filename = f"iosys_{model_safe}_{capacity}.json"
        filepath = OUTPUT_DIR / filename

        # JSON保存
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2)

        print(f"  保存: {model} {capacity} ({len(products)}件) → {filename}")
        total_count += len(products)

    return total_count


def main():
    """メイン処理"""
    all_products = scrape_iosys_pricelist()

    if not all_products:
        print("\nデータが取得できませんでした")
        return

    print(f"\n=== データ保存中 ===\n")
    total_count = save_to_json(all_products)

    print(f"\n=== 収集完了 ===")
    print(f"合計: {len(all_products)}モデル、{total_count}件の買取価格データを取得")
    print(f"保存先: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
