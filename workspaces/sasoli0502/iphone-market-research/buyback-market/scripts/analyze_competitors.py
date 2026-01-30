"""
競合買取価格の比較分析スクリプト

じゃんぱらとイオシスのデータを集計・分析してレポートを生成します。
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import re


def load_all_data(site: str) -> list[dict]:
    """指定サイトの全データを読み込み"""
    data_dir = Path(__file__).parent.parent / "data" / "raw" / site
    all_data = []

    if not data_dir.exists():
        print(f"⚠️ {site}のデータディレクトリが見つかりません: {data_dir}")
        return all_data

    json_files = list(data_dir.glob("*.json"))
    print(f"📂 {site}: {len(json_files)}ファイル発見")

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_data.extend(data)
                else:
                    all_data.append(data)
        except Exception as e:
            print(f"  ⚠️ 読み込みエラー: {json_file.name} - {e}")

    print(f"  ✓ {len(all_data)}件のデータを読み込み")
    return all_data


def normalize_model_name(model: str) -> str:
    """モデル名を正規化"""
    # 空白や改行を削除
    model = re.sub(r'\s+', ' ', model).strip()
    # "iPhone" の後の空白を統一
    model = re.sub(r'iPhone\s+', 'iPhone ', model)
    return model


def analyze_by_model(df: pd.DataFrame) -> pd.DataFrame:
    """モデル別の分析"""
    if df.empty:
        return pd.DataFrame()

    # モデル名を正規化
    df['model_normalized'] = df['model'].apply(normalize_model_name)

    # モデル+容量でグループ化
    grouped = df.groupby(['model_normalized', 'capacity', 'site'])

    stats = grouped['buyback_price'].agg([
        ('count', 'count'),
        ('mean', 'mean'),
        ('median', 'median'),
        ('min', 'min'),
        ('max', 'max'),
        ('std', 'std'),
    ]).reset_index()

    # 列名を日本語化
    stats.columns = ['モデル', '容量', 'サイト', 'データ件数', '平均価格', '中央値', '最安値', '最高値', '標準偏差']

    # 価格を整数に
    for col in ['平均価格', '中央値', '最安値', '最高値', '標準偏差']:
        stats[col] = stats[col].fillna(0).astype(int)

    # ソート
    stats = stats.sort_values(['モデル', '容量', 'サイト'])

    return stats


def create_comparison_table(df: pd.DataFrame) -> pd.DataFrame:
    """サイト間の価格比較表を作成"""
    if df.empty:
        return pd.DataFrame()

    # モデル名を正規化
    df['model_normalized'] = df['model'].apply(normalize_model_name)

    # モデル+容量+サイトでグループ化して中央値を取得
    pivot_data = []

    for (model, capacity), group in df.groupby(['model_normalized', 'capacity']):
        row = {
            'モデル': model,
            '容量': capacity,
        }

        for site in ['じゃんぱら', 'イオシス']:
            site_data = group[group['site'] == site]
            if not site_data.empty:
                row[f'{site}_中央値'] = int(site_data['buyback_price'].median())
                row[f'{site}_件数'] = len(site_data)
            else:
                row[f'{site}_中央値'] = None
                row[f'{site}_件数'] = 0

        # 価格差を計算
        if row.get('じゃんぱら_中央値') and row.get('イオシス_中央値'):
            diff = row['イオシス_中央値'] - row['じゃんぱら_中央値']
            row['価格差'] = diff
            row['価格差率'] = f"{(diff / row['じゃんぱら_中央値'] * 100):.1f}%"
        else:
            row['価格差'] = None
            row['価格差率'] = None

        pivot_data.append(row)

    comparison_df = pd.DataFrame(pivot_data)

    # ソート
    comparison_df = comparison_df.sort_values(['モデル', '容量'])

    return comparison_df


def create_normalized_data(df: pd.DataFrame) -> pd.DataFrame:
    """正規化データを作成（機種・容量・買取ランク・企業名のフィールド構造）"""
    if df.empty:
        return pd.DataFrame()

    # モデル名を正規化
    df['model_normalized'] = df['model'].apply(normalize_model_name)

    # 必要なフィールドを選択・リネーム
    normalized_df = df[['model_normalized', 'capacity', 'condition', 'site', 'buyback_price']].copy()
    normalized_df.columns = ['機種', '容量', '買取ランク', '企業名', '買取価格']

    # 重複を除外（同じ機種・容量・買取ランク・企業名・買取価格の組み合わせは1件のみ）
    normalized_df = normalized_df.drop_duplicates()

    # ソート（機種 → 容量 → 企業名 → 買取ランク → 買取価格）
    normalized_df = normalized_df.sort_values(['機種', '容量', '企業名', '買取ランク', '買取価格'], ascending=[True, True, True, True, False])

    # インデックスをリセット
    normalized_df = normalized_df.reset_index(drop=True)

    return normalized_df


def generate_report(janpara_data: list, iosys_data: list) -> None:
    """レポート生成"""
    print("\n" + "=" * 60)
    print("競合買取価格分析レポート生成")
    print("=" * 60)

    # データフレームに変換
    df_janpara = pd.DataFrame(janpara_data) if janpara_data else pd.DataFrame()
    df_iosys = pd.DataFrame(iosys_data) if iosys_data else pd.DataFrame()

    # 統合
    df_all = pd.concat([df_janpara, df_iosys], ignore_index=True)

    if df_all.empty:
        print("❌ 分析対象データがありません")
        return

    print(f"📊 総データ件数: {len(df_all)}件")
    print(f"  - じゃんぱら: {len(df_janpara)}件")
    print(f"  - イオシス: {len(df_iosys)}件")

    # 正規化データ作成
    print("\n📋 正規化データを作成中...")
    normalized_df = create_normalized_data(df_all)

    # モデル別統計
    print("📈 モデル別統計を作成中...")
    stats_df = analyze_by_model(df_all)

    # サイト間比較表
    print("🔄 サイト間比較表を作成中...")
    comparison_df = create_comparison_table(df_all)

    # レポート保存
    report_dir = Path(__file__).parent.parent / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # CSV保存（正規化データ）
    normalized_csv_path = report_dir / f"normalized_data_{timestamp}.csv"
    normalized_df.to_csv(normalized_csv_path, index=False, encoding='utf-8-sig')
    print(f"\n💾 正規化データ: {normalized_csv_path}")

    # CSV保存（モデル別統計）
    csv_path = report_dir / f"competitor_analysis_{timestamp}.csv"
    stats_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"💾 モデル別統計: {csv_path}")

    # CSV保存（サイト間比較）
    comparison_csv_path = report_dir / f"competitor_comparison_{timestamp}.csv"
    comparison_df.to_csv(comparison_csv_path, index=False, encoding='utf-8-sig')
    print(f"💾 サイト間比較: {comparison_csv_path}")

    # Excel保存（複数シート）
    excel_path = report_dir / f"competitor_analysis_{timestamp}.xlsx"
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        # サマリーシート
        summary_data = {
            '項目': [
                '分析日時',
                'じゃんぱらデータ件数',
                'イオシスデータ件数',
                '総データ件数',
                '分析モデル数',
            ],
            '値': [
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                len(df_janpara),
                len(df_iosys),
                len(df_all),
                len(df_all['model'].unique()) if 'model' in df_all.columns else 0,
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='1_サマリー', index=False)

        # 正規化データシート（最も重要）
        normalized_df.to_excel(writer, sheet_name='2_正規化データ', index=False)

        # サイト間比較シート
        comparison_df.to_excel(writer, sheet_name='3_サイト間比較', index=False)

        # モデル別統計シート
        stats_df.to_excel(writer, sheet_name='4_モデル別統計', index=False)

    print(f"💾 Excelレポート（4シート）: {excel_path}")

    # サマリー表示
    print("\n" + "=" * 60)
    print("📊 分析サマリー")
    print("=" * 60)

    if not comparison_df.empty:
        # 価格差のある主要モデルを表示
        comparison_with_diff = comparison_df[comparison_df['価格差'].notna()].copy()
        if not comparison_with_diff.empty:
            print("\n🔝 価格差が大きいモデル TOP10:")
            top10 = comparison_with_diff.nlargest(10, '価格差')
            for idx, row in top10.iterrows():
                print(f"  {row['モデル']} {row['容量']}")
                print(f"    じゃんぱら: ¥{row['じゃんぱら_中央値']:,} ({row['じゃんぱら_件数']}件)")
                print(f"    イオシス: ¥{row['イオシス_中央値']:,} ({row['イオシス_件数']}件)")
                print(f"    差額: ¥{row['価格差']:,} ({row['価格差率']})")
                print()

    print("\n✅ レポート生成完了")


def main():
    """メイン実行"""
    print("=" * 60)
    print("競合買取価格 分析")
    print("=" * 60)
    print()

    # データ読み込み
    janpara_data = load_all_data("janpara")
    iosys_data = load_all_data("iosys")

    # レポート生成
    generate_report(janpara_data, iosys_data)


if __name__ == "__main__":
    main()
