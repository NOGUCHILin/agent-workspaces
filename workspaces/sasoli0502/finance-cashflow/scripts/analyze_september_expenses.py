"""
9月のクレカ取引明細から通信費・消耗品費・その他の内訳を分析
"""
import pandas as pd
from pathlib import Path

def analyze_september_expenses():
    # データ読み込み
    data_path = Path(__file__).parent.parent / 'data' / 'credit_card_transactions.csv'
    df = pd.read_csv(data_path)

    # 日付変換
    df['取引日'] = pd.to_datetime(df['取引日'])

    # 9月データを抽出
    sept_df = df[df['取引日'].dt.month == 9].copy()

    print("=" * 80)
    print("2025年9月 クレジットカード取引分析")
    print("=" * 80)
    print(f"\n総取引件数: {len(sept_df)}件")

    # 勘定科目別の集計
    print("\n【勘定科目別 集計】")
    print("-" * 80)
    category_summary = sept_df.groupby('借方勘定科目')['借方金額(円)'].agg(['sum', 'count'])
    category_summary = category_summary.sort_values('sum', ascending=False)
    category_summary['sum'] = category_summary['sum'].apply(lambda x: f"{x:,.0f}円")
    print(category_summary.to_string())

    # 通信費の詳細
    print("\n\n【通信費 詳細】")
    print("-" * 80)
    comm_df = sept_df[sept_df['借方勘定科目'] == '通信費'].copy()
    comm_summary = comm_df.groupby('摘要')['借方金額(円)'].agg(['sum', 'count'])
    comm_summary = comm_summary.sort_values('sum', ascending=False)
    print(f"通信費合計: {comm_df['借方金額(円)'].sum():,.0f}円 ({len(comm_df)}件)")
    print("\n内訳:")
    for idx, row in comm_summary.iterrows():
        print(f"  {idx:<50} {row['sum']:>12,.0f}円 ({row['count']:>2}件)")

    # 備品・消耗品費の詳細
    print("\n\n【備品・消耗品費 詳細】")
    print("-" * 80)
    supply_df = sept_df[sept_df['借方勘定科目'] == '備品・消耗品費'].copy()
    supply_summary = supply_df.groupby('摘要')['借方金額(円)'].agg(['sum', 'count'])
    supply_summary = supply_summary.sort_values('sum', ascending=False)
    print(f"備品・消耗品費合計: {supply_df['借方金額(円)'].sum():,.0f}円 ({len(supply_df)}件)")
    print("\n内訳 (上位20件):")
    for idx, row in supply_summary.head(20).iterrows():
        print(f"  {idx:<50} {row['sum']:>12,.0f}円 ({row['count']:>2}件)")

    # 支払手数料の詳細
    print("\n\n【支払手数料 詳細】")
    print("-" * 80)
    fee_df = sept_df[sept_df['借方勘定科目'] == '支払手数料'].copy()
    fee_summary = fee_df.groupby('摘要')['借方金額(円)'].agg(['sum', 'count'])
    fee_summary = fee_summary.sort_values('sum', ascending=False)
    print(f"支払手数料合計: {fee_df['借方金額(円)'].sum():,.0f}円 ({len(fee_df)}件)")
    print("\n内訳:")
    for idx, row in fee_summary.iterrows():
        print(f"  {idx:<50} {row['sum']:>12,.0f}円 ({row['count']:>2}件)")

    # 広告宣伝費の詳細
    print("\n\n【広告宣伝費 詳細】")
    print("-" * 80)
    ad_df = sept_df[sept_df['借方勘定科目'] == '広告宣伝費'].copy()
    ad_summary = ad_df.groupby('摘要')['借方金額(円)'].agg(['sum', 'count'])
    ad_summary = ad_summary.sort_values('sum', ascending=False)
    print(f"広告宣伝費合計: {ad_df['借方金額(円)'].sum():,.0f}円 ({len(ad_df)}件)")
    print("\n内訳:")
    for idx, row in ad_summary.iterrows():
        print(f"  {idx:<50} {row['sum']:>12,.0f}円 ({row['count']:>2}件)")

    # 仮払金（広告チャージ）の詳細
    print("\n\n【仮払金（広告チャージ） 詳細】")
    print("-" * 80)
    prepaid_df = sept_df[sept_df['借方勘定科目'] == '仮払金'].copy()
    prepaid_summary = prepaid_df.groupby('摘要')['借方金額(円)'].agg(['sum', 'count'])
    prepaid_summary = prepaid_summary.sort_values('sum', ascending=False)
    print(f"仮払金合計: {prepaid_df['借方金額(円)'].sum():,.0f}円 ({len(prepaid_df)}件)")
    print("\n内訳:")
    for idx, row in prepaid_summary.iterrows():
        print(f"  {idx:<50} {row['sum']:>12,.0f}円 ({row['count']:>2}件)")

    # カード別集計
    print("\n\n【カード別 集計】")
    print("-" * 80)
    card_summary = sept_df.groupby('貸方補助科目')['借方金額(円)'].sum()
    card_summary = card_summary.sort_values(ascending=False)
    print("カード別利用額:")
    for card, amount in card_summary.items():
        print(f"  {card:<30} {amount:>12,.0f}円")

    print("\n" + "=" * 80)

if __name__ == '__main__':
    analyze_september_expenses()
