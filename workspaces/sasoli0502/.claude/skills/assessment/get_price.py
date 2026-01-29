"""
BM平均売価をGoogle Sheetsから取得するスクリプト（gspread API版）
"""
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pathlib import Path
from typing import Optional

# 認証情報ファイルのパス
CREDENTIALS_PATH = Path(__file__).parent / "credentials.json"

# スプレッドシート情報
SPREADSHEET_ID = "1Gg4Lvvlx25GGk-LdEnr8apUO2Q4e2ZOYovaAlBfV7os"
SHEET_NAME = "BM平均売価(新)"


def get_bm_price(model: str, capacity: str, grade: str) -> Optional[int]:
    """
    機種・容量・グレードから平均売価を取得（gspread API版）

    Args:
        model: 機種名（例: "iPhone 12 mini"）
        capacity: 容量（例: "64GB"）
        grade: グレード（例: "Cグレード", "C", "プレミアム"）
              - "Aグレード", "Bグレード", "Cグレード" → "A", "B", "C"に自動変換
              - "A", "B", "C", "プレミアム" → そのまま使用

    Returns:
        平均売価（円）。見つからない場合はNone

    Example:
        >>> get_bm_price("iPhone 12 mini", "64GB", "Cグレード")
        23866
        >>> get_bm_price("iPhone 14 Pro", "256GB", "B")
        82225
    """
    # グレード表記の正規化（Aグレード/Bグレード/Cグレード → A/B/C）
    # スプレッドシート内の実際の表記: A, B, C, プレミアム
    if grade in ["Aグレード", "Bグレード", "Cグレード"]:
        grade = grade[0]  # "Aグレード" → "A"
    # "A", "B", "C", "プレミアム" はそのまま使用

    try:
        # 認証
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            str(CREDENTIALS_PATH), scope)
        client = gspread.authorize(creds)

        # スプレッドシートを開く
        sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

        # 全データを取得（A2:D513）
        data = sheet.get('A2:D513')

        # 該当する行を検索
        for row in data:
            if len(row) >= 4:
                sheet_model, sheet_capacity, sheet_grade, sheet_price = row
                if (sheet_model == model and
                    sheet_capacity == capacity and
                    sheet_grade == grade):
                    # 価格を整数に変換（カンマ区切りも処理）
                    price_str = sheet_price.replace(",", "").replace("円", "").strip()
                    if price_str:
                        return int(float(price_str))

        print(f"警告: {model} {capacity} {grade} の価格が見つかりませんでした")
        return None

    except Exception as e:
        print(f"エラー: {e}")
        return None


if __name__ == "__main__":
    # テスト
    print("=== BM平均売価取得テスト（gspread API版） ===\n")

    # テストケース1: iPhone 12 mini
    price = get_bm_price("iPhone 12 mini", "64GB", "C")
    if price:
        print(f"✓ iPhone 12 mini 64GB C: {price}円")

    # テストケース2: iPhone 12 Pro Max
    price = get_bm_price("iPhone 12 Pro Max", "128GB", "C")
    if price:
        print(f"✓ iPhone 12 Pro Max 128GB C: {price}円")
