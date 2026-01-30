# Todoist タスク同期システム

CLAUDE.mdの`<pending-tasks>`セクションをTodoistと自動同期します。

## セットアップ

### 1. APIトークンの設定

`.env`ファイルを作成して、TodoistのAPIトークンを設定します：

```bash
# .env.templateをコピー
cp work/misc-tasks/todoist-sync/.env.template work/misc-tasks/todoist-sync/.env

# .envファイルを編集してAPIトークンを設定
# TODOIST_API_TOKEN=あなたのAPIトークン
```

**APIトークンの取得方法**:
1. https://todoist.com にログイン
2. 右上のアイコン → 「設定」
3. 「連携機能」タブ
4. 「開発者」セクションでAPIトークンをコピー

### 2. 依存関係のインストール

```bash
uv pip install requests python-dotenv
```

## 使い方

### 手動同期

```bash
# APIトークンを環境変数に設定して実行
source work/misc-tasks/todoist-sync/.env
uv run python work/misc-tasks/todoist-sync/sync_tasks.py
```

### 自動同期（定期実行）

#### macOS (launchd)

`~/Library/LaunchAgents/com.todoist.sync.plist`を作成：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.todoist.sync</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>source /Users/noguchisara/projects/work/misc-tasks/todoist-sync/.env && cd /Users/noguchisara/projects && uv run python work/misc-tasks/todoist-sync/sync_tasks.py</string>
    </array>
    <key>StartInterval</key>
    <integer>300</integer>
    <key>StandardOutPath</key>
    <string>/tmp/todoist-sync.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/todoist-sync-error.log</string>
</dict>
</plist>
```

起動:
```bash
launchctl load ~/Library/LaunchAgents/com.todoist.sync.plist
```

停止:
```bash
launchctl unload ~/Library/LaunchAgents/com.todoist.sync.plist
```

**5分ごとに自動同期されます。**

## 動作

### 同期ロジック

1. **CLAUDE.mdから抽出**
   - `<pending-tasks>`セクション内の全タスクを抽出
   - カテゴリ（野口器単独、共同など）をラベルとして設定

2. **優先度の判定**
   - `【最優先】` → 優先度4（赤）
   - `【優先】` → 優先度3（オレンジ）
   - それ以外 → 優先度1（通常）

3. **Todoistと同期**
   - CLAUDE.mdに新しいタスク → Todoistに追加
   - CLAUDE.mdから削除されたタスク → Todoistから削除

### タスク形式

CLAUDE.mdのタスク:
```
### 野口器単独
1. **【最優先】クレジットカード内訳調査**
```

Todoistでの表示:
```
[野口器単独] クレジットカード内訳調査
優先度: 4（赤）
ラベル: 野口器
```

## リマインダー設定

Todoistアプリ（携帯）で設定します：

1. Todoistアプリを開く
2. 「インボックス」を開く
3. 右上の「...」→ 「リマインダー」
4. 毎日のリマインダーを設定（例：毎朝9時）

## トラブルシューティング

### APIトークンエラー

```
❌ エラー: 環境変数 TODOIST_API_TOKEN が設定されていません
```

→ `.env`ファイルを作成してAPIトークンを設定してください

### 同期されない

- `sync_tasks.py`を手動実行して動作確認
- ログファイル(`/tmp/todoist-sync.log`)を確認
- CLAUDE.mdの`<pending-tasks>`セクションが正しいか確認

## 仕様

- **同期対象**: CLAUDE.mdの`<pending-tasks>`セクションのみ
- **同期方向**: CLAUDE.md → Todoist（一方向）
- **同期頻度**: 手動 or 5分ごと（自動設定時）
- **対象タスク**: 野口器さん個人のタスクのみ
