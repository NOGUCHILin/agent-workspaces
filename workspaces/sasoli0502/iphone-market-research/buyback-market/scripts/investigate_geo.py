"""
ゲオ買取サイトの構造調査スクリプト

このスクリプトはゲオのiPhone買取ページの構造を調査し、
スクレイピング戦略を決定するための情報を収集します。
"""

from browser_scraper_base import BrowserScraperBase
from pathlib import Path
from datetime import datetime


class GeoInvestigator(BrowserScraperBase):
    """ゲオサイトの構造調査クラス"""

    BASE_URL = "https://buymobile.geo-online.co.jp/"

    def investigate(self) -> dict:
        """
        ゲオサイトの構造を調査

        Returns:
            調査結果の辞書
        """
        print("🔍 ゲオサイトの構造調査を開始...")

        page = self.new_page()

        # メインページにアクセス
        print(f"📄 {self.BASE_URL} にアクセス中...")
        try:
            self.goto(page, self.BASE_URL, wait_until="networkidle")
            print("✅ アクセス成功！")
        except Exception as e:
            print(f"❌ アクセス失敗: {e}")
            return {"error": str(e), "status": "failed"}

        # スクリーンショット撮影
        screenshot_dir = Path(__file__).parent.parent / "data" / "screenshots"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = screenshot_dir / f"geo_main_{timestamp}.png"

        print(f"📸 スクリーンショット撮影: {screenshot_path}")
        self.take_screenshot(page, screenshot_path, full_page=True)

        # ページタイトル取得
        title = page.title()
        print(f"📝 ページタイトル: {title}")

        # ページのHTMLを部分的に保存（デバッグ用）
        html_content = page.content()
        html_path = screenshot_dir / f"geo_main_{timestamp}.html"
        html_path.write_text(html_content, encoding="utf-8")
        print(f"💾 HTML保存: {html_path}")

        # iPhoneリンクを探す
        print("\n🔎 iPhoneリンクを検索中...")
        iphone_links = self._find_iphone_links(page)

        if not iphone_links:
            print("⚠️ iPhoneリンクが見つかりません")
            print("💡 手動でページを確認してください")
        else:
            print(f"✅ {len(iphone_links)}個のiPhoneリンクを発見")
            for i, link in enumerate(iphone_links[:5], 1):
                print(f"  {i}. {link['text']}: {link['url']}")

        # ナビゲーション構造を調査
        print("\n🗂️ ナビゲーション構造を調査中...")
        nav_structure = self._analyze_navigation(page)

        result = {
            "status": "success",
            "timestamp": timestamp,
            "url": self.BASE_URL,
            "title": title,
            "screenshot": str(screenshot_path),
            "html_file": str(html_path),
            "iphone_links": iphone_links,
            "navigation": nav_structure,
        }

        print("\n✅ 調査完了！")
        return result

    def _find_iphone_links(self, page) -> list[dict]:
        """iPhoneに関連するリンクを検索"""
        links = []

        # よくあるパターンを試す
        patterns = [
            'a:has-text("iPhone")',
            'a:has-text("アイフォン")',
            '[href*="iphone"]',
            '[href*="iPhone"]',
        ]

        for pattern in patterns:
            try:
                elements = page.query_selector_all(pattern)
                for el in elements:
                    text = el.inner_text().strip()
                    href = el.get_attribute("href")
                    if href and text:
                        # 相対URLを絶対URLに変換
                        if href.startswith("/"):
                            href = self.BASE_URL.rstrip("/") + href
                        links.append({"text": text, "url": href})
            except Exception:
                pass

        # 重複削除
        unique_links = []
        seen_urls = set()
        for link in links:
            if link["url"] not in seen_urls:
                unique_links.append(link)
                seen_urls.add(link["url"])

        return unique_links

    def _analyze_navigation(self, page) -> dict:
        """ナビゲーション構造を分析"""
        nav = {}

        # メインナビゲーション
        try:
            nav_elements = page.query_selector_all("nav a, .nav a, header a")
            nav["main_menu"] = [
                {
                    "text": el.inner_text().strip(),
                    "url": el.get_attribute("href"),
                }
                for el in nav_elements[:20]  # 最初の20個まで
                if el.inner_text().strip()
            ]
        except Exception:
            nav["main_menu"] = []

        # セレクトボックス（モデル選択などに使われることがある）
        try:
            selects = page.query_selector_all("select")
            nav["select_boxes"] = []
            for select in selects:
                options = select.query_selector_all("option")
                nav["select_boxes"].append({
                    "id": select.get_attribute("id"),
                    "name": select.get_attribute("name"),
                    "options": [opt.inner_text().strip() for opt in options[:10]],
                })
        except Exception:
            nav["select_boxes"] = []

        return nav


def main():
    """メイン実行"""
    print("=" * 60)
    print("ゲオ買取サイト構造調査")
    print("=" * 60)
    print()

    # ヘッドレスモードで実行（デバッグ時はheadless=Falseに変更）
    with GeoInvestigator(headless=True, timeout=60000) as investigator:
        result = investigator.investigate()

    # 結果を保存
    if result.get("status") == "success":
        output_dir = Path(__file__).parent.parent / "data" / "investigations"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"geo_investigation_{result['timestamp']}.json"

        investigator.save_json(result, output_path)
        print(f"\n💾 調査結果を保存: {output_path}")
        print("\n📋 次のステップ:")
        print("  1. スクリーンショットを確認")
        print("  2. HTMLファイルを確認")
        print("  3. iPhoneリンクから詳細ページに遷移するスクリプトを作成")
    else:
        print(f"\n❌ 調査失敗: {result.get('error')}")


if __name__ == "__main__":
    main()
