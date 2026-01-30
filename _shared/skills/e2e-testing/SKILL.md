---
name: e2e-testing
description: E2Eテストの設計・実装・実行を支援。「E2Eテスト追加」「テスト書いて」「ステージング検証」「テストカバレッジ確認」で使用。
---

# E2E Testing Skill

## このスキルの使い方

「E2Eテスト追加して」「テストカバレッジ確認」と言われたら、以下のワークフローを実行する。

## ワークフロー

### Step 1: 現状分析
```bash
# 既存E2Eテスト一覧
find tests/e2e -name "*.spec.ts" -type f

# テスト対象ページ一覧（public-site）
find public-site/src/app -name "page.tsx" | grep -v __tests__

# テスト対象ページ一覧（admin-app）
find admin-app/code/app -name "page.tsx" | grep -v __tests__

# LIFFページ一覧
find admin-app/code/app/liff -name "page.tsx"
```

### Step 2: カバレッジマトリクス作成

以下の表を埋めて、テストギャップを特定する：

| ページ/機能 | Unit | Integration | E2E | 優先度 | 理由 |
|------------|------|-------------|-----|--------|------|
| LP ippan-a | ✅ | - | ❌ | 高 | 収益直結 |
| LP shitadori-a | ✅ | - | ❌ | 高 | 収益直結 |
| LIFF 見積もり | ✅ | ✅ | ❌ | 高 | ユーザー影響大 |
| LIFF 予約 | ✅ | ✅ | ❌ | 高 | ユーザー影響大 |
| Admin 価格管理 | ✅ | ✅ | ❌ | 低 | 内部ツール |

### Step 3: 優先度判定

E2Eテストを追加すべき基準：
1. **収益直結** - LP、決済、申込フロー → 必須
2. **ユーザー影響大** - フォーム送信、認証 → 必須
3. **過去に障害発生** - 再発防止 → 必須
4. **複数システム連携** - API→DB→通知 → 推奨
5. **内部ツール** - Admin系 → 不要（Unit/Integrationで十分）

### Step 4: テスト設計

各ページごとに以下を定義：

```markdown
## {ページ名} テスト設計

### テスト対象URL
- /lp/ippan-a

### テストケース
1. 正常系: デフォルト表示
2. 正常系: utm_term による動的H1
3. 正常系: モバイル表示
4. 異常系: 不正パラメータ

### 検証項目
- [ ] H1テキストが正しい
- [ ] CTAボタンが表示される
- [ ] リンクが有効
```

### Step 5: 実装

`tests/e2e/` に以下の構造でテストを作成：

```
tests/e2e/
├── critical-paths/
│   ├── lp/
│   │   ├── ippan-a.spec.ts
│   │   ├── shitadori-a.spec.ts
│   │   └── kosho-a.spec.ts
│   └── liff/
│       ├── estimate.spec.ts
│       └── booking.spec.ts
├── visual/
│   └── lp-screenshots.spec.ts
└── smoke/
    └── health-check.spec.ts
```

---

# E2E Testing Reference

## テスト設計思想: Testing Trophy

```
      E2E (10%)  ← クリティカルパスのみ
    Integration (30%)  ← API・コンポーネント連携
  Unit (60%)  ← ビジネスロジック
```

E2Eは**ユーザー影響の大きいクリティカルパス**に限定し、メンテナンスコストを抑える。

## ディレクトリ構造

```
tests/e2e/
├── critical-paths/         # ユーザークリティカルパス
│   ├── lp/                 # LP関連
│   │   ├── dynamic_headline.spec.ts
│   │   └── responsive.spec.ts
│   └── liff/               # LIFFフォーム
│       ├── estimate.spec.ts
│       └── booking.spec.ts
├── visual/                 # Visual Regression
│   └── lp_screenshots.spec.ts
├── smoke/                  # デプロイ後スモーク
│   └── health_check.spec.ts
├── setup/                  # テストセットアップ
│   └── fixtures.ts
├── global-setup.js
└── global-teardown.js
```

## テストカテゴリと優先度

| カテゴリ | 対象 | 実行タイミング | 優先度 |
|---------|------|---------------|--------|
| **smoke** | 疎通確認 | 全デプロイ後 | 最高 |
| **critical-paths** | ユーザーフロー | PR・staging | 高 |
| **visual** | UI崩れ | staging・定期 | 中 |

## テスト作成ガイドライン

### 1. ファイル命名規則
```
{機能名}_{テスト種別}.spec.ts
例: dynamic_headline.spec.ts, estimate_form.spec.ts
```

