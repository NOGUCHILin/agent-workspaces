"""
CSVファイルをHTMLテーブルとして表示するビューアー
"""

import pandas as pd
from pathlib import Path
import sys
import webbrowser
import tempfile

def view_csv_as_html(csv_path: str):
    """CSVをHTMLテーブルとして表示"""
    csv_file = Path(csv_path)

    if not csv_file.exists():
        print(f"❌ ファイルが見つかりません: {csv_path}")
        return

    print(f"📂 読み込み中: {csv_file.name}")

    # CSVを読み込み
    df = pd.read_csv(csv_file)

    print(f"✓ {len(df)}行 × {len(df.columns)}列のデータを読み込みました")

    # HTMLを生成
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{csv_file.name}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }}
            h1 {{
                color: #333;
                font-size: 24px;
            }}
            .info {{
                background: #fff;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .table-container {{
                overflow-x: auto;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                font-size: 14px;
            }}
            th {{
                background-color: #4CAF50;
                color: white;
                padding: 12px;
                text-align: left;
                position: sticky;
                top: 0;
                z-index: 10;
            }}
            td {{
                padding: 10px;
                border-bottom: 1px solid #ddd;
            }}
            tr:hover {{
                background-color: #f5f5f5;
            }}
            tr:nth-child(even) {{
                background-color: #fafafa;
            }}
            .number {{
                text-align: right;
                font-family: 'Monaco', 'Courier New', monospace;
            }}
        </style>
    </head>
    <body>
        <h1>📊 {csv_file.name}</h1>
        <div class="info">
            <strong>データ件数:</strong> {len(df):,}行<br>
            <strong>カラム数:</strong> {len(df.columns)}列<br>
            <strong>カラム:</strong> {', '.join(df.columns.tolist())}
        </div>
        <div class="table-container">
            {df.to_html(index=False, classes='data-table', escape=False, na_rep='-')}
        </div>
    </body>
    </html>
    """

    # reportsディレクトリに保存
    report_dir = csv_file.parent.parent / "reports" if csv_file.parent.name == "reports" else csv_file.parent / "reports"
    if not report_dir.exists():
        report_dir = csv_file.parent

    html_filename = csv_file.stem + '.html'
    html_path = report_dir / html_filename

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✓ HTMLファイル生成: {html_path}")
    print(f"\n💡 VSCode Serverでファイルを開いてください:")
    print(f"   {html_path}")
    print(f"\n   または、右クリック → 'Open in Browser' / 'Preview'で表示できます")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: uv run python scripts/view_csv.py <CSVファイルパス>")
        sys.exit(1)

    csv_path = sys.argv[1]
    view_csv_as_html(csv_path)
