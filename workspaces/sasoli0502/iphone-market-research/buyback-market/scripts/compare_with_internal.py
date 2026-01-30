"""
弊社買取価格と競合価格の比較分析

弊社の掲示価格とじゃんぱら・イオシスの掲示価格を比較し、
価格差や競争力を分析します。
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import re


# パス設定
BASE_DIR = Path(__file__).parent.parent
INTERNAL_DATA = BASE_DIR / "data" / "internal" / "buyback_history.csv"
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
REPORTS_DIR = BASE_DIR / "reports"


def normalize_model_name(name: str) -> str:
    """
    モデル名を正規化

    例:
    - "iPhone 15 Pro" → "iPhone 15 Pro"
    - "iPhone SE（第3世代）" → "iPhone SE (第3世代)"
    """
    # 全角括弧を半角に
    name = name.replace("（", "(").replace("）", ")")
    return name.strip()


def normalize_capacity(capacity: str) -> str:
    """
    容量を正規化

    例:
    - "256GB" → "256GB"
    - "1TB" → "1TB"
    """
    return str(capacity).strip()


def normalize_condition(condition: str) -> str:
    """
    状態を正規化

    弊社の状態 → 競合の状態にマッピング
    """
    condition_map = {
        "新品・未開封": "未使用品",
        "新品同様": "中古品",
        "美品": "中古品",
        "使用感あり": "中古品",
        "目立つ傷あり": "中古品",
        "外装ジャンク": "中古品",
    }
    return condition_map.get(condition, "中古品")


def load_internal_data():
    """弊社の買取価格データを読み込み"""
    print("📂 弊社データ読み込み中...")

    df = pd.read_csv(INTERNAL_DATA, encoding='utf-8-sig')

    # カラム名を正規化
    df.columns = df.columns.str.strip()

    # 必要なカラムをチェック
    required_cols = ['機体型番', '記憶容量', '等級', '高額買取価格']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"必須カラムが見つかりません: {col}")

    # データを正規化
    df['model'] = df['機体型番'].apply(normalize_model_name)
    df['capacity'] = df['記憶容量'].apply(normalize_capacity)
    df['condition_original'] = df['等級']
    df['condition'] = df['等級'].apply(normalize_condition)
    df['buyback_price'] = pd.to_numeric(df['高額買取価格'], errors='coerce')

    # 必要なカラムのみ抽出
    df = df[['model', 'capacity', 'condition_original', 'condition', 'buyback_price']]

    # 欠損値を削除
    df = df.dropna(subset=['buyback_price'])

    print(f"  ✓ {len(df)}件のデータを読み込み")

    return df


def load_competitor_data():
    """競合の買取価格データを読み込み"""
    print("\n📂 競合データ読み込み中...")

    all_data = []

    # じゃんぱらのデータ
    janpara_dir = RAW_DATA_DIR / "janpara"
    if janpara_dir.exists():
        janpara_files = list(janpara_dir.glob("*.json"))
        for file in janpara_files:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_data.extend(data)
        print(f"  ✓ じゃんぱら: {len(janpara_files)}ファイル")

    # イオシスのデータ
    iosys_dir = RAW_DATA_DIR / "iosys"
    if iosys_dir.exists():
        iosys_files = list(iosys_dir.glob("*.json"))
        for file in iosys_files:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_data.extend(data)
        print(f"  ✓ イオシス: {len(iosys_files)}ファイル")

    # DataFrameに変換
    df = pd.DataFrame(all_data)

    # 必要なカラムをチェック
    if 'model' in df.columns and 'capacity' in df.columns:
        df['model'] = df['model'].apply(normalize_model_name)
        df['capacity'] = df['capacity'].apply(normalize_capacity)

    print(f"  ✓ 合計 {len(df)}件のデータを読み込み")

    return df


def calculate_competitor_avg_price(competitor_df):
    """
    競合の平均価格を計算

    モデル×容量×状態ごとにグループ化して平均価格を算出
    """
    print("\n📊 競合の平均価格を計算中...")

    # モデル×容量×状態ごとにグループ化
    grouped = competitor_df.groupby(['model', 'capacity', 'condition']).agg({
        'buyback_price': ['mean', 'min', 'max', 'count'],
        'site': lambda x: ', '.join(sorted(set(x)))
    }).reset_index()

    # カラム名をフラット化
    grouped.columns = ['model', 'capacity', 'condition', 'avg_price', 'min_price', 'max_price', 'data_count', 'sites']

    print(f"  ✓ {len(grouped)}件のユニークな組み合わせ")

    return grouped


def compare_prices(internal_df, competitor_avg_df):
    """
    弊社価格と競合価格を比較
    """
    print("\n🔍 価格比較中...")

    # 弊社データと競合データをマージ
    # 弊社は状態別、競合は平均値（状態は「中古品」または「未使用品」）
    merged = internal_df.merge(
        competitor_avg_df,
        on=['model', 'capacity', 'condition'],
        how='left'
    )

    # 価格差を計算
    merged['price_diff'] = merged['buyback_price'] - merged['avg_price']
    merged['price_diff_pct'] = (merged['price_diff'] / merged['avg_price'] * 100).round(1)

    # 競争力の判定
    def judge_competitiveness(diff_pct):
        if pd.isna(diff_pct):
            return "データなし"
        elif diff_pct >= 10:
            return "かなり高い"
        elif diff_pct >= 5:
            return "やや高い"
        elif diff_pct >= -5:
            return "同水準"
        elif diff_pct >= -10:
            return "やや低い"
        else:
            return "かなり低い"

    merged['competitiveness'] = merged['price_diff_pct'].apply(judge_competitiveness)

    print(f"  ✓ {len(merged)}件の比較データを生成")

    return merged


def generate_summary(comparison_df):
    """
    サマリーレポートを生成
    """
    print("\n📈 サマリー生成中...")

    # 競合データがあるものだけを抽出
    valid_data = comparison_df[comparison_df['avg_price'].notna()].copy()

    if len(valid_data) == 0:
        print("  ⚠️ 競合データとマッチするデータがありません")
        return None

    # 競争力別の集計
    competitiveness_summary = valid_data['competitiveness'].value_counts().to_dict()

    # 価格差の統計
    price_stats = {
        "平均価格差": f"¥{valid_data['price_diff'].mean():,.0f}",
        "平均価格差率": f"{valid_data['price_diff_pct'].mean():.1f}%",
        "最大価格差": f"¥{valid_data['price_diff'].max():,.0f}",
        "最小価格差": f"¥{valid_data['price_diff'].min():,.0f}",
    }

    # 弊社の方が高いモデルTOP10
    high_price_models = valid_data.nlargest(10, 'price_diff')[
        ['model', 'capacity', 'condition_original', 'buyback_price', 'avg_price', 'price_diff', 'price_diff_pct']
    ]

    # 弊社の方が低いモデルTOP10
    low_price_models = valid_data.nsmallest(10, 'price_diff')[
        ['model', 'capacity', 'condition_original', 'buyback_price', 'avg_price', 'price_diff', 'price_diff_pct']
    ]

    summary = {
        "total_models": len(valid_data),
        "competitiveness_summary": competitiveness_summary,
        "price_stats": price_stats,
        "high_price_models": high_price_models,
        "low_price_models": low_price_models,
    }

    return summary


def save_reports(comparison_df, summary):
    """
    レポートを保存
    """
    print("\n💾 レポート保存中...")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # 1. 詳細比較レポート（CSV）
    csv_path = REPORTS_DIR / f"internal_vs_competitor_{timestamp}.csv"
    comparison_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"  ✓ 詳細比較: {csv_path}")

    # 2. Excelレポート（複数シート）
    excel_path = REPORTS_DIR / f"internal_vs_competitor_{timestamp}.xlsx"
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        # シート1: 全データ
        comparison_df.to_excel(writer, sheet_name='全データ', index=False)

        # シート2: 弊社が高いモデルTOP20
        if summary:
            high_models = summary['high_price_models'].copy()
            high_models.to_excel(writer, sheet_name='弊社が高いTOP20', index=False)

            # シート3: 弊社が低いモデルTOP20
            low_models = summary['low_price_models'].copy()
            low_models.to_excel(writer, sheet_name='弊社が低いTOP20', index=False)

    print(f"  ✓ Excelレポート: {excel_path}")

    return excel_path


def print_summary(summary):
    """
    サマリーをコンソールに表示
    """
    if not summary:
        return

    print("\n" + "=" * 60)
    print("📊 弊社 vs 競合 価格比較サマリー")
    print("=" * 60)

    print(f"\n📈 分析対象: {summary['total_models']}件")

    print("\n🏆 競争力の分布:")
    for key, value in summary['competitiveness_summary'].items():
        print(f"  {key}: {value}件")

    print("\n💰 価格差の統計:")
    for key, value in summary['price_stats'].items():
        print(f"  {key}: {value}")

    print("\n⬆️ 弊社の方が高いモデル TOP5:")
    for idx, row in summary['high_price_models'].head(5).iterrows():
        print(f"  {row['model']} {row['capacity']} ({row['condition_original']})")
        print(f"    弊社: ¥{row['buyback_price']:,.0f}")
        print(f"    競合平均: ¥{row['avg_price']:,.0f}")
        print(f"    差額: ¥{row['price_diff']:,.0f} ({row['price_diff_pct']:+.1f}%)")
        print()

    print("⬇️ 弊社の方が低いモデル TOP5:")
    for idx, row in summary['low_price_models'].head(5).iterrows():
        print(f"  {row['model']} {row['capacity']} ({row['condition_original']})")
        print(f"    弊社: ¥{row['buyback_price']:,.0f}")
        print(f"    競合平均: ¥{row['avg_price']:,.0f}")
        print(f"    差額: ¥{row['price_diff']:,.0f} ({row['price_diff_pct']:+.1f}%)")
        print()


def main():
    """メイン処理"""
    print("\n" + "=" * 60)
    print("弊社 vs 競合 買取価格比較分析")
    print("=" * 60)

    # データ読み込み
    internal_df = load_internal_data()
    competitor_df = load_competitor_data()

    # 競合の平均価格を計算
    competitor_avg_df = calculate_competitor_avg_price(competitor_df)

    # 価格比較
    comparison_df = compare_prices(internal_df, competitor_avg_df)

    # サマリー生成
    summary = generate_summary(comparison_df)

    # レポート保存
    excel_path = save_reports(comparison_df, summary)

    # サマリー表示
    print_summary(summary)

    print("\n" + "=" * 60)
    print("✅ 分析完了")
    print("=" * 60)
    print(f"\n📊 レポート: {excel_path}")


if __name__ == "__main__":
    main()
