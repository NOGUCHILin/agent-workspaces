"""
じゃんぱら買取価格スクレイパー

じゃんぱらの買取価格検索ページからiPhoneの買取価格を取得する
"""

import json
import time
import re
from datetime import datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from models import get_all_model_capacity_combinations

# 設定
BASE_URL = "https://buy.janpara.co.jp"
SEARCH_URL = f"{BASE_URL}/buy/search/"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "raw" / "janpara"
SLEEP_INTERVAL = 2  # リクエスト間隔（秒）

# HTTPヘッダー（スクレイピング検出回避）
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
}


def is_exact_model_match(product_name, target_model, target_capacity):
    """
    商品名が指定されたモデルと完全に一致するかチェック

    Args:
        product_name: 商品名（例: "iPhone 15 Pro 256GB"）
        target_model: 対象モデル（例: "iPhone 15 Pro"）
        target_capacity: 対象容量（例: "256GB"）

    Returns:
        bool: 一致する場合True
    """
    # 商品名を正規化（大文字小文字、スペース）
    product_name = product_name.upper().replace("　", " ")
    target_model = target_model.upper().replace("　", " ")

    # モデル名から数字部分を抽出（厳密マッチング用）
    # 例: "iPhone 15 Pro" -> "15"
    model_number_match = re.search(r'IPHONE\s+(\d+|X|XR|XS|SE)', target_model)
    if not model_number_match:
        return False

    model_number = model_number_match.group(1)

    # 商品名にモデル番号が含まれているかチェック
    if model_number == "SE":
        # SE の場合は特別処理（第2世代、第3世代など）
        if "SE" not in product_name and "SE（" not in product_name:
            return False
    elif model_number in ["X", "XR", "XS"]:
        # X, XR, XS の場合
        if model_number == "X":
            # iPhone X（XR, XSではない）
            if " X " not in product_name and not re.search(r'IPHONE\s*X\s+\d+GB', product_name):
                return False
            # XR, XSを除外
            if "XR" in product_name or "XS" in product_name:
                return False
        elif model_number == "XR":
            if "XR" not in product_name:
                return False
        elif model_number == "XS":
            if "XS" not in product_name:
                return False
            # XS Max は除外（別モデル）
            if "XS MAX" in product_name and "MAX" not in target_model:
                return False
    else:
        # 数字モデル（11, 12, 13等）
        # iPhone 12 の場合、iPhone 120やiPhone 1などにマッチしないように
        pattern = rf'IPHONE\s+{model_number}(?:\s|$|[^0-9])'
        if not re.search(pattern, product_name):
            return False

    # サブモデル（Pro, Plus, Max, mini）のチェック
    # モデル番号の直後にサブモデル名があるかを確認（より厳密）
    if "PRO MAX" in target_model:
        # "iPhone XX Pro Max" の形式を確認
        if not re.search(rf'IPHONE\s+{model_number}\s+PRO\s+MAX', product_name):
            return False
    elif "PRO" in target_model:
        # "iPhone XX Pro" の形式を確認（Pro Maxは除外）
        if not re.search(rf'IPHONE\s+{model_number}\s+PRO(?!\s+MAX)', product_name):
            return False
    elif "PLUS" in target_model:
        # "iPhone XX Plus" の形式を確認
        if not re.search(rf'IPHONE\s+{model_number}\s+PLUS', product_name):
            return False
    elif "MINI" in target_model:
        # "iPhone XX mini" の形式を確認
        if not re.search(rf'IPHONE\s+{model_number}\s+MINI', product_name):
            return False
    else:
        # 無印モデル（Pro, Plus, Max, miniなし）
        # モデル番号の直後にサブモデル名がないことを確認
        if re.search(rf'IPHONE\s+{model_number}\s+(PRO|PLUS|MAX|MINI)', product_name):
            return False

    # 容量のチェック
    if target_capacity not in product_name:
        return False

    return True


class JanparaScraper:
    """じゃんぱらスクレイパークラス"""

    def __init__(self):
        self.base_url = BASE_URL
        self.search_url = SEARCH_URL
        self.headers = HEADERS
        self.output_dir = OUTPUT_DIR

    def scrape_model(self, model, capacity):
        """
        モデルの買取価格を取得

        Args:
            model: モデル名
            capacity: 容量

        Returns:
            list: 買取価格データのリスト
        """
        products = search_buyback_price(model, capacity)

        # データを保存
        if products:
            save_to_json(products, model, capacity)

        return products


