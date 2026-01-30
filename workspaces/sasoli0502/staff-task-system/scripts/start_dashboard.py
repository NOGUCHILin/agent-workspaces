#!/usr/bin/env python3
"""
ダッシュボードサーバー起動スクリプト

シンプルなHTTPサーバーを起動してダッシュボードを提供
"""

import sys
import json
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "scripts"))

from dashboard_api import DashboardAPI


class DashboardHTTPRequestHandler(SimpleHTTPRequestHandler):
    """ダッシュボード用カスタムリクエストハンドラ"""

    def __init__(self, *args, **kwargs):
        # ドキュメントルートをプロジェクトルートに設定
        super().__init__(*args, directory=str(project_root), **kwargs)

    def do_GET(self):
        """GETリクエストを処理"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)

        # APIエンドポイント
        if path == '/api/dashboard':
            self.handle_api_dashboard(query)
        elif path == '/api/summary':
            self.handle_api_summary(query)
        elif path == '/api/staff':
            self.handle_api_staff(query)
        elif path == '/api/alerts':
            self.handle_api_alerts(query)
        # ルートアクセス → monitor.htmlにリダイレクト
        elif path == '/':
            self.send_response(302)
            self.send_header('Location', '/monitor')
            self.end_headers()
        # /monitor → monitor.htmlを返す
        elif path == '/monitor':
            self.serve_monitor_html()
        else:
            # その他のリクエストは通常のファイル配信
            super().do_GET()

    def handle_api_dashboard(self, query):
        """全データを返すAPIエンドポイント"""
        date_str = query.get('date', [None])[0]
        api = DashboardAPI(date_str)
        data = api.get_dashboard_data()
        self.send_json_response(data)

    def handle_api_summary(self, query):
        """サマリーのみ返すAPIエンドポイント"""
        date_str = query.get('date', [None])[0]
        api = DashboardAPI(date_str)
        data = api.get_summary()
        self.send_json_response(data)

    def handle_api_staff(self, query):
        """スタッフ別進捗を返すAPIエンドポイント"""
        date_str = query.get('date', [None])[0]
        api = DashboardAPI(date_str)
        data = api.get_staff_progress()
        self.send_json_response(data)

    def handle_api_alerts(self, query):
        """警告を返すAPIエンドポイント"""
        date_str = query.get('date', [None])[0]
        api = DashboardAPI(date_str)
        data = api.get_alerts()
        self.send_json_response(data)

    def serve_monitor_html(self):
        """monitor.htmlを配信"""
        try:
            html_path = project_root / "dashboard" / "monitor.html"
            with open(html_path, 'rb') as f:
                content = f.read()

            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Internal Server Error: {str(e)}")

    def send_json_response(self, data):
        """JSON形式でレスポンスを返す"""
        try:
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            encoded_data = json_data.encode('utf-8')

            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(encoded_data)))
            self.send_header('Access-Control-Allow-Origin', '*')  # CORS対応
            self.end_headers()
            self.wfile.write(encoded_data)
        except Exception as e:
            self.send_error(500, f"Internal Server Error: {str(e)}")

    def log_message(self, format, *args):
        """ログメッセージをカスタマイズ"""
        # シンプルなログ出力
        sys.stdout.write(f"[{self.log_date_time_string()}] {format % args}\n")


def start_server(port=8000, host='127.0.0.1'):
    """ダッシュボードサーバーを起動

    Args:
        port: ポート番号（デフォルト: 8000）
        host: ホスト名（デフォルト: 127.0.0.1）
    """
    server_address = (host, port)
    httpd = HTTPServer(server_address, DashboardHTTPRequestHandler)

    print("=" * 60)
    print("📊 タスク管理ダッシュボード サーバー起動")
    print("=" * 60)
    print()
    print(f"🌐 URL: http://{host}:{port}/monitor")
    print()
    print("💡 使い方:")
    print("  1. ブラウザで上記URLを開く")
    print("  2. 自動で5秒ごとに更新されます")
    print("  3. 停止するには Ctrl+C を押してください")
    print()
    print("📡 利用可能なAPIエンドポイント:")
    print(f"  - http://{host}:{port}/api/dashboard  (全データ)")
    print(f"  - http://{host}:{port}/api/summary   (サマリー)")
    print(f"  - http://{host}:{port}/api/staff     (スタッフ別)")
    print(f"  - http://{host}:{port}/api/alerts    (警告)")
    print()
    print("=" * 60)
    print()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print()
        print("=" * 60)
        print("🛑 サーバーを停止しました")
        print("=" * 60)
        httpd.shutdown()


def main():
    """エントリーポイント"""
    import argparse

    parser = argparse.ArgumentParser(description="ダッシュボードサーバー起動")
    parser.add_argument('--port', type=int, default=8000, help='ポート番号（デフォルト: 8000）')
    parser.add_argument('--host', default='127.0.0.1', help='ホスト名（デフォルト: 127.0.0.1）')

    args = parser.parse_args()

    start_server(port=args.port, host=args.host)


if __name__ == "__main__":
    main()
