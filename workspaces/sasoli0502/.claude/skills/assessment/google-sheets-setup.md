# Google Sheets API セットアップ

BM平均売価を自動取得するためのGoogle Sheets API設定手順

## 1. Google Cloud Platformでプロジェクト作成

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新しいプロジェクトを作成（例: "iphone-assessment-automation"）

## 2. Google Sheets APIを有効化

1. プロジェクトを選択
2. 「APIとサービス」→「ライブラリ」
3. "Google Sheets API"を検索して有効化

## 3. サービスアカウントを作成

1. 「APIとサービス」→「認証情報」
2. 「認証情報を作成」→「サービスアカウント」
3. サービスアカウント名を入力（例: "sheets-reader"）
4. ロールは不要（スキップ）
5. 作成完了

## 4. 認証情報（JSONキー）をダウンロード

1. 作成したサービスアカウントをクリック
2. 「キー」タブ→「鍵を追加」→「新しい鍵を作成」
3. JSON形式を選択してダウンロード
4. ダウンロードしたJSONファイルを以下に保存：
   ```
   c:\Users\koyom\agent-workspaces\workspaces\sasoli0502\.claude\skills\assessment\credentials.json
   ```

## 5. スプレッドシートを共有

1. スプレッドシートを開く: https://docs.google.com/spreadsheets/d/1Gg4Lvvlx25GGk-LdEnr8apUO2Q4e2ZOYovaAlBfV7os/edit
2. 「共有」ボタンをクリック
3. サービスアカウントのメールアドレス（`xxx@xxx.iam.gserviceaccount.com`）を追加
4. 権限は「閲覧者」でOK

## 6. 必要なPythonライブラリをインストール

```bash
pip install gspread oauth2client
```

## スプレッドシート情報

- **スプレッドシートID**: `1Gg4Lvvlx25GGk-LdEnr8apUO2Q4e2ZOYovaAlBfV7os`
- **シート名**: `BM平均売価(新)`
- **参照範囲**: A2:D513
- **データ構造**:
  - A列: 機種（例: iPhone 12 mini）
  - B列: 容量（例: 64GB）
  - C列: グレード（A/B/Cグレード）
  - D列: 平均売価（円）

## 使用方法

`get_price.py`スクリプトを実行：

```python
from get_price import get_bm_price

# 機種、容量、グレードから平均売価を取得
price = get_bm_price("iPhone 12 mini", "64GB", "Cグレード")
print(price)  # 23866
```

## トラブルシューティング

### エラー: `gspread.exceptions.APIError: [403]`
→ スプレッドシートがサービスアカウントと共有されていません。手順5を確認してください。

### エラー: `FileNotFoundError: credentials.json`
→ 認証情報ファイルが正しい場所に保存されていません。手順4を確認してください。

### エラー: `gspread.exceptions.WorksheetNotFound`
→ シート名が正しくありません。スプレッドシートのシート名を確認してください。
