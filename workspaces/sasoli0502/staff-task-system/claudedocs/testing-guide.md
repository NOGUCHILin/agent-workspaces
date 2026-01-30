# スタッフタスク管理システム - テストガイド

## テスト方法

### 基本コマンド

```bash
cd /Users/noguchilin/dev/noguchisara-projects/work/staff-task-system
echo "今日のタスク教えて" | claude chat --dangerously-skip-permissions
```

---

## テストケース

### 1. タスク確認

```bash
echo "今日のタスク教えて" | claude chat --dangerously-skip-permissions
```

**期待結果**: タスク一覧と進捗サマリーが表示される

---

### 2. スキル検索

```bash
echo "修理できる人は誰？" | claude chat --dangerously-skip-permissions
```

**期待結果**: 雜賀さんのスキル情報が表示される

---

### 3. スタッフ情報

```bash
echo "細谷さんのスキルを教えて" | claude chat --dangerously-skip-permissions
```

**期待結果**: 細谷さんの全スキル情報が表示される

---

### 4. タスク追加

```bash
echo "iPhone 16の査定タスクを細谷さんに追加して" | claude chat --dangerously-skip-permissions
```

**期待結果**: 新しいタスクIDが発行され、追加成功メッセージが表示される

---

最終更新: 2025-10-15