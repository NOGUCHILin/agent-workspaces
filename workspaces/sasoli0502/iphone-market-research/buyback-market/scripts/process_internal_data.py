#!/usr/bin/env python3
"""
弊社買取実績データ処理スクリプト

Kintoneからエクスポートしたデータを競合分析用に正規化する。

使用方法:
    uv run python scripts/process_internal_data.py data/internal/kintone_buyback_data_20251117.csv
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

def load_kintone_data(file_path: str) -> pd.DataFrame:
    """
    KintoneからエクスポートしたCSVを読み込む

    Args:
        file_path: CSVファイルのパス

    Returns:
        pandas.DataFrame
    """
    print(f"📂 読み込み中: {file_path}")

    # Shift-JISで読み込み（Kintoneのデフォルト）
    try:
        df = pd.read_csv(file_path, encoding='shift-jis')
        print(f"✅ {len(df):,}件のレコードを読み込みました")
    except UnicodeDecodeError:
        # UTF-8も試す
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        print(f"✅ {len(df):,}件のレコードを読み込みました（UTF-8）")

    return df

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    データクレンジング

    - 必須フィールドの確認
    - 空データの除外
    - iPhoneデータのみ抽出
    - 価格データの数値化
    """
    print("\n🧹 データクレンジング中...")

    original_count = len(df)

    # フィールド名の確認と標準化
    expected_fields = {
        'レコード番号': 'record_id',
        '機種': 'model',
        '容量': 'capacity',
        'ランク': 'rank',
        '最終買取価格': 'price',
        '進捗': 'status'
    }

    # フィールドの存在確認
    missing_fields = [f for f in expected_fields.keys() if f not in df.columns]
    if missing_fields:
        print(f"⚠️  警告: 以下のフィールドが見つかりません: {missing_fields}")
        print(f"   実際のフィールド: {list(df.columns)}")
        sys.exit(1)

    # フィールド名を英語に変換
    df = df.rename(columns=expected_fields)

    # 必須フィールドが空のレコードを除外
    df = df.dropna(subset=['model', 'capacity', 'rank', 'price'])
    print(f"  - 空データ除外: {original_count - len(df):,}件削除")

    # iPhoneのみ抽出
    original_count = len(df)
    df = df[df['model'].str.contains('iPhone', case=False, na=False)]
    print(f"  - iPhone抽出: {original_count - len(df):,}件除外（非iPhone）")

    # 価格を数値化
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    original_count = len(df)
    df = df.dropna(subset=['price'])
    print(f"  - 価格データ検証: {original_count - len(df):,}件除外（価格無効）")

    # 価格が0円のデータを除外
    original_count = len(df)
    df = df[df['price'] > 0]
    print(f"  - 0円データ除外: {original_count - len(df):,}件削除")

    print(f"✅ クレンジング後: {len(df):,}件")

    return df

def normalize_model_name(model: str) -> str:
    """
    機種名を正規化

    例:
        "iPhone 14 Pro" -> "iPhone 14 Pro"
        "iPhone SE（第3世代）" -> "iPhone SE (3rd Gen)"
        "iPhone13" -> "iPhone 13"
    """
    import re

    # スペースの統一
    model = model.strip()

    # 「iPhone13」→「iPhone 13」のようにスペースを追加
    model = re.sub(r'iPhone(\d+)', r'iPhone \1', model)

    # 世代表記の正規化
    model = model.replace('（第1世代）', ' (1st Gen)')
    model = model.replace('（第2世代）', ' (2nd Gen)')
    model = model.replace('（第3世代）', ' (3rd Gen)')

    return model

def normalize_capacity(capacity: str) -> str:
    """
    容量を正規化

    例:
        "128GB" -> "128GB"
        "128 GB" -> "128GB"
        "1TB" -> "1TB"
    """
    import re

    # スペース除去
    capacity = capacity.replace(' ', '')

    # 大文字に統一
    capacity = capacity.upper()

    return capacity

def normalize_rank(rank: str) -> str:
    """
    ランクを正規化

    Kintoneのランク → 競合サイトのランク表記に合わせる:
    - 新品・未開封 -> 新品
    - 新品同様（A） -> A
    - 美品（B） -> B
    - 使用感あり（C） -> C
    - 目立つ傷あり -> C（競合サイトではCランク相当）
    - 外装ジャンク -> ジャンク
    """
    rank_mapping = {
        '新品・未開封': '新品',
        '新品同様（A）': 'A',
        '新品同様': 'A',
        '美品（B）': 'B',
        '美品': 'B',
        '使用感あり（C）': 'C',
        '使用感あり': 'C',
        '目立つ傷あり': 'C',
        '傷あり': 'C',
        '外装ジャンク': 'ジャンク',
        'ジャンク': 'ジャンク',
    }

    return rank_mapping.get(rank, rank)

