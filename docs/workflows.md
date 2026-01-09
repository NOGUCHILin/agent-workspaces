# Claude Code推奨ワークフロー

出典: [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)

## 1. Explore-Plan-Code-Commit

最も基本的なパターン。

1. **Explore** - ファイル調査、コードベース理解
2. **Plan** - 詳細な計画作成（extended thinking活用）
3. **Code** - 実装
4. **Commit** - 変更をコミット

## 2. Test-Driven Development

テスト先行で成功基準を明確化。

1. テストを先に書く
2. Claudeがテストを満たすまで反復実装
3. 明確な成功/失敗基準があるため効率的

## 3. Visual Iteration

デザインモックベースの開発。

1. デザインモック/スクリーンショットを提供
2. Claude が実装
3. 視覚的に確認・調整を繰り返す

## 4. Safe YOLO Mode

コンテナ内での自律実行。

```bash
claude --dangerously-skip-permissions
```

- 隔離されたコンテナ環境で使用
- ルーチンタスクの自動化向け
- 本番環境では使用禁止

## 並列開発パターン

- **git worktrees**で複数インスタンス並列実行
- 独立したタスクを同時進行
- 大規模マイグレーションの「ファンアウト」
