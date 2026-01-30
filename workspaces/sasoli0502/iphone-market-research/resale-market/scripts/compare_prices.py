"""
弊社販売価格と楽天市場の競合価格を比較分析
"""
import json
import re
from pathlib import Path
from typing import List, Dict
import pandas as pd
from datetime import datetime


def extract_rank(product_name: str) -> str:
    """
    商品名からランク情報を抽出（analyze.pyと同じロジック）

    Args:
        product_name: 商品名

    Returns:
        ランク情報（Aランク/Bランク/Cランク等）
    """
    name_upper = product_name.upper()

    # ジャンク品
    if 'ジャンク' in product_name or 'JUNK' in name_upper:
        return 'ジャンク'

    # Sランク（新品同様）
    if re.search(r'[【\[].*?S.*?ランク.*?[】\]]', product_name):
        return 'Sランク'
    if re.search(r'[【\[].*?未使用.*?[】\]]', product_name):
        return 'Sランク'

    # Aランク
    if re.search(r'[【\[].*?A.*?ランク.*?[】\]]', product_name):
        return 'Aランク'
    if re.search(r'[【\[].*?中古A.*?[】\]]', product_name):
        return 'Aランク'

    # Bランク
    if re.search(r'[【\[].*?B.*?ランク.*?[】\]]', product_name):
        return 'Bランク'
    if re.search(r'[【\[].*?中古B.*?[】\]]', product_name):
        return 'Bランク'

    # Cランク
    if re.search(r'[【\[].*?C.*?ランク.*?[】\]]', product_name):
        return 'Cランク'
    if re.search(r'[【\[].*?中古C.*?[】\]]', product_name):
        return 'Cランク'

    # 新品・未開封
    if '新品' in product_name or '未開封' in product_name:
        return '新品'

    # その他中古
    if '中古' in product_name:
        return '中古（ランク不明）'

    return 'ランク未確認'


def load_company_prices(csv_path: Path) -> pd.DataFrame:
    """
    弊社販売価格CSVを読み込み

    Args:
        csv_path: 弊社価格CSVファイルパス

    Returns:
        弊社価格DataFrame
    """
    df = pd.read_csv(csv_path, encoding='utf-8-sig')

    # A/B/Cランクのみにフィルタリング
    df = df[df['グレード'].isin(['A', 'B', 'C'])].copy()

    # カラム名を統一
    df = df.rename(columns={
        '機種': 'model',
        '容量': 'capacity',
        'グレード': 'rank',
        '平均売価': 'company_price'
    })

    # ランク名を統一（'A' → 'Aランク'）
    df['rank'] = df['rank'] + 'ランク'

    return df


def load_rakuten_data(rakuten_dir: Path) -> pd.DataFrame:
    """
    楽天市場データを読み込み、A/B/Cランク別に集計

    Args:
        rakuten_dir: 楽天データディレクトリ

    Returns:
        楽天価格統計DataFrame（機種×容量×ランク別）
    """
    all_products = []

    for json_file in rakuten_dir.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                all_products.extend(data)
        except Exception as e:
            print(f"エラー: {json_file} - {e}")

    if not all_products:
        return pd.DataFrame()

    df = pd.DataFrame(all_products)

    # ランク抽出
    df['rank'] = df['product_name'].apply(extract_rank)

    # A/B/Cランクのみにフィルタリング
    valid_ranks = ['Aランク', 'Bランク', 'Cランク']
    df = df[df['rank'].isin(valid_ranks)].copy()

    # 機種×容量×ランク別に集計
    rakuten_stats = (
        df.groupby(['model', 'capacity', 'rank'])
        .agg(
            rakuten_count=('price', 'count'),
            rakuten_min=('price', 'min'),
            rakuten_mean=('price', 'mean'),
            rakuten_median=('price', 'median'),
            rakuten_max=('price', 'max')
        )
        .round(0)
        .astype(int)
        .reset_index()
    )

    return rakuten_stats


def compare_prices(company_df: pd.DataFrame, rakuten_df: pd.DataFrame) -> pd.DataFrame:
    """
    弊社価格と楽天価格を比較

    Args:
        company_df: 弊社価格DataFrame
        rakuten_df: 楽天価格統計DataFrame

    Returns:
        比較結果DataFrame
    """
    # 機種×容量×ランクでマージ
    merged = pd.merge(
        company_df,
        rakuten_df,
        on=['model', 'capacity', 'rank'],
        how='left'
    )

    # 楽天データがない場合は0で埋める
    merged = merged.fillna(0).astype({
        'rakuten_count': int,
        'rakuten_min': int,
        'rakuten_mean': int,
        'rakuten_median': int,
        'rakuten_max': int
    })

    # 価格差計算
    merged['price_diff_yen'] = merged['company_price'] - merged['rakuten_mean']

    # 価格差率計算（楽天平均が0の場合は除外）
    merged['price_diff_pct'] = merged.apply(
        lambda row: round((row['price_diff_yen'] / row['rakuten_mean']) * 100, 1)
        if row['rakuten_mean'] > 0 else 0,
        axis=1
    )

    # 推奨価格計算（楽天平均 + 5%マージン）
    merged['recommended_price'] = merged.apply(
        lambda row: int(row['rakuten_mean'] * 1.05) if row['rakuten_mean'] > 0 else 0,
        axis=1
    )

    # カラム順序整理
    columns_order = [
        'model', 'capacity', 'rank',
        'company_price',
        'rakuten_count', 'rakuten_min', 'rakuten_mean', 'rakuten_median', 'rakuten_max',
        'price_diff_yen', 'price_diff_pct',
        'recommended_price'
    ]

    merged = merged[columns_order]

    # カラム名を日本語に変更
    merged = merged.rename(columns={
        'model': '機種',
        'capacity': '容量',
        'rank': 'ランク',
        'company_price': '弊社価格',
        'rakuten_count': '楽天商品数',
        'rakuten_min': '楽天最低',
        'rakuten_mean': '楽天平均',
        'rakuten_median': '楽天中央値',
        'rakuten_max': '楽天最高',
        'price_diff_yen': '価格差(円)',
        'price_diff_pct': '価格差(%)',
        'recommended_price': '推奨価格'
    })

    return merged