def extract_max_prices(df: pd.DataFrame) -> pd.DataFrame:
    """
    同一モデル・容量・ランクで最高価格を抽出

    理由: カラー違い等で同じモデルでも価格が異なる場合、
          競合比較では最高価格を採用する
    """
    print("\n💰 最高価格抽出中...")

    original_count = len(df)

    # 機種名・容量・ランクを正規化
    df['model_normalized'] = df['model'].apply(normalize_model_name)
    df['capacity_normalized'] = df['capacity'].apply(normalize_capacity)
    df['rank_normalized'] = df['rank'].apply(normalize_rank)

    # 同一モデル・容量・ランクでグループ化して最高価格を抽出
    df_max = df.loc[df.groupby(['model_normalized', 'capacity_normalized', 'rank_normalized'])['price'].idxmax()]

    print(f"  - 元データ: {original_count:,}件")
    print(f"  - 最高価格抽出後: {len(df_max):,}件")
    print(f"  - 削減: {original_count - len(df_max):,}件")

    return df_max

def create_normalized_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    競合データ形式に正規化

    出力形式:
        - 機種名
        - 容量
        - 買取ランク
        - 企業名: "弊社"
        - 買取価格
    """
    print("\n🔄 競合データ形式に正規化中...")

    normalized_df = pd.DataFrame({
        '機種名': df['model_normalized'],
        '容量': df['capacity_normalized'],
        '買取ランク': df['rank_normalized'],
        '企業名': '弊社',
        '買取価格': df['price'].astype(int)
    })

    # ソート: 機種名 -> 容量 -> ランク
    normalized_df = normalized_df.sort_values(['機種名', '容量', '買取ランク'])

    # 重複除外（念のため）
    original_count = len(normalized_df)
    normalized_df = normalized_df.drop_duplicates()

    if original_count > len(normalized_df):
        print(f"  - 重複除外: {original_count - len(normalized_df):,}件")

    print(f"✅ 正規化完了: {len(normalized_df):,}件")

    return normalized_df

def save_normalized_data(df: pd.DataFrame, output_dir: str = 'data/processed'):
    """
    正規化データを保存
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_path / 'normalized_internal_data.csv'
    output_file_timestamped = output_path / f'normalized_internal_data_{timestamp}.csv'

    # 保存
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    df.to_csv(output_file_timestamped, index=False, encoding='utf-8-sig')

    print(f"\n💾 保存完了:")
    print(f"  - {output_file}")
    print(f"  - {output_file_timestamped}")

    return output_file

def show_statistics(df: pd.DataFrame):
    """
    データの統計情報を表示
    """
    print("\n📊 データ統計:")
    print(f"  - 総件数: {len(df):,}件")
    print(f"  - ユニーク機種数: {df['機種名'].nunique()}機種")
    print(f"  - 価格範囲: ¥{df['買取価格'].min():,} 〜 ¥{df['買取価格'].max():,}")
    print(f"  - 平均価格: ¥{df['買取価格'].mean():,.0f}")
    print(f"  - 中央値: ¥{df['買取価格'].median():,.0f}")

    print("\n📋 ランク別件数:")
    rank_counts = df['買取ランク'].value_counts()
    for rank, count in rank_counts.items():
        print(f"  - {rank}: {count:,}件")

    print("\n🔝 買取価格TOP10:")
    top10 = df.nlargest(10, '買取価格')[['機種名', '容量', '買取ランク', '買取価格']]
    for idx, row in top10.iterrows():
        print(f"  {row['機種名']} {row['容量']} ({row['買取ランク']}): ¥{row['買取価格']:,}")

def main():
    """
    メイン処理
    """
    if len(sys.argv) < 2:
        print("使用方法: uv run python scripts/process_internal_data.py <CSVファイルパス>")
        print("例: uv run python scripts/process_internal_data.py data/internal/kintone_buyback_data_20251117.csv")
        sys.exit(1)

    input_file = sys.argv[1]

    if not Path(input_file).exists():
        print(f"❌ エラー: ファイルが見つかりません: {input_file}")
        sys.exit(1)

    print("=" * 60)
    print("弊社買取実績データ処理")
    print("=" * 60)

    # データ読み込み
    df = load_kintone_data(input_file)

    # データクレンジング
    df = clean_data(df)

    # 最高価格抽出
    df = extract_max_prices(df)

    # 正規化
    normalized_df = create_normalized_data(df)

    # 統計情報表示
    show_statistics(normalized_df)

    # 保存
    output_file = save_normalized_data(normalized_df)

    print("\n" + "=" * 60)
    print("✅ 処理完了")
    print("=" * 60)
    print(f"\n次のステップ:")
    print(f"  1. データ確認:")
    print(f"     uv run python scripts/view_csv.py {output_file}")
    print(f"  2. 3社比較分析:")
    print(f"     uv run python scripts/analyze_three_way.py")

if __name__ == '__main__':
    main()
