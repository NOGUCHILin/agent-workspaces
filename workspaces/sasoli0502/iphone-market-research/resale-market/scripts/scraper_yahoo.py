"""
Yahoo!ショッピング 商品検索APIを使った相場調査スクリプト
"""
import time
import requests
from datetime import datetime
from typing import List, Dict, Optional
import json
from pathlib import Path

from models import get_all_model_capacity_combinations, get_search_keywords, should_exclude_product
from config import YAHOO_CLIENT_ID


class YahooShoppingScraper:
    """Yahoo!ショッピングAPIを使った商品検索"""

    API_URL = "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch"
    HITS_PER_PAGE = 20  # 1ページあたりの取得件数
    MAX_PAGE = 5  # 最大取得ページ数
    SLEEP_INTERVAL = 1.0  # リクエスト間隔（秒）- 1秒に1リクエスト制限

    def __init__(self, client_id: str):
        if not client_id:
            raise ValueError("Yahoo!ショッピングAPIのClient IDが設定されていません")
        self.client_id = client_id

    def search_products(
        self, keyword: str, max_page: int = MAX_PAGE
    ) -> List[Dict]:
        """
        キーワードで商品検索

        Args:
            keyword: 検索キーワード
            max_page: 最大取得ページ数

        Returns:
            検索結果のリスト
        """
        all_items = []

        for page in range(1, max_page + 1):
            params = {
                "appid": self.client_id,
                "query": keyword,
                "results": self.HITS_PER_PAGE,
                "start": (page - 1) * self.HITS_PER_PAGE + 1,
                "sort": "+price",  # 価格安い順
            }

            try:
                response = requests.get(self.API_URL, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                # エラーチェック
                if "ResultSet" not in data:
                    break

                result_set = data["ResultSet"]
                total_results = result_set.get("totalResultsReturned", 0)

                if total_results == 0:
                    break  # 結果がなければ終了

                items = result_set.get("Result", [])
                all_items.extend(items)

                # これ以上結果がなければ終了
                total_available = result_set.get("totalResultsAvailable", 0)
                if len(all_items) >= total_available:
                    break

                # レート制限対策（重要: 1秒に1リクエスト）
                time.sleep(self.SLEEP_INTERVAL)

            except requests.exceptions.RequestException as e:
                print(f"  エラー: {keyword} (page {page}) - {e}")
                break

        return all_items

    def extract_product_info(self, item: Dict) -> Dict:
        """
        API結果から必要な情報を抽出

        Args:
            item: APIの商品情報

        Returns:
            抽出した商品情報
        """
        # 価格情報の取得
        price = 0
        if "Price" in item:
            price_data = item["Price"]
            if isinstance(price_data, dict):
                price = price_data.get("_value", 0)
            else:
                price = price_data

        return {
            "product_name": item.get("Name", ""),
            "price": int(price) if price else 0,
            "url": item.get("Url", ""),
            "shop_name": item.get("Store", {}).get("Name", ""),
            "image_url": item.get("Image", {}).get("Medium", ""),
            "description": item.get("Description", ""),
            "brand": item.get("Brand", {}).get("Name", ""),
        }

    def scrape_iphone_prices(
        self, model: str, capacity: str, output_dir: Optional[Path] = None
    ) -> List[Dict]:
        """
        特定のiPhoneモデル・容量の価格情報を取得

        Args:
            model: iPhoneモデル（例: "iPhone 15 Pro"）
            capacity: 容量（例: "256GB"）
            output_dir: 保存先ディレクトリ（Noneの場合は保存しない）

        Returns:
            商品情報のリスト
        """
        print(f"検索中: {model} {capacity}")

        # 検索キーワードのバリエーション
        keywords = get_search_keywords(model, capacity)

        all_products = []
        seen_urls = set()

        for keyword in keywords:
            print(f"  キーワード: {keyword}")
            items = self.search_products(keyword)

            valid_count = 0
            for item in items:
                product = self.extract_product_info(item)

                # 除外すべき商品をスキップ
                if should_exclude_product(product["product_name"]):
                    continue

                # 重複除去（URLベース）
                if product["url"] not in seen_urls:
                    product["search_keyword"] = keyword
                    product["model"] = model
                    product["capacity"] = capacity
                    product["scraped_at"] = datetime.now().isoformat()
                    all_products.append(product)
                    seen_urls.add(product["url"])
                    valid_count += 1

            print(f"    {len(items)}件取得 → {valid_count}件有効")

        print(f"  合計: {len(all_products)}件（重複除去後）")

        # 保存
        if output_dir and all_products:
            output_dir.mkdir(parents=True, exist_ok=True)
            filename = f"yahoo_{model.replace(' ', '_')}_{capacity}.json"
            filepath = output_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(all_products, f, ensure_ascii=False, indent=2)

            print(f"  保存: {filepath}")

        return all_products


def main():
    """メイン処理"""
    if not YAHOO_CLIENT_ID:
        print("❌ エラー: Yahoo!ショッピングAPIのClient IDが設定されていません")
        print("\n設定方法:")
        print("  export YAHOO_CLIENT_ID='your_client_id'")
        print("\nYahoo! Client ID取得:")
        print("  https://developer.yahoo.co.jp/")
        return

    # 出力ディレクトリ
    output_dir = Path(__file__).parent.parent / "data" / "raw" / "yahoo"

    # スクレイパー初期化
    scraper = YahooShoppingScraper(YAHOO_CLIENT_ID)

    # 全モデル×容量の組み合わせ
    combinations = get_all_model_capacity_combinations()

    print(f"Yahoo!ショッピング iPhone価格調査開始")
    print(f"対象: {len(combinations)}件")
    print(f"保存先: {output_dir}")
    print("-" * 60)

    # テスト実行（最初の3件のみ）
    for model, capacity in combinations[:3]:
        scraper.scrape_iphone_prices(model, capacity, output_dir)
        time.sleep(2)  # サイトへの負荷を考慮

    print("-" * 60)
    print("完了！")


if __name__ == "__main__":
    main()
