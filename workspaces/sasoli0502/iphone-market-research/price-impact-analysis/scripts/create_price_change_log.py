"""
買取価格変更履歴の自動生成スクリプト

使い方:
    # 2つの買取価格CSVを比較して変更履歴を生成
    uv run python scripts/create_price_change_log.py \
        --before 買取価格20251118.csv \
        --after 買取価格20251119.csv \
        --change-date 2025-11-19

    # 親ディレクトリの最新2ファイルを自動検出して比較
    uv run python scripts/create_price_change_log.py --auto

機能:
    - 2つの買取価格CSVを比較
    - 価格が変更された行のみを抽出
    - price_changes.csv に追記
"""

import pandas as pd
import argparse
from pathlib import Path
from datetime import datetime
import glob

# ============================================================
# 設定
# ============================================================

BASE_DIR = Path(__file__).parent.parent
PARENT_DIR = BASE_DIR.parent
PRICE_CHANGES_DIR = BASE_DIR / "data" / "price_changes"
PRICE_CHANGES_FILE = PRICE_CHANGES_DIR / "price_changes.csv"

# ============================================================
# 買取価格CSVの読み込み
# ============================================================

def load_buyback_price(file_path: Path) -> pd.DataFrame:
    """
    買取価格CSVを読み込み

    Args:
        file_path: CSVファイルパス

    Returns:
        DataFrame
    """
    df = pd.read_csv(file_path)

    # BOMを削除（もしあれば）
    df.columns = df.columns.str.replace('\ufeff', '')

    # カラム名を正規化
    column_mapping = {
        '機体型番': 'model',
        '記憶容量': 'capacity',
        '等級': 'rank',
        '高額買取価格': 'price_high',
        '特急買取価格': 'price_express',
    }

    df = df.rename(columns=column_mapping)

    # 必要なカラムのみ抽出
    required_columns = ['model', 'capacity', 'rank', 'price_high']
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"必須カラムが見つかりません: {required_columns}")

    return df[required_columns]


# ============================================================
# 価格変更の検出
# ============================================================

def detect_price_changes(df_before: pd.DataFrame, df_after: pd.DataFrame) -> pd.DataFrame:
    """
    2つの買取価格データを比較して変更を検出

    Args:
        df_before: 変更前のデータ
        df_after: 変更後のデータ

    Returns:
        変更があった行のみのDataFrame
    """
    # マージ
    df_merged = pd.merge(
        df_before,
        df_after,
        on=['model', 'capacity', 'rank'],
        how='outer',
        suffixes=('_before', '_after')
    )

    # 価格が変更された行のみ抽出
    df_changed = df_merged[
        df_merged['price_high_before'] != df_merged['price_high_after']
    ].copy()

    # NaNを0に置換（新規追加または削除された行の場合）
    df_changed['price_high_before'] = df_changed['price_high_before'].fillna(0).astype(int)
    df_changed['price_high_after'] = df_changed['price_high_after'].fillna(0).astype(int)

    # 変更額と変更率を計算
    df_changed['price_diff'] = df_changed['price_high_after'] - df_changed['price_high_before']
    df_changed['price_change_rate'] = (
        (df_changed['price_diff'] / df_changed['price_high_before'] * 100)
        .replace([float('inf'), -float('inf')], 0)
        .fillna(0)
        .round(2)
    )

    return df_changed


# ============================================================
# price_changes.csv に追記
# ============================================================

def append_to_price_changes(
    df_changes: pd.DataFrame,
    change_date: str,
    note: str = ""
):
    """
    price_changes.csv に変更履歴を追記

    Args:
        df_changes: 変更データ
        change_date: 変更日 (YYYY-MM-DD)
        note: 備考
    """
    # 既存ファイルの読み込み（存在しない場合は新規作成）
    if PRICE_CHANGES_FILE.exists():
        df_existing = pd.read_csv(PRICE_CHANGES_FILE)
    else:
        df_existing = pd.DataFrame(columns=[
            '変更日', '機種', '容量', 'ランク', '変更前価格', '変更後価格', '変更額', '変更率(%)', '備考'
        ])

    # 新しいレコードを作成
    new_records = []
    for _, row in df_changes.iterrows():
        new_records.append({
            '変更日': change_date,
            '機種': row['model'],
            '容量': row['capacity'],
            'ランク': row['rank'],
            '変更前価格': int(row['price_high_before']),
            '変更後価格': int(row['price_high_after']),
            '変更額': int(row['price_diff']),
            '変更率(%)': row['price_change_rate'],
            '備考': note,
        })

    df_new = pd.DataFrame(new_records)

    # 結合
    df_combined = pd.concat([df_existing, df_new], ignore_index=True)

    # 保存
    PRICE_CHANGES_DIR.mkdir(parents=True, exist_ok=True)
    df_combined.to_csv(PRICE_CHANGES_FILE, index=False, encoding='utf-8-sig')

    print(f"✅ {len(new_records)} 件の価格変更を記録しました")
    print(f"   保存先: {PRICE_CHANGES_FILE}")


