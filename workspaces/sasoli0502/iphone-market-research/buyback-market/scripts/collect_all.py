"""
全モデルの買取価格を一括収集するスクリプト

じゃんぱらとイオシスから全86モデルのデータを収集します。
"""

from scraper_janpara import JanparaScraper
from scraper_iosys import IosysScraper
from models import get_all_model_capacity_combinations
from pathlib import Path
import time
from datetime import datetime
import json


def collect_janpara_all():
    """じゃんぱらから全モデルを収集"""
    print("=" * 60)
    print("じゃんぱら全モデル収集開始")
    print("=" * 60)

    # モデル×容量の組み合わせを取得
    model_combinations = get_all_model_capacity_combinations()
    print(f"対象モデル数: {len(model_combinations)}モデル")
    print()

    scraper = JanparaScraper()
    all_results = []
    success_count = 0
    error_count = 0

    for i, (model, capacity) in enumerate(model_combinations, 1):
        print(f"\n[{i}/{len(model_combinations)}] {model} {capacity}")
        print("-" * 40)

        try:
            results = scraper.scrape_model(model, capacity)

            if results:
                all_results.extend(results)
                success_count += 1
                print(f"✅ {len(results)}件取得")
            else:
                error_count += 1
                print(f"⚠️ データなし")

            # サーバー負荷軽減のため待機（2-3秒）
            time.sleep(2.5)

        except Exception as e:
            error_count += 1
            print(f"❌ エラー: {e}")
            continue

    # サマリー表示
    print("\n" + "=" * 60)
    print("じゃんぱら収集完了")
    print("=" * 60)
    print(f"成功: {success_count}モデル")
    print(f"失敗: {error_count}モデル")
    print(f"合計データ件数: {len(all_results)}件")

    # 統計情報を保存
    stats = {
        "site": "じゃんぱら",
        "total_models": len(model_combinations),
        "success_count": success_count,
        "error_count": error_count,
        "total_data_count": len(all_results),
        "scraped_at": datetime.now().isoformat(),
    }

    stats_dir = Path(__file__).parent.parent / "data" / "stats"
    stats_dir.mkdir(parents=True, exist_ok=True)
    stats_path = stats_dir / f"janpara_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"\n📊 統計情報: {stats_path}")

    return all_results


def collect_iosys_all():
    """イオシスから全モデルを収集"""
    print("\n" + "=" * 60)
    print("イオシス全モデル収集開始")
    print("=" * 60)

    # モデル×容量の組み合わせを取得
    model_combinations = get_all_model_capacity_combinations()
    print(f"対象モデル数: {len(model_combinations)}モデル")
    print()

    scraper = IosysScraper()

    # イオシスは一括で全モデル取得できる
    print("📄 価格リストを取得中...")
    all_results = scraper.scrape_all_models()

    print("\n" + "=" * 60)
    print("イオシス収集完了")
    print("=" * 60)
    print(f"合計データ件数: {len(all_results)}件")

    # 統計情報を保存
    stats = {
        "site": "イオシス",
        "total_models": len(model_combinations),
        "total_data_count": len(all_results),
        "scraped_at": datetime.now().isoformat(),
    }

    stats_dir = Path(__file__).parent.parent / "data" / "stats"
    stats_dir.mkdir(parents=True, exist_ok=True)
    stats_path = stats_dir / f"iosys_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"\n📊 統計情報: {stats_path}")

    return all_results


def main():
    """メイン実行"""
    print("\n" + "=" * 60)
    print("iPhone買取価格 全モデル一括収集")
    print("=" * 60)
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    start_time = time.time()

    # じゃんぱら収集
    janpara_results = collect_janpara_all()

    # 待機時間（サイト切り替え）
    print("\n⏳ 5秒待機...")
    time.sleep(5)

    # イオシス収集
    iosys_results = collect_iosys_all()

    # 全体サマリー
    elapsed_time = time.time() - start_time

    print("\n" + "=" * 60)
    print("全サイト収集完了")
    print("=" * 60)
    print(f"じゃんぱら: {len(janpara_results)}件")
    print(f"イオシス: {len(iosys_results)}件")
    print(f"合計: {len(janpara_results) + len(iosys_results)}件")
    print(f"所要時間: {elapsed_time/60:.1f}分")
    print()

    # データの場所を案内
    data_dir = Path(__file__).parent.parent / "data" / "raw"
    print("📂 データ保存先:")
    print(f"  じゃんぱら: {data_dir / 'janpara'}/")
    print(f"  イオシス: {data_dir / 'iosys'}/")


if __name__ == "__main__":
    main()