def search_buyback_price(model, capacity):
    """
    じゃんぱらで買取価格を検索

    Args:
        model: モデル名（例：iPhone 15 Pro）
        capacity: 容量（例：256GB）

    Returns:
        list: 買取価格データのリスト
    """
    # 検索キーワード作成
    keyword = f"{model} {capacity}"

    print(f"  検索中: {keyword}")

    # 検索リクエスト
    params = {
        "keyword": keyword,
        "category": "iphone",  # iPhoneカテゴリに限定
    }

    try:
        response = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()

        # HTMLを解析
        soup = BeautifulSoup(response.content, "lxml")

        # 買取価格データを抽出
        products = []

        # じゃんぱらの商品リストを解析
        # 各商品は <div class="col"> に含まれる
        items = soup.find_all("div", class_="col")

        if not items:
            print(f"    → 商品が見つかりませんでした")
            return []

        filtered_count = 0
        for item in items:
            try:
                # 商品名 - <p class="tit">
                name_elem = item.find("p", class_="tit")
                if not name_elem:
                    continue
                product_name = name_elem.get_text(strip=True)

                # モデル名の厳密なマッチングチェック
                if not is_exact_model_match(product_name, model, capacity):
                    filtered_count += 1
                    continue

                # 詳細ページURL - <p class="detail"><a>
                detail_elem = item.find("p", class_="detail")
                url = ""
                if detail_elem:
                    link_elem = detail_elem.find("a", href=True)
                    if link_elem:
                        url = BASE_URL + link_elem["href"]

                # 状態別の価格を取得
                used_wrap = item.find("div", class_="used_wrap")
                if not used_wrap:
                    continue

                # 未使用品の価格
                unused_div = used_wrap.find("div", class_="unused")
                unused_price = None
                if unused_div:
                    price_elem = unused_div.find("p", class_="price")
                    if price_elem:
                        price_text = price_elem.get_text(strip=True)
                        # "--- 円" または数値
                        if "---" not in price_text and "円" in price_text:
                            try:
                                # "～85,000円" や "85,000円" から数値を抽出
                                price_text = price_text.replace("～", "").replace(",", "").replace("円", "").replace("¥", "").strip()
                                unused_price = int(price_text)
                            except ValueError:
                                pass

                # 中古品の価格
                used_div = used_wrap.find("div", class_="used")
                used_price = None
                if used_div:
                    price_elem = used_div.find("p", class_="price")
                    if price_elem:
                        price_text = price_elem.get_text(strip=True)
                        if "---" not in price_text and "円" in price_text:
                            try:
                                # "～85,000円" や "85,000円" から数値を抽出
                                price_text = price_text.replace("～", "").replace(",", "").replace("円", "").replace("¥", "").strip()
                                used_price = int(price_text)
                            except ValueError:
                                pass

                # データ作成（未使用品と中古品を別々に保存）
                if unused_price:
                    product_data = {
                        "product_name": product_name,
                        "model": model,
                        "capacity": capacity,
                        "condition": "未使用品",
                        "buyback_price": unused_price,
                        "url": url,
                        "site": "じゃんぱら",
                        "scraped_at": datetime.now().isoformat()
                    }
                    products.append(product_data)

                if used_price:
                    product_data = {
                        "product_name": product_name,
                        "model": model,
                        "capacity": capacity,
                        "condition": "中古品",
                        "buyback_price": used_price,
                        "url": url,
                        "site": "じゃんぱら",
                        "scraped_at": datetime.now().isoformat()
                    }
                    products.append(product_data)

            except Exception as e:
                print(f"    警告: 商品データの解析エラー: {e}")
                continue

        if filtered_count > 0:
            print(f"    → {len(products)}件取得（{filtered_count}件フィルタリング）")
        else:
            print(f"    → {len(products)}件取得")
        return products

    except requests.exceptions.RequestException as e:
        print(f"    エラー: リクエスト失敗: {e}")
        return []
    except Exception as e:
        print(f"    エラー: 予期しないエラー: {e}")
        return []


def save_to_json(data, model, capacity):
    """
    データをJSONファイルに保存

    Args:
        data: 保存するデータ
        model: モデル名
        capacity: 容量
    """
    if not data:
        return

    # ファイル名作成（例：janpara_iPhone_15_Pro_256GB.json）
    model_safe = model.replace(" ", "_")
    filename = f"janpara_{model_safe}_{capacity}.json"
    filepath = OUTPUT_DIR / filename

    # 出力ディレクトリ作成
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # JSON保存
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"  保存完了: {filepath}")


def main():
    """メイン処理"""
    print("=== じゃんぱら買取価格収集開始 ===\n")

    # テスト用：最初の3件のみ
    all_models = get_all_model_capacity_combinations()
    test_models = all_models[:3]

    print(f"テスト実行: {len(test_models)}件のモデルを収集\n")

    total_count = 0

    for model, capacity in test_models:
        print(f"[{model} {capacity}]")

        # 買取価格を検索
        products = search_buyback_price(model, capacity)

        if products:
            # JSONに保存
            save_to_json(products, model, capacity)
            total_count += len(products)

        # レート制限対策
        time.sleep(SLEEP_INTERVAL)

    print(f"\n=== 収集完了 ===")
    print(f"合計: {total_count}件の買取価格データを取得")
    print(f"保存先: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