### 2. テスト構造テンプレート

```typescript
import { test, expect } from '@playwright/test'

test.describe('機能名', () => {
  test.beforeEach(async ({ page }) => {
    // 共通セットアップ
  })

  test('正常系: 期待する動作の説明', async ({ page }) => {
    // Arrange
    await page.goto('/path')

    // Act
    await page.click('button')

    // Assert
    await expect(page.locator('h1')).toContainText('期待値')
  })

  test('異常系: エラーケースの説明', async ({ page }) => {
    // ...
  })
})
```

### 3. セレクタ優先順位

```typescript
// 推奨順位（上から優先）
page.getByRole('button', { name: '送信' })     // 1. Role + accessible name
page.getByLabel('メールアドレス')               // 2. Label
page.getByPlaceholder('example@mail.com')      // 3. Placeholder
page.getByTestId('submit-button')              // 4. data-testid
page.locator('.submit-btn')                    // 5. CSS（最終手段）
```

### 4. 環境URL設定

```typescript
// playwright.config.ts で環境切り替え
const baseURL = process.env.E2E_BASE_URL || 'http://localhost:3000'

// テスト内
await page.goto('/lp/ippan-a')  // baseURLからの相対パス
```

## 実行コマンド

```bash
# 全E2Eテスト実行
pnpm test:e2e

# 特定ファイルのみ
pnpm test:e2e tests/e2e/critical-paths/lp/

# UIモードでデバッグ
pnpm test:e2e --ui

# 特定ブラウザのみ
pnpm test:e2e --project=chromium

# ステージング環境で実行
E2E_BASE_URL=https://staging.applebuyers.jp pnpm test:e2e
```

## モバイルテスト

```typescript
import { devices } from '@playwright/test'

test.use({ ...devices['iPhone 12'] })

test('モバイル表示確認', async ({ page }) => {
  await page.goto('/lp/ippan-a')
  // viewport自動設定済み
})
```

## Visual Regression Testing

```typescript
test('LP スクリーンショット比較', async ({ page }) => {
  await page.goto('/lp/ippan-a')
  await expect(page).toHaveScreenshot('lp-ippan-a.png', {
    fullPage: true,
    maxDiffPixels: 100,  // 許容差分
  })
})
```

初回実行でベースライン作成 → 以降は差分検出

## LIFFテストの注意点

LIFFはLINE SDK依存のため、以下の戦略を採用：

1. **APIモック**: `page.route()` でLINE APIをモック
2. **認証スキップ**: テスト用トークンを環境変数で注入
3. **フォーム操作のみ検証**: LINE送信は手動確認

```typescript
test.beforeEach(async ({ page }) => {
  // LIFF SDK モック
  await page.route('**/liff.line.me/**', route => {
    route.fulfill({ status: 200, body: JSON.stringify({ userId: 'test' }) })
  })
})
```

## CI/CD統合

### ローカルフック（husky + lint-staged）

**コスト: 0（ローカル実行）**

```
[コード編集中]     [コミット時]       [push時]
      ↓                ↓                ↓
  手動実行         pre-commit        pre-push
  pnpm test        lint-staged       Unit Test
```

| フック | 実行内容 | 目的 |
|-------|---------|------|
| **pre-commit** | `pnpm lint-staged` | 変更ファイルのLint |
| **pre-push** | `pnpm test:admin && test:site` | Unit Test実行 |

**設定ファイル:**
- `.husky/pre-commit`: lint-staged実行
- `.husky/pre-push`: Unit Test実行
- `package.json`: lint-staged設定

```json
// package.json
{
  "lint-staged": {
    "admin-app/**/*.{ts,tsx}": ["pnpm --filter @applebuyers/admin-app lint --fix"],
    "public-site/**/*.{ts,tsx}": ["pnpm --filter @applebuyers/public-site lint --fix"]
  }
}
```

### テスト実行タイミング設計

| 環境 | タイミング | 実行テスト | 目的 | コスト |
|------|-----------|-----------|------|--------|
| **ローカル** | コミット時 | lint-staged | 変更ファイルLint | 0 |
| **ローカル** | push時 | Unit Test | 品質確認 | 0 |
| **GitHub Actions** | PR作成時 | Unit + Lint | 早期フィードバック | 1-2分 |
| **GitHub Actions** | main merge時 | Integration + Smoke E2E | 品質ゲート | 3-5分 |
| **GitHub Actions** | staging deploy後 | Critical Path E2E | 本番前検証 | 5-10分 |
| **GitHub Actions** | production deploy後 | Smoke Test | 疎通確認 | 1分 |
| **GitHub Actions** | 週1定期（日曜深夜） | Full E2E + Visual | 回帰検出 | 15-20分 |

