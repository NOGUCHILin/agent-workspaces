#!/usr/bin/env python3
"""
資金繰り分析 統合実行スクリプト

すべての分析処理を一括実行します。

実行順序:
1. データクリーニング (clean_journal_data.py)
2. 詳細版資金繰り表 (generate_cashflow_detailed.py)
3. 損益計算書 (generate_pl_statement.py)
4. クレカ経費分析 (analyze_credit_card.py)
5. 資金繰り予測 (forecast_cashflow.py)
"""

import subprocess
from pathlib import Path
from datetime import datetime
import sys


def print_header(text: str):
    """セクションヘッダーを表示"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def print_step(step_num: int, total: int, description: str):
    """ステップ番号と説明を表示"""
    print(f"[{step_num}/{total}] {description}")
    print("-" * 80)


def run_script(script_path: Path) -> bool:
    """
    スクリプトを実行し、結果を返す

    Returns:
        bool: 成功時True、失敗時False
    """
    try:
        result = subprocess.run(
            ["uv", "run", "python", str(script_path)],
            cwd=script_path.parent.parent,
            capture_output=False,
            text=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ エラー: スクリプト実行に失敗しました")
        print(f"   {script_path.name}")
        return False


def main():
    project_root = Path(__file__).parent.parent
    scripts_dir = project_root / "scripts"
    source_dir = project_root / "data" / "source"

    print_header("📊 資金繰り分析 統合実行")
    print(f"開始時刻: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
    print(f"プロジェクト: {project_root}\n")

    # ===== Step 0: 元データの確認 =====
    print_header("Step 0: 元データの確認")

    # 仕訳帳CSVを検索
    journal_files = list(source_dir.glob("仕訳帳_*.csv"))

    if not journal_files:
        print("❌ エラー: 仕訳帳CSVが見つかりません")
        print(f"\n以下のディレクトリに配置してください:")
        print(f"  {source_dir}/")
        print(f"\nファイル名の例:")
        print(f"  仕訳帳_20251029_1608.csv")
        print(f"\nマネーフォワードクラウド会計からエクスポートしてください:")
        print(f"  会計 → 帳票 → 仕訳帳 → CSV出力")
        sys.exit(1)

    # 最新のファイルを取得
    latest_journal = max(journal_files, key=lambda p: p.stat().st_mtime)
    print(f"✅ 仕訳帳CSV発見: {latest_journal.name}")

    # 社内資金繰り表の確認（オプション）
    internal_files = list(source_dir.glob("社内資金繰り表_*.csv"))
    if internal_files:
        latest_internal = max(internal_files, key=lambda p: p.stat().st_mtime)
        print(f"✅ 社内資金繰り表発見: {latest_internal.name}")
    else:
        print(f"⚠️  社内資金繰り表なし（オプション）")

    print("\n準備完了。分析を開始します...\n")

    # ===== 実行するスクリプトのリスト =====
    scripts = [
        {
            "name": "データクリーニング",
            "path": scripts_dir / "clean_journal_data.py",
            "description": "仕訳帳CSVを整形し、分析用データを生成"
        },
        {
            "name": "詳細版資金繰り表",
            "path": scripts_dir / "generate_cashflow_detailed.py",
            "description": "日次資金繰り表をHTML形式で生成"
        },
        {
            "name": "損益計算書",
            "path": scripts_dir / "generate_pl_statement.py",
            "description": "月次損益計算書をHTML形式で生成"
        },
        {
            "name": "クレカ経費分析",
            "path": scripts_dir / "analyze_credit_card.py",
            "description": "クレジットカード経費を月別に集計"
        },
        {
            "name": "資金繰り予測",
            "path": scripts_dir / "forecast_cashflow.py",
            "description": "過去データから今後30日間の資金繰りを予測"
        }
    ]

    total_scripts = len(scripts)
    success_count = 0
    failed_scripts = []

    # ===== 各スクリプトを順次実行 =====
    for idx, script_info in enumerate(scripts, start=1):
        print_step(idx, total_scripts, script_info["name"])
        print(f"📝 {script_info['description']}\n")

        if not script_info["path"].exists():
            print(f"❌ スクリプトが見つかりません: {script_info['path']}")
            failed_scripts.append(script_info["name"])
            continue

        success = run_script(script_info["path"])

        if success:
            print(f"\n✅ 完了: {script_info['name']}\n")
            success_count += 1
        else:
            print(f"\n❌ 失敗: {script_info['name']}\n")
            failed_scripts.append(script_info["name"])

    # ===== 最終サマリー =====
    print_header("📊 実行結果サマリー")

    print(f"完了時刻: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
    print(f"\n成功: {success_count}/{total_scripts} スクリプト")

    if failed_scripts:
        print(f"\n失敗したスクリプト:")
        for name in failed_scripts:
            print(f"  ❌ {name}")

    # 生成されたレポートの一覧
    reports_dir = project_root / "data" / "reports"
    if reports_dir.exists():
        html_files = sorted(reports_dir.glob("*.html"), key=lambda p: p.stat().st_mtime, reverse=True)

        if html_files:
            print(f"\n生成されたレポート ({reports_dir}):")
            for html_file in html_files[:5]:  # 最新5件
                mtime = datetime.fromtimestamp(html_file.stat().st_mtime)
                print(f"  📄 {html_file.name} ({mtime.strftime('%m/%d %H:%M')})")

    processed_dir = project_root / "data" / "processed"
    if processed_dir.exists():
        csv_files = sorted(processed_dir.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)

        if csv_files:
            print(f"\n処理済みデータ ({processed_dir}):")
            for csv_file in csv_files[:3]:  # 最新3件
                mtime = datetime.fromtimestamp(csv_file.stat().st_mtime)
                print(f"  📄 {csv_file.name} ({mtime.strftime('%m/%d %H:%M')})")

    print("\n" + "=" * 80)

    if success_count == total_scripts:
        print("🎉 すべての分析が正常に完了しました！")
    else:
        print("⚠️  一部のスクリプトが失敗しました。エラーメッセージを確認してください。")

    print("=" * 80 + "\n")

    # 終了コード
    sys.exit(0 if success_count == total_scripts else 1)


if __name__ == "__main__":
    main()
