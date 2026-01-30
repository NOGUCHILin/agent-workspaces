"""
全チャネルから一括でデータ収集
"""
import time
from pathlib import Path
from datetime import datetime
import argparse

from models import get_all_model_capacity_combinations
from config import validate_api_keys, RAKUTEN_APP_ID, YAHOO_CLIENT_ID
from scraper_rakuten import RakutenScraper
from scraper_yahoo import YahooShoppingScraper


def main():
    parser = argparse.ArgumentParser(description="iPhone中古価格の一括収集")
    parser.add_argument(
        "--test",
        action="store_true",
        help="テストモード（最初の3件のみ取得）",
    )
    parser.add_argument(
        "--channels",
        nargs="+",
        choices=["rakuten", "yahoo"],
        default=["rakuten", "yahoo"],
        help="データ収集するチャネル",
    )
    args = parser.parse_args()

    # API設定確認
    print("=== API設定確認 ===")
    api_status = validate_api_keys()
    for api, configured in api_status.items():
        print(f"  {api}: {'✅ 設定済み' if configured else '❌ 未設定'}")
    print()

    # データディレクトリ
    data_dir = Path(__file__).parent.parent / "data" / "raw"

    # 対象モデル
    combinations = get_all_model_capacity_combinations()
    if args.test:
        combinations = combinations[:3]
        print("⚠️  テストモード: 最初の3件のみ取得")

    print(f"=== データ収集開始 ===")
    print(f"対象モデル数: {len(combinations)}件")
    print(f"対象チャネル: {', '.join(args.channels)}")
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)

    # 楽天市場
    if "rakuten" in args.channels and api_status["rakuten"]:
        print("\n【楽天市場】")
        rakuten_dir = data_dir / "rakuten"
        scraper = RakutenScraper(RAKUTEN_APP_ID)

        for i, (model, capacity) in enumerate(combinations, 1):
            print(f"[{i}/{len(combinations)}] ", end="")
            scraper.scrape_iphone_prices(model, capacity, rakuten_dir)
            time.sleep(2)  # サイトへの負荷を考慮

    # Yahoo!ショッピング
    if "yahoo" in args.channels and api_status["yahoo"]:
        print("\n【Yahoo!ショッピング】")
        yahoo_dir = data_dir / "yahoo"
        scraper = YahooShoppingScraper(YAHOO_CLIENT_ID)

        for i, (model, capacity) in enumerate(combinations, 1):
            print(f"[{i}/{len(combinations)}] ", end="")
            scraper.scrape_iphone_prices(model, capacity, yahoo_dir)
            time.sleep(2)  # サイトへの負荷を考慮

    print("\n" + "-" * 60)
    print(f"完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("✅ データ収集完了！")


if __name__ == "__main__":
    main()
