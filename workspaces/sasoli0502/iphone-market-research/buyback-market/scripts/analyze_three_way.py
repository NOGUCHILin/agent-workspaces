#!/usr/bin/env python3
"""
3社比較分析スクリプト

弊社 vs じゃんぱら vs イオシスの買取価格を比較分析する。

使用方法:
    uv run python scripts/analyze_three_way.py
"""

from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

def load_data():
    """
    3社のデータを読み込んで結合
    """
    print("📂 データ読み込み中...")

    # 弊社データ
    internal_file = 'data/processed/normalized_internal_data.csv'
    if not Path(internal_file).exists():
        print(f"❌ エラー: 弊社データが見つかりません: {internal_file}")
        print("先に process_internal_data.py を実行してください")
        exit(1)

    df_internal = pd.read_csv(internal_file, encoding='utf-8-sig')
    print(f"  - 弊社: {len(df_internal):,}件")

    # 競合データ（じゃんぱら + イオシス）
    competitor_files = list(Path('reports').glob('normalized_data_*.csv'))
    if not competitor_files:
        print(f"❌ エラー: 競合データが見つかりません")
        print("先に analyze_competitors.py を実行してください")
        exit(1)

    # 最新の競合データを読み込み
    competitor_file = sorted(competitor_files)[-1]
    df_competitors = pd.read_csv(competitor_file, encoding='utf-8-sig')
    print(f"  - 競合データ: {len(df_competitors):,}件（{competitor_file.name}）")

    # フィールド名を統一（弊社は「機種名」、競合は「機種」）
    if '機種' in df_competitors.columns and '機種名' not in df_competitors.columns:
        df_competitors = df_competitors.rename(columns={'機種': '機種名'})

    # データ結合
    df_all = pd.concat([df_internal, df_competitors], ignore_index=True)
    print(f"✅ 総データ数: {len(df_all):,}件")

    return df_all

