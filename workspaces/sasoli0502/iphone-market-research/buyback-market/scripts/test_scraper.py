"""
修正後のスクレイパーをテスト
"""

from scraper_janpara import JanparaScraper

# 新しいモデルでテスト
test_models = [
    ("iPhone 16 Pro", "256GB"),
    ("iPhone 15 Pro", "256GB"),
    ("iPhone 14 Pro", "256GB"),
]

scraper = JanparaScraper()

for model, capacity in test_models:
    print(f"\n{'='*60}")
    print(f"テスト: {model} {capacity}")
    print('='*60)

    results = scraper.scrape_model(model, capacity)

    if results:
        print(f"\n取得データ: {len(results)}件")
        for i, result in enumerate(results[:3], 1):
            print(f"{i}. {result['product_name']}")
            print(f"   価格: ¥{result['buyback_price']:,}")
    else:
        print("\nデータなし")