### コスト最適化（GitHub Actions）

**1人開発向け: 無料枠（2,000分/月）内で収める設計**

| 施策 | 効果 | 実装 |
|------|------|------|
| `paths-ignore` | 無駄実行50%減 | docs/, README変更は除外 |
| キャッシュ | 30-50%時間短縮 | node_modules + Playwright |
| Chromiumのみ | 1/3の時間 | `--project=chromium` |
| E2Eは収益導線のみ | 実行時間削減 | LP→申込→完了の導線 |
| `retention-days: 7` | ストレージ節約 | アーティファクト保持期間 |

```yaml
# .github/workflows/ci.yml 推奨設定
on:
  pull_request:
    paths-ignore:
      - 'docs/**'
      - '*.md'
      - '.vscode/**'

jobs:
  test:
    runs-on: ubuntu-latest  # macOSは10倍コスト、避ける
    steps:
      - uses: actions/cache@v4
        with:
          path: |
            node_modules
            ~/.cache/ms-playwright
          key: ${{ runner.os }}-deps-${{ hashFiles('pnpm-lock.yaml') }}
```

### GitHub Actions サンプル

```yaml
# staging デプロイ後に自動実行
- name: Run E2E tests on staging
  run: |
    E2E_BASE_URL=${{ secrets.STAGING_URL }} pnpm test:e2e --project=chromium
  env:
    CI: true
```

### 失敗時のデバッグ

```bash
# トレース付きで実行
pnpm test:e2e --trace on

# 失敗時のみトレース保存
pnpm test:e2e --trace retain-on-failure
```

### 障害発生時のテスト追加フロー

```
1. 本番で問題発生
2. 原因特定・修正
3. 同じ問題を検出するE2Eテストを追加
4. 実装トラッキングに記録
5. CI/CDに組み込み → 再発防止
```

## 追加すべきテストの判断基準

以下に該当する場合のみE2Eテストを追加：

1. **収益に直結** - LP、決済、申込フロー
2. **ユーザー影響大** - フォーム送信、認証
3. **過去に障害発生** - 再発防止
4. **複数システム連携** - API→DB→通知

単純なUI変更、内部ツール、稀なエッジケースは**Unit/Integration**で対応。

---

## 実装トラッキング

このセクションは実装状況を追跡する。スキル実行時に更新する。

### カバレッジマトリクス（現状）

| ページ/機能 | Unit | Integration | E2E | Visual | 状態 |
|------------|------|-------------|-----|--------|------|
| LP ippan-a | ✅ | - | ✅ | ✅ | 完了 |
| LP shitadori-a | ✅ | - | ✅ | ✅ | 完了 |
| LP kosho-a | ✅ | - | ✅ | ✅ | 完了 |
| LP model | ✅ | - | ✅ | ✅ | 完了 |
| LIFF 見積もり | ✅ | ✅ | ✅ | - | 完了 |
| LIFF 予約 | ✅ | ✅ | ✅ | - | 完了 |
| GCLID連携 | - | - | ✅ | - | 完了 |
| Smokeテスト | - | - | ✅ | - | 完了 |
| API疎通 | - | - | ✅ | - | 完了 |

### 実装履歴

| 日付 | 追加テスト | 担当 |
|------|-----------|------|
| 2026-01-23 | LP動的H1テスト (dynamic_headline.spec.ts) | Claude |
| 2026-01-23 | Smokeテスト (health_check.spec.ts) | Claude |
| 2026-01-23 | husky + lint-staged設定 | Claude |
| 2026-01-23 | Visual Regression (lp_screenshots.spec.ts) | Claude |
| 2026-01-23 | CI/CDキャッシュ最適化 (ci-pull-request.yml) | Claude |
| 2026-01-23 | 週次回帰テスト (ci-weekly-regression.yml) | Claude |
| 2026-01-23 | 本番LP疎通確認 (deploy-production.yml) | Claude |

### 次のアクション

1. Visual Regressionベースライン生成（初回実行: `pnpm test:e2e tests/e2e/visual/ --update-snapshots`）
2. テストカバレッジ拡大（新機能追加時）
3. フレーキーテストの監視・修正
