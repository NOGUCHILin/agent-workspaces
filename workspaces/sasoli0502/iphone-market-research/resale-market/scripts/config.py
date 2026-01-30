"""
API設定ファイル

各APIのキー・認証情報を管理
環境変数または設定ファイルから読み込み
"""
import os

# 楽天API
RAKUTEN_APP_ID = os.getenv("RAKUTEN_APP_ID", "")

# Yahoo!ショッピングAPI
YAHOO_CLIENT_ID = os.getenv("YAHOO_CLIENT_ID", "")

# Amazon PA-API（オプション）
AMAZON_ACCESS_KEY = os.getenv("AMAZON_ACCESS_KEY", "")
AMAZON_SECRET_KEY = os.getenv("AMAZON_SECRET_KEY", "")
AMAZON_PARTNER_TAG = os.getenv("AMAZON_PARTNER_TAG", "")


def validate_api_keys():
    """
    必須APIキーが設定されているか確認

    Returns:
        dict: 各APIの設定状況
    """
    status = {
        "rakuten": bool(RAKUTEN_APP_ID),
        "yahoo": bool(YAHOO_CLIENT_ID),
        "amazon": bool(AMAZON_ACCESS_KEY and AMAZON_SECRET_KEY and AMAZON_PARTNER_TAG),
    }
    return status


if __name__ == "__main__":
    status = validate_api_keys()
    print("API設定状況:")
    for api, configured in status.items():
        print(f"  {api}: {'✅ 設定済み' if configured else '❌ 未設定'}")

    if not status["rakuten"]:
        print("\n楽天APIキーの設定方法:")
        print("  export RAKUTEN_APP_ID='your_app_id'")

    if not status["yahoo"]:
        print("\nYahoo!ショッピングAPIキーの設定方法:")
        print("  export YAHOO_CLIENT_ID='your_client_id'")
