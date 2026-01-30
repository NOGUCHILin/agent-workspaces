"""
収集した価格データの分析
"""
import json
import re
from pathlib import Path
from typing import List, Dict
import pandas as pd
from datetime import datetime


def extract_rank(product_name: str) -> str:
    """
    商品名からランク情報を抽出

    Args:
        product_name: 商品名

    Returns:
        ランク情報（未確認/Aランク/Bランク/Cランク/ジャンク等）
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


def load_json_files(directory: Path) -> List[Dict]:
    """
    指定ディレクトリ内のJSONファイルを全て読み込み

    Args:
        directory: 対象ディレクトリ

    Returns:
        全商品データのリスト
    """
    all_products = []

    if not directory.exists():
        return all_products

    for json_file in directory.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                all_products.extend(data)
        except Exception as e:
            print(f"エラー: {json_file} - {e}")

    return all_products


def analyze_channel(channel_name: str, products: List[Dict]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    チャネルごとの価格分析

    Args:
        channel_name: チャネル名
        products: 商品データのリスト

    Returns:
        (基本集計DataFrame, ランク別集計DataFrame)のタプル
    """
    if not products:
        print(f"  {channel_name}: データなし")
        return pd.DataFrame(), pd.DataFrame()

    df = pd.DataFrame(products)

    # ランク情報を抽出
    df['rank'] = df['product_name'].apply(extract_rank)

    # A/B/Cランクのみにフィルタリング
    valid_ranks = ['Aランク', 'Bランク', 'Cランク']
    df_filtered = df[df['rank'].isin(valid_ranks)].copy()

    if df_filtered.empty:
        print(f"  {channel_name}: A/B/Cランクのデータなし（総データ数: {len(df)}件）")
        return pd.DataFrame(), pd.DataFrame()

    # フィルタリング結果の表示
    print(f"  {channel_name}: 総データ数 {len(df)}件 → A/B/Cランク {len(df_filtered)}件に絞り込み")
    excluded_count = len(df) - len(df_filtered)
    if excluded_count > 0:
        excluded_ranks = df[~df['rank'].isin(valid_ranks)]['rank'].value_counts()
        print(f"    除外: {excluded_count}件")
        for rank, count in excluded_ranks.items():
            print(f"      {rank}: {count}件")

    # 基本集計: モデル×容量ごとに集計（A/B/Cのみ）
    summary = (
        df_filtered.groupby(["model", "capacity"])
        .agg(
            商品数=("price", "count"),
            最低価格=("price", "min"),
            平均価格=("price", "mean"),
            中央値=("price", "median"),
            最高価格=("price", "max"),
        )
        .round(0)
        .astype(int)
    )
    summary["チャネル"] = channel_name

    # ランク別集計: モデル×容量×ランクごとに集計（A/B/Cのみ）
    rank_summary = (
        df_filtered.groupby(["model", "capacity", "rank"])
        .agg(
            商品数=("price", "count"),
            最低価格=("price", "min"),
            平均価格=("price", "mean"),
            中央値=("price", "median"),
            最高価格=("price", "max"),
        )
        .round(0)
        .astype(int)
    )
    rank_summary["チャネル"] = channel_name

    # A/B/Cランクの分布表示
    rank_dist = df_filtered['rank'].value_counts()
    print(f"    A/B/Cランク分布:")
    for rank, count in rank_dist.items():
        print(f"      {rank}: {count}件")

    return summary, rank_summary


def create_price_report(data_dir: Path, output_dir: Path):
    """
    相場レポート作成

    Args:
        data_dir: 生データディレクトリ
        output_dir: 出力先ディレクトリ
    """
    print("=== 価格分析開始 ===")

    all_summaries = []
    all_rank_summaries = []

    # 楽天市場
    rakuten_dir = data_dir / "rakuten"
    if rakuten_dir.exists():
        print("\n【楽天市場】")
        rakuten_products = load_json_files(rakuten_dir)
        rakuten_summary, rakuten_rank_summary = analyze_channel("楽天市場", rakuten_products)
        if not rakuten_summary.empty:
            all_summaries.append(rakuten_summary)
            all_rank_summaries.append(rakuten_rank_summary)

    # Yahoo!ショッピング
    yahoo_dir = data_dir / "yahoo"
    if yahoo_dir.exists():
        print("\n【Yahoo!ショッピング】")
        yahoo_products = load_json_files(yahoo_dir)
        yahoo_summary, yahoo_rank_summary = analyze_channel("Yahoo!ショッピング", yahoo_products)
        if not yahoo_summary.empty:
            all_summaries.append(yahoo_summary)
            all_rank_summaries.append(yahoo_rank_summary)

    if not all_summaries:
        print("\n❌ 分析対象のデータがありません")
        return

    # 統合
    combined = pd.concat(all_summaries)
    combined_rank = pd.concat(all_rank_summaries)

    # 保存
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Excel形式
    excel_path = output_dir / f"iphone_price_report_{timestamp}.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        # 基本集計: チャネル別シート
        for channel in combined["チャネル"].unique():
            channel_data = combined[combined["チャネル"] == channel].drop(
                columns=["チャネル"]
            )
            channel_data.to_excel(writer, sheet_name=f"{channel}_基本")

        # 基本集計: 全体統合シート
        combined.to_excel(writer, sheet_name="全チャネル統合")

        # ランク別集計: チャネル別シート
        for channel in combined_rank["チャネル"].unique():
            channel_rank_data = combined_rank[combined_rank["チャネル"] == channel].drop(
                columns=["チャネル"]
            )
            channel_rank_data.to_excel(writer, sheet_name=f"{channel}_ランク別")

        # ランク別集計: 全体統合シート
        combined_rank.to_excel(writer, sheet_name="全チャネル_ランク別")

    print(f"\n✅ レポート保存: {excel_path}")

    # CSV形式（基本集計）
    csv_path = output_dir / f"iphone_price_report_{timestamp}.csv"
    combined.to_csv(csv_path, encoding="utf-8-sig")
    print(f"✅ CSV保存（基本集計）: {csv_path}")

    # CSV形式（ランク別集計）
    csv_rank_path = output_dir / f"iphone_price_report_rank_{timestamp}.csv"
    combined_rank.to_csv(csv_rank_path, encoding="utf-8-sig")
    print(f"✅ CSV保存（ランク別）: {csv_rank_path}")

    # サマリー表示
    print("\n=== 価格サマリー（基本集計・一部抜粋） ===")
    print(combined.head(10).to_string())

    print("\n=== 価格サマリー（ランク別集計・一部抜粋） ===")
    print(combined_rank.head(15).to_string())


def main():
    """メイン処理"""
    data_dir = Path(__file__).parent.parent / "data" / "raw"
    output_dir = Path(__file__).parent.parent / "reports"

    create_price_report(data_dir, output_dir)


if __name__ == "__main__":
    main()