def normalize_model_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    機種名の表記揺れを統一

    例:
        - "iPhone SE (3rd Gen)" と "iPhone SE（第3世代）" を統一
    """
    print("\n🔄 機種名の正規化中...")

    # 機種名の表記揺れを統一
    df['機種名_正規化'] = df['機種名'].str.replace('（第3世代）', ' (3rd Gen)', regex=False)
    df['機種名_正規化'] = df['機種名_正規化'].str.replace('（第2世代）', ' (2nd Gen)', regex=False)
    df['機種名_正規化'] = df['機種名_正規化'].str.replace('（第1世代）', ' (1st Gen)', regex=False)

    # スペースの統一
    df['機種名_正規化'] = df['機種名_正規化'].str.strip()

    unique_before = df['機種名'].nunique()
    unique_after = df['機種名_正規化'].nunique()
    print(f"  - 正規化前: {unique_before}機種")
    print(f"  - 正規化後: {unique_after}機種")

    return df

def normalize_ranks(df: pd.DataFrame) -> pd.DataFrame:
    """
    買取ランクの表記を統一

    競合サイト:
        - じゃんぱら: 中古品、新品、ジャンク
        - イオシス: A, B, C, ジャンク

    弊社:
        - 新品、A, B, C, ジャンク

    統一後:
        - 新品
        - A（新品同様）
        - B（美品）
        - C（使用感あり）
        - ジャンク
    """
    print("\n🏷️  買取ランクの正規化中...")

    # じゃんぱらの「中古品」をマッピング
    # じゃんぱらの中古品は状態が幅広いため、Bランク相当とする
    rank_mapping = {
        '中古品': 'B',
        '新品': '新品',
        'ジャンク': 'ジャンク',
        'A': 'A',
        'B': 'B',
        'C': 'C',
    }

    df['買取ランク_正規化'] = df['買取ランク'].map(rank_mapping)

    # マッピングできなかったランクを確認
    unmapped = df[df['買取ランク_正規化'].isna()]['買取ランク'].unique()
    if len(unmapped) > 0:
        print(f"  ⚠️  警告: マッピングできなかったランク: {unmapped}")
        # マッピングできなかったものはそのまま使用
        df['買取ランク_正規化'] = df['買取ランク_正規化'].fillna(df['買取ランク'])

    rank_counts = df.groupby(['企業名', '買取ランク_正規化']).size().unstack(fill_value=0)
    print("\n  企業別ランク分布:")
    print(rank_counts)

    return df

def create_three_way_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """
    3社の価格を横並びで比較

    出力形式:
        機種名 | 容量 | ランク | 弊社 | じゃんぱら | イオシス | 最安 | 最高 | 弊社の順位
    """
    print("\n📊 3社比較テーブル作成中...")

    # ピボットテーブルで企業別に価格を展開
    comparison = df.pivot_table(
        index=['機種名_正規化', '容量', '買取ランク_正規化'],
        columns='企業名',
        values='買取価格',
        aggfunc='max'  # 同じ機種・容量・ランクで複数ある場合は最高値
    ).reset_index()

    # 企業名のカラムをフラットに
    comparison.columns.name = None
    comparison = comparison.rename(columns={
        '機種名_正規化': '機種名',
        '買取ランク_正規化': 'ランク'
    })

    # 最安値・最高値を計算
    price_columns = [col for col in comparison.columns if col in ['弊社', 'じゃんぱら', 'イオシス']]
    comparison['最安値'] = comparison[price_columns].min(axis=1)
    comparison['最高値'] = comparison[price_columns].max(axis=1)

    # 弊社の順位を計算（1位=最高価格、3位=最低価格）
    def calculate_rank(row):
        prices = []
        if pd.notna(row.get('弊社')):
            prices.append(('弊社', row['弊社']))
        if pd.notna(row.get('じゃんぱら')):
            prices.append(('じゃんぱら', row['じゃんぱら']))
        if pd.notna(row.get('イオシス')):
            prices.append(('イオシス', row['イオシス']))

        if not prices:
            return np.nan

        # 価格で降順ソート
        prices.sort(key=lambda x: x[1], reverse=True)

        # 弊社の順位を返す
        for i, (company, _) in enumerate(prices, 1):
            if company == '弊社':
                return i

        return np.nan

    comparison['弊社の順位'] = comparison.apply(calculate_rank, axis=1)

    # 価格差を計算（弊社 - 競合最高値）
    def calculate_price_diff(row):
        internal_price = row.get('弊社')
        if pd.isna(internal_price):
            return np.nan

        competitor_prices = []
        if pd.notna(row.get('じゃんぱら')):
            competitor_prices.append(row['じゃんぱら'])
        if pd.notna(row.get('イオシス')):
            competitor_prices.append(row['イオシス'])

        if not competitor_prices:
            return np.nan

        max_competitor = max(competitor_prices)
        return internal_price - max_competitor

    comparison['価格差（弊社-競合最高）'] = comparison.apply(calculate_price_diff, axis=1)

    # ソート: 価格差の大きい順
    comparison = comparison.sort_values('価格差（弊社-競合最高）', ascending=False)

    print(f"✅ 比較可能なモデル: {len(comparison):,}件")

    return comparison

def analyze_positioning(comparison: pd.DataFrame):
    """
    弊社の価格ポジショニング分析
    """
    print("\n" + "=" * 60)
    print("📈 弊社の価格ポジショニング分析")
    print("=" * 60)

    # 弊社データがあるレコードのみ
    internal_data = comparison[comparison['弊社'].notna()]

    if len(internal_data) == 0:
        print("⚠️  弊社データが見つかりません")
        return

    # 順位別の件数
    rank_counts = internal_data['弊社の順位'].value_counts().sort_index()
    total = len(internal_data)

    print("\n🏆 弊社の価格順位:")
    for rank, count in rank_counts.items():
        percentage = (count / total) * 100
        print(f"  {int(rank)}位: {count:,}件 ({percentage:.1f}%)")

    # 価格差の統計
    print("\n💰 価格差統計（弊社 - 競合最高値）:")
    price_diff = internal_data['価格差（弊社-競合最高）'].dropna()
    print(f"  - 平均: ¥{price_diff.mean():,.0f}")
    print(f"  - 中央値: ¥{price_diff.median():,.0f}")
    print(f"  - 最大（弊社が高い）: ¥{price_diff.max():,.0f}")
    print(f"  - 最小（弊社が安い）: ¥{price_diff.min():,.0f}")

    # 競合より高い・安い件数
    higher = len(price_diff[price_diff > 0])
    lower = len(price_diff[price_diff < 0])
    equal = len(price_diff[price_diff == 0])

    print(f"\n  - 競合より高く買い取る: {higher}件 ({higher/len(price_diff)*100:.1f}%)")
    print(f"  - 競合より安く買い取る: {lower}件 ({lower/len(price_diff)*100:.1f}%)")
    print(f"  - 競合と同額: {equal}件 ({equal/len(price_diff)*100:.1f}%)")

def show_top_differences(comparison: pd.DataFrame, n: int = 10):
    """
    価格差が大きいモデルを表示
    """
    print("\n" + "=" * 60)
    print(f"🔝 弊社が競合より高く買い取るモデル TOP{n}")
    print("=" * 60)

    # 弊社データがあり、価格差がプラスのもの
    top_higher = comparison[
        (comparison['弊社'].notna()) &
        (comparison['価格差（弊社-競合最高）'] > 0)
    ].head(n)

    for idx, row in top_higher.iterrows():
        diff = row['価格差（弊社-競合最高）']
        internal = row['弊社']
        janpara = row.get('じゃんぱら', np.nan)
        iosys = row.get('イオシス', np.nan)

        competitor_max = max([p for p in [janpara, iosys] if pd.notna(p)], default=0)
        diff_pct = (diff / competitor_max * 100) if competitor_max > 0 else 0

        print(f"\n{row['機種名']} {row['容量']} ({row['ランク']})")
        print(f"  弊社: ¥{internal:,.0f}")
        if pd.notna(janpara):
            print(f"  じゃんぱら: ¥{janpara:,.0f}")
        if pd.notna(iosys):
            print(f"  イオシス: ¥{iosys:,.0f}")
        print(f"  📈 差額: +¥{diff:,.0f} ({diff_pct:+.1f}%)")

    print("\n" + "=" * 60)
    print(f"🔻 弊社が競合より安く買い取るモデル TOP{n}")
    print("=" * 60)

    # 弊社データがあり、価格差がマイナスのもの
    top_lower = comparison[
        (comparison['弊社'].notna()) &
        (comparison['価格差（弊社-競合最高）'] < 0)
    ].tail(n)

    for idx, row in top_lower.iterrows():
        diff = row['価格差（弊社-競合最高）']
        internal = row['弊社']
        janpara = row.get('じゃんぱら', np.nan)
        iosys = row.get('イオシス', np.nan)

        competitor_max = max([p for p in [janpara, iosys] if pd.notna(p)], default=0)
        diff_pct = (diff / competitor_max * 100) if competitor_max > 0 else 0

        print(f"\n{row['機種名']} {row['容量']} ({row['ランク']})")
        print(f"  弊社: ¥{internal:,.0f}")
        if pd.notna(janpara):
            print(f"  じゃんぱら: ¥{janpara:,.0f}")
        if pd.notna(iosys):
            print(f"  イオシス: ¥{iosys:,.0f}")
        print(f"  📉 差額: ¥{diff:,.0f} ({diff_pct:.1f}%)")

def save_reports(comparison: pd.DataFrame, df_all: pd.DataFrame):
    """
    レポートを保存
    """
    print("\n💾 レポート保存中...")

    output_dir = Path('reports')
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # 1. 3社比較CSV
    output_file = output_dir / f'three_way_comparison_{timestamp}.csv'
    comparison.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"  ✅ {output_file}")

    # 2. 3社比較Excel（見やすく整形）
    excel_file = output_dir / f'three_way_analysis_{timestamp}.xlsx'

    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        # シート1: サマリー
        summary_data = {
            '項目': [
                '総データ数',
                '弊社データ数',
                'じゃんぱらデータ数',
                'イオシスデータ数',
                '比較可能モデル数',
                '弊社が1位の件数',
                '弊社が2位の件数',
                '弊社が3位の件数',
            ],
            '値': [
                len(df_all),
                len(df_all[df_all['企業名'] == '弊社']),
                len(df_all[df_all['企業名'] == 'じゃんぱら']),
                len(df_all[df_all['企業名'] == 'イオシス']),
                len(comparison),
                len(comparison[comparison['弊社の順位'] == 1]),
                len(comparison[comparison['弊社の順位'] == 2]),
                len(comparison[comparison['弊社の順位'] == 3]),
            ]
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='1_サマリー', index=False)

        # シート2: 3社比較（全データ）
        comparison.to_excel(writer, sheet_name='2_3社比較', index=False)

        # シート3: 弊社が強いモデル（価格差プラス）
        strong_models = comparison[
            (comparison['弊社'].notna()) &
            (comparison['価格差（弊社-競合最高）'] > 0)
        ].sort_values('価格差（弊社-競合最高）', ascending=False)
        strong_models.to_excel(writer, sheet_name='3_弊社が強いモデル', index=False)

        # シート4: 弊社が弱いモデル（価格差マイナス）
        weak_models = comparison[
            (comparison['弊社'].notna()) &
            (comparison['価格差（弊社-競合最高）'] < 0)
        ].sort_values('価格差（弊社-競合最高）', ascending=True)
        weak_models.to_excel(writer, sheet_name='4_弊社が弱いモデル', index=False)

    print(f"  ✅ {excel_file}")

    # 3. HTMLビューアー
    html_file = output_dir / f'three_way_comparison_{timestamp}.html'
    html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3社比較分析 - {timestamp}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-top: 20px;
        }}
        th {{
            background: #4CAF50;
            color: white;
            padding: 12px;
            text-align: left;
            position: sticky;
            top: 0;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .rank-1 {{ background: #gold; font-weight: bold; }}
        .rank-2 {{ background: #silver; }}
        .rank-3 {{ background: #cd7f32; }}
        .positive {{ color: #4CAF50; font-weight: bold; }}
        .negative {{ color: #f44336; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>📊 3社買取価格比較分析</h1>
    <p>生成日時: {timestamp}</p>

    {comparison.to_html(index=False, classes='data-table', escape=False)}
</body>
</html>
"""
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"  ✅ {html_file}")

def main():
    """
    メイン処理
    """
    print("=" * 60)
    print("3社比較分析（弊社 vs じゃんぱら vs イオシス）")
    print("=" * 60)

    # データ読み込み
    df_all = load_data()

    # 機種名・ランクの正規化
    df_all = normalize_model_names(df_all)
    df_all = normalize_ranks(df_all)

    # 3社比較テーブル作成
    comparison = create_three_way_comparison(df_all)

    # 分析
    analyze_positioning(comparison)
    show_top_differences(comparison, n=10)

    # レポート保存
    save_reports(comparison, df_all)

    print("\n" + "=" * 60)
    print("✅ 分析完了")
    print("=" * 60)

if __name__ == '__main__':
    main()