# ============================================================
# 自動検出モード
# ============================================================

def auto_detect_latest_files() -> tuple:
    """
    親ディレクトリから最新の買取価格CSVを2つ自動検出

    Returns:
        (変更前ファイル, 変更後ファイル)
    """
    csv_files = list(PARENT_DIR.glob("買取価格*.csv"))

    if len(csv_files) < 2:
        raise FileNotFoundError(
            f"買取価格CSVが2つ以上見つかりません。\n"
            f"検索ディレクトリ: {PARENT_DIR}"
        )

    # 更新日時でソート（新しい順）
    csv_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

    # 最新2ファイル
    after_file = csv_files[0]
    before_file = csv_files[1]

    print(f"📂 自動検出:")
    print(f"   変更前: {before_file.name}")
    print(f"   変更後: {after_file.name}")
    print()

    return before_file, after_file


# ============================================================
# メイン処理
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='買取価格変更履歴の自動生成')
    parser.add_argument('--before', type=str, help='変更前の買取価格CSVファイル名')
    parser.add_argument('--after', type=str, help='変更後の買取価格CSVファイル名')
    parser.add_argument('--change-date', type=str, help='価格変更日 (YYYY-MM-DD)')
    parser.add_argument('--auto', action='store_true', help='最新2ファイルを自動検出')
    parser.add_argument('--note', type=str, default='', help='備考（オプション）')

    args = parser.parse_args()

    print("=" * 60)
    print("📊 買取価格変更履歴の自動生成")
    print("=" * 60)
    print()

    # ファイル指定
    if args.auto:
        # 自動検出モード
        before_file, after_file = auto_detect_latest_files()

        # 変更日を推測（変更後ファイルの日付から）
        if not args.change_date:
            # ファイル名から日付を抽出（例: 買取価格20251119.csv → 2025-11-19）
            import re
            match = re.search(r'(\d{8})', after_file.name)
            if match:
                date_str = match.group(1)
                args.change_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            else:
                args.change_date = datetime.now().strftime("%Y-%m-%d")

    elif args.before and args.after:
        # 手動指定モード
        before_file = PARENT_DIR / args.before
        after_file = PARENT_DIR / args.after

        if not before_file.exists():
            print(f"❌ エラー: {before_file} が見つかりません")
            return

        if not after_file.exists():
            print(f"❌ エラー: {after_file} が見つかりません")
            return

        if not args.change_date:
            args.change_date = datetime.now().strftime("%Y-%m-%d")

    else:
        print("❌ エラー: --auto または --before と --after を指定してください")
        parser.print_help()
        return

    print(f"変更日: {args.change_date}")
    print()

    # データ読み込み
    print("📂 データ読み込み中...")
    df_before = load_buyback_price(before_file)
    df_after = load_buyback_price(after_file)
    print(f"   変更前: {len(df_before)} 行")
    print(f"   変更後: {len(df_after)} 行")
    print()

    # 変更検出
    print("🔍 価格変更を検出中...")
    df_changes = detect_price_changes(df_before, df_after)
    print(f"   検出: {len(df_changes)} 件の価格変更")
    print()

    if len(df_changes) == 0:
        print("✅ 価格変更はありませんでした")
        return

    # サマリー表示
    print("=" * 60)
    print("📈 変更サマリー")
    print("=" * 60)
    print(f"変更件数: {len(df_changes)} 件")
    print(f"値上げ: {len(df_changes[df_changes['price_diff'] > 0])} 件")
    print(f"値下げ: {len(df_changes[df_changes['price_diff'] < 0])} 件")
    print(f"平均変更額: {df_changes['price_diff'].mean():.0f} 円")
    print(f"平均変更率: {df_changes['price_change_rate'].mean():.2f} %")
    print()

    # 上位10件を表示
    print("【主な価格変更】")
    df_top = df_changes.nlargest(10, 'price_diff')
    for _, row in df_top.iterrows():
        print(f"  {row['model']} {row['capacity']} {row['rank']}: "
              f"{int(row['price_high_before']):,}円 → {int(row['price_high_after']):,}円 "
              f"({row['price_diff']:+,}円, {row['price_change_rate']:+.1f}%)")
    print()

    # 保存
    append_to_price_changes(df_changes, args.change_date, args.note)
    print()


if __name__ == "__main__":
    main()
