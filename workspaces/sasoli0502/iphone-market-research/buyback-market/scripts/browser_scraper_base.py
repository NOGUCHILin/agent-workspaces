"""
汎用的なブラウザ自動化スクレイパーのベースクラス

このモジュールはPlaywrightを使用した汎用的なスクレイピング基盤を提供します。
様々なWebサイトのスクレイピングに再利用可能な設計になっています。

使用例:
    class MyScraper(BrowserScraperBase):
        def scrape(self, url: str) -> dict:
            page = self.new_page()
            page.goto(url)
            # スクレイピング処理
            return data

    with MyScraper(headless=True) as scraper:
        data = scraper.scrape("https://example.com")
"""

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from typing import Optional, Dict, Any
import time
from pathlib import Path
import json


class BrowserScraperBase:
    """
    Playwrightを使用したブラウザ自動化の汎用ベースクラス

    特徴:
    - ヘッドレス/ヘッド付きモード切り替え
    - User-Agent設定
    - スクリーンショット機能
    - タイムアウト設定
    - コンテキストマネージャー対応
    - エラーハンドリング
    """

    def __init__(
        self,
        headless: bool = True,
        user_agent: Optional[str] = None,
        timeout: int = 30000,
        slow_mo: int = 0,
        viewport: Optional[Dict[str, int]] = None,
    ):
        """
        Args:
            headless: ヘッドレスモードで実行するか（デフォルト: True）
            user_agent: カスタムUser-Agent（デフォルト: Chrome on macOS）
            timeout: デフォルトタイムアウト（ミリ秒、デフォルト: 30秒）
            slow_mo: 操作を遅くする時間（ミリ秒、デバッグ用）
            viewport: ビューポートサイズ（デフォルト: 1920x1080）
        """
        self.headless = headless
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        self.timeout = timeout
        self.slow_mo = slow_mo
        self.viewport = viewport or {"width": 1920, "height": 1080}

        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    def __enter__(self):
        """コンテキストマネージャーのエントリーポイント"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャーの終了処理"""
        self.close()

    def start(self):
        """ブラウザを起動"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
        )
        self.context = self.browser.new_context(
            user_agent=self.user_agent,
            viewport=self.viewport,
        )
        self.context.set_default_timeout(self.timeout)

    def close(self):
        """ブラウザを終了"""
        if self._page:
            self._page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def new_page(self) -> Page:
        """
        新しいページを作成

        Returns:
            Page: Playwrightのページオブジェクト
        """
        if not self.context:
            raise RuntimeError("Browser not started. Call start() first.")

        self._page = self.context.new_page()
        return self._page

    def goto(self, page: Page, url: str, wait_until: str = "domcontentloaded") -> None:
        """
        指定URLに遷移

        Args:
            page: Pageオブジェクト
            url: 遷移先URL
            wait_until: 待機条件（'load', 'domcontentloaded', 'networkidle'）
        """
        page.goto(url, wait_until=wait_until)

    def wait_for_selector(
        self,
        page: Page,
        selector: str,
        timeout: Optional[int] = None
    ) -> None:
        """
        セレクターの要素が表示されるまで待機

        Args:
            page: Pageオブジェクト
            selector: CSSセレクター
            timeout: タイムアウト（ミリ秒、Noneの場合はデフォルト値）
        """
        page.wait_for_selector(selector, timeout=timeout or self.timeout)

    def take_screenshot(
        self,
        page: Page,
        path: Path,
        full_page: bool = False
    ) -> None:
        """
        スクリーンショットを撮影

        Args:
            page: Pageオブジェクト
            path: 保存先パス
            full_page: ページ全体を撮影するか
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(path), full_page=full_page)

    def extract_text(self, page: Page, selector: str) -> Optional[str]:
        """
        セレクターに一致する要素のテキストを抽出

        Args:
            page: Pageオブジェクト
            selector: CSSセレクター

        Returns:
            テキスト（見つからない場合はNone）
        """
        try:
            element = page.query_selector(selector)
            return element.inner_text() if element else None
        except Exception:
            return None

    def extract_texts(self, page: Page, selector: str) -> list[str]:
        """
        セレクターに一致する全要素のテキストを抽出

        Args:
            page: Pageオブジェクト
            selector: CSSセレクター

        Returns:
            テキストのリスト
        """
        elements = page.query_selector_all(selector)
        return [el.inner_text() for el in elements]

    def extract_attribute(
        self,
        page: Page,
        selector: str,
        attribute: str
    ) -> Optional[str]:
        """
        セレクターに一致する要素の属性を抽出

        Args:
            page: Pageオブジェクト
            selector: CSSセレクター
            attribute: 属性名

        Returns:
            属性値（見つからない場合はNone）
        """
        try:
            element = page.query_selector(selector)
            return element.get_attribute(attribute) if element else None
        except Exception:
            return None

    def click(self, page: Page, selector: str, wait_after: float = 0.5) -> None:
        """
        要素をクリック

        Args:
            page: Pageオブジェクト
            selector: CSSセレクター
            wait_after: クリック後の待機時間（秒）
        """
        page.click(selector)
        if wait_after > 0:
            time.sleep(wait_after)

    def fill(self, page: Page, selector: str, text: str) -> None:
        """
        入力フィールドにテキストを入力

        Args:
            page: Pageオブジェクト
            selector: CSSセレクター
            text: 入力するテキスト
        """
        page.fill(selector, text)

    def select_option(self, page: Page, selector: str, value: str) -> None:
        """
        セレクトボックスのオプションを選択

        Args:
            page: Pageオブジェクト
            selector: CSSセレクター
            value: 選択する値
        """
        page.select_option(selector, value)

    def scroll_to_bottom(self, page: Page, wait: float = 1.0) -> None:
        """
        ページの最下部までスクロール

        Args:
            page: Pageオブジェクト
            wait: スクロール後の待機時間（秒）
        """
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(wait)

    def wait(self, seconds: float) -> None:
        """
        指定秒数待機

        Args:
            seconds: 待機時間（秒）
        """
        time.sleep(seconds)

    def save_json(self, data: Any, path: Path) -> None:
        """
        データをJSONファイルとして保存

        Args:
            data: 保存するデータ
            path: 保存先パス
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_json(self, path: Path) -> Any:
        """
        JSONファイルを読み込み

        Args:
            path: ファイルパス

        Returns:
            読み込んだデータ
        """
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