def create_comparison_report(data_dir: Path, output_dir: Path):
    """
    弊社価格と楽天価格の比較レポート作成

    Args:
        data_dir: データディレクトリ
        output_dir: 出力先ディレクトリ
    """
    print("=== 弊社価格 vs 楽天価格 比較分析開始 ===\n")

    # 弊社価格読み込み
    company_csv = data_dir / "company" / "backmarket_prices.csv"
    if not company_csv.exists():
        print(f"❌ 弊社価格ファイルが見つかりません: {company_csv}")
        return

    print(f"📂 弊社価格読み込み: {company_csv}")
    company_df = load_company_prices(company_csv)
    print(f"  弊社価格データ: {len(company_df)}件（A/B/Cのみ）\n")

    # 楽天データ読み込み
    rakuten_dir = data_dir / "raw" / "rakuten"
    if not rakuten_dir.exists():
        print(f"❌ 楽天データディレクトリが見つかりません: {rakuten_dir}")
        return

    print(f"📂 楽天データ読み込み: {rakuten_dir}")
    rakuten_df = load_rakuten_data(rakuten_dir)
    if rakuten_df.empty:
        print("❌ 楽天データが空です")
        return

    print(f"  楽天データ: {len(rakuten_df)}パターン（機種×容量×ランク）\n")

    # ランク別の統計表示
    print("  楽天データのランク別統計:")
    for rank in ['Aランク', 'Bランク', 'Cランク']:
        rank_data = rakuten_df[rakuten_df['rank'] == rank]
        if not rank_data.empty:
            total_count = rank_data['rakuten_count'].sum()
            print(f"    {rank}: {len(rank_data)}パターン、{total_count}商品")
    print()

    # 価格比較
    comparison_df = compare_prices(company_df, rakuten_df)

    # 保存
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Excel形式
    excel_path = output_dir / f"price_comparison_{timestamp}.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        # 全体
        comparison_df.to_excel(writer, sheet_name="全体比較", index=False)

        # ランク別シート
        for rank in ['Aランク', 'Bランク', 'Cランク']:
            rank_data = comparison_df[comparison_df['ランク'] == rank]
            if not rank_data.empty:
                rank_data.to_excel(writer, sheet_name=rank, index=False)

        # 価格差が大きい順（上位30件）
        high_diff = comparison_df[comparison_df['楽天商品数'] > 0].copy()
        high_diff = high_diff.sort_values('価格差(%)', ascending=False).head(30)
        high_diff.to_excel(writer, sheet_name="価格差大きい順", index=False)

        # 楽天データがないもの
        no_rakuten = comparison_df[comparison_df['楽天商品数'] == 0]
        if not no_rakuten.empty:
            no_rakuten.to_excel(writer, sheet_name="楽天データなし", index=False)

    print(f"✅ レポート保存: {excel_path}\n")

    # CSV形式
    csv_path = output_dir / f"price_comparison_{timestamp}.csv"
    comparison_df.to_csv(csv_path, encoding="utf-8-sig", index=False)
    print(f"✅ CSV保存: {csv_path}\n")

    # サマリー表示
    print("=== 比較サマリー ===")
    print(f"総比較件数: {len(comparison_df)}件")

    with_rakuten = comparison_df[comparison_df['楽天商品数'] > 0]
    print(f"楽天データあり: {len(with_rakuten)}件")
    print(f"楽天データなし: {len(comparison_df) - len(with_rakuten)}件\n")

    if not with_rakuten.empty:
        avg_diff = with_rakuten['価格差(円)'].mean()
        avg_diff_pct = with_rakuten['価格差(%)'].mean()
        print(f"平均価格差: {avg_diff:,.0f}円 ({avg_diff_pct:.1f}%)")
        print(f"  弊社が高い: {len(with_rakuten[with_rakuten['価格差(円)'] > 0])}件")
        print(f"  弊社が安い: {len(with_rakuten[with_rakuten['価格差(円)'] < 0])}件\n")

    # サンプル表示（上位10件）
    print("=== 価格比較サンプル（価格差が大きい順・上位10件） ===")
    sample = with_rakuten.sort_values('価格差(%)', ascending=False).head(10)
    print(sample.to_string(index=False))


def main():
    """メイン処理"""
    data_dir = Path(__file__).parent.parent / "data"
    output_dir = Path(__file__).parent.parent / "reports"

    create_comparison_report(data_dir, output_dir)


if __name__ == "__main__":
    main()
