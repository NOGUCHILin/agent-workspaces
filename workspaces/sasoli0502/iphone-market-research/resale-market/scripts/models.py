"""
iPhone機種と容量の定義
"""

# iPhone X（2017年）以降のモデル定義
IPHONE_MODELS = {
    # 2017年
    "iPhone X": {
        "year": 2017,
        "capacities": ["64GB", "256GB"]
    },

    # 2018年
    "iPhone XR": {
        "year": 2018,
        "capacities": ["64GB", "128GB", "256GB"]
    },
    "iPhone XS": {
        "year": 2018,
        "capacities": ["64GB", "256GB", "512GB"]
    },
    "iPhone XS Max": {
        "year": 2018,
        "capacities": ["64GB", "256GB", "512GB"]
    },

    # 2019年
    "iPhone 11": {
        "year": 2019,
        "capacities": ["64GB", "128GB", "256GB"]
    },
    "iPhone 11 Pro": {
        "year": 2019,
        "capacities": ["64GB", "256GB", "512GB"]
    },
    "iPhone 11 Pro Max": {
        "year": 2019,
        "capacities": ["64GB", "256GB", "512GB"]
    },

    # 2020年
    "iPhone 12 mini": {
        "year": 2020,
        "capacities": ["64GB", "128GB", "256GB"]
    },
    "iPhone 12": {
        "year": 2020,
        "capacities": ["64GB", "128GB", "256GB"]
    },
    "iPhone 12 Pro": {
        "year": 2020,
        "capacities": ["128GB", "256GB", "512GB"]
    },
    "iPhone 12 Pro Max": {
        "year": 2020,
        "capacities": ["128GB", "256GB", "512GB"]
    },

    # 2021年
    "iPhone 13 mini": {
        "year": 2021,
        "capacities": ["128GB", "256GB", "512GB"]
    },
    "iPhone 13": {
        "year": 2021,
        "capacities": ["128GB", "256GB", "512GB"]
    },
    "iPhone 13 Pro": {
        "year": 2021,
        "capacities": ["128GB", "256GB", "512GB", "1TB"]
    },
    "iPhone 13 Pro Max": {
        "year": 2021,
        "capacities": ["128GB", "256GB", "512GB", "1TB"]
    },

    # 2022年
    "iPhone 14": {
        "year": 2022,
        "capacities": ["128GB", "256GB", "512GB"]
    },
    "iPhone 14 Plus": {
        "year": 2022,
        "capacities": ["128GB", "256GB", "512GB"]
    },
    "iPhone 14 Pro": {
        "year": 2022,
        "capacities": ["128GB", "256GB", "512GB", "1TB"]
    },
    "iPhone 14 Pro Max": {
        "year": 2022,
        "capacities": ["128GB", "256GB", "512GB", "1TB"]
    },

    # 2023年
    "iPhone 15": {
        "year": 2023,
        "capacities": ["128GB", "256GB", "512GB"]
    },
    "iPhone 15 Plus": {
        "year": 2023,
        "capacities": ["128GB", "256GB", "512GB"]
    },
    "iPhone 15 Pro": {
        "year": 2023,
        "capacities": ["128GB", "256GB", "512GB", "1TB"]
    },
    "iPhone 15 Pro Max": {
        "year": 2023,
        "capacities": ["128GB", "256GB", "512GB", "1TB"]
    },

    # 2024年
    "iPhone 16": {
        "year": 2024,
        "capacities": ["128GB", "256GB", "512GB"]
    },
    "iPhone 16 Plus": {
        "year": 2024,
        "capacities": ["128GB", "256GB", "512GB"]
    },
    "iPhone 16 Pro": {
        "year": 2024,
        "capacities": ["256GB", "512GB", "1TB"]
    },
    "iPhone 16 Pro Max": {
        "year": 2024,
        "capacities": ["256GB", "512GB", "1TB"]
    },
}


def get_all_model_capacity_combinations():
    """
    全てのモデル×容量の組み合わせを生成

    Returns:
        list: [(model, capacity), ...] のリスト
    """
    combinations = []
    for model, info in IPHONE_MODELS.items():
        for capacity in info["capacities"]:
            combinations.append((model, capacity))
    return combinations


def get_search_keywords(model, capacity):
    """
    検索用キーワードのバリエーションを生成

    Args:
        model: モデル名（例: "iPhone 15 Pro"）
        capacity: 容量（例: "256GB"）

    Returns:
        list: 検索キーワードのリスト
    """
    # より具体的なキーワードで本体のみを検索
    keywords = [
        f"{model} {capacity} 本体 SIMフリー",
        f"{model} {capacity} SIMフリー 本体",
        f"{model} {capacity} 中古",
    ]
    return keywords


def should_exclude_product(product_name: str) -> bool:
    """
    除外すべき商品かどうかを判定

    Args:
        product_name: 商品名

    Returns:
        bool: 除外すべきならTrue
    """
    # 除外キーワード（iPhone本体以外を除外）
    exclude_keywords = [
        "usbメモリ",
        "usb メモリ",
        "ケース",
        "カバー",
        "フィルム",
        "ガラス",
        "保護",
        "充電器",
        "ケーブル",
        "イヤホン",
        "バッテリー",
        "アダプタ",
        "スタンド",
        "ホルダー",
        "リング",
        "ストラップ",
        "simカード",
        "sim カード",
        "メモリーカード",
        "sdカード",
    ]

    product_name_lower = product_name.lower()

    for keyword in exclude_keywords:
        if keyword in product_name_lower:
            return True

    return False


if __name__ == "__main__":
    # テスト実行
    combinations = get_all_model_capacity_combinations()
    print(f"総組み合わせ数: {len(combinations)}")
    print("\n最初の5件:")
    for model, capacity in combinations[:5]:
        print(f"  {model} {capacity}")

    print("\n最後の5件:")
    for model, capacity in combinations[-5:]:
        print(f"  {model} {capacity}")

    # 検索キーワード例
    print("\n検索キーワード例（iPhone 15 Pro 256GB）:")
    for keyword in get_search_keywords("iPhone 15 Pro", "256GB"):
        print(f"  {keyword}")
