"""
楽天市場 商品検索APIを使った相場調査スクリプト
"""
import time
import requests
from datetime import datetime
from typing import List, Dict, Optional
import json
from pathlib import Path

from models import get_all_model_capacity_combinations, get_search_keywords, should_exclude_product
from config import RAKUTEN_APP_ID


class RakutenScraper:
    """楽天市場APIを使った商品検索"""

    API_URL = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170706"
    HITS_PER_PAGE = 30  # 1ページあたりの取得件数（最大30）
    MAX_PAGE = 3  # 最大取得ページ数（過度なリクエストを避ける）
    SLEEP_INTERVAL = 1.0  # リクエスト間隔（秒）

    def __init__(self, app_id: str):
        if not app_id:
            raise ValueError("楽天APIのアプリIDが設定されていません")
        self.app_id = app_id

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
                "applicationId": self.app_id,
                "format": "json",
                "keyword": keyword,
                "hits": self.HITS_PER_PAGE,
                "page": page,
                "sort": "+itemPrice",  # 価格安い順
            }

            try:
                response = requests.get(self.API_URL, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                items = data.get("Items", [])
                if not items:
                    break  # 結果がなければ終了

                all_items.extend(items)

                # ページ情報
                page_count = data.get("pageCount", 0)
                if page >= page_count:
                    break  # 最終ページに到達

                # レート制限対策
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
        item_data = item.get("Item", {})

        # 画像URLを安全に取得
        image_urls = item_data.get("mediumImageUrls", [])
        image_url = ""
        if image_urls and len(image_urls) > 0:
            image_url = image_urls[0].get("imageUrl", "")

        return {
            "product_name": item_data.get("itemName", ""),
            "price": item_data.get("itemPrice", 0),
            "url": item_data.get("itemUrl", ""),
            "shop_name": item_data.get("shopName", ""),
            "image_url": image_url,
            "review_count": item_data.get("reviewCount", 0),
            "review_average": item_data.get("reviewAverage", 0),
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
            filename = f"rakuten_{model.replace(' ', '_')}_{capacity}.json"
            filepath = output_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(all_products, f, ensure_ascii=False, indent=2)

            print(f"  保存: {filepath}")

        return all_products


def main():
    """メイン処理"""
    if not RAKUTEN_APP_ID:
        print("❌ エラー: 楽天APIのアプリIDが設定されていません")
        print("\n設定方法:")
        print("  export RAKUTEN_APP_ID='your_app_id'")
        print("\n楽天APIアプリID取得:")
        print("  https://webservice.rakuten.co.jp/")
        return

    # 出力ディレクトリ
    output_dir = Path(__file__).parent.parent / "data" / "raw" / "rakuten"

    # スクレイパー初期化
    scraper = RakutenScraper(RAKUTEN_APP_ID)

    # 全モデル×容量の組み合わせ
    combinations = get_all_model_capacity_combinations()

    print(f"楽天市場 iPhone価格調査開始")
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
