# finance_web 改修設計書

- **作成日**: 2026-05-15
- **対象**: `/home/kenta_kamijyo/finance_web`（家計管理アプリ、Vercel デプロイ済み）
- **目的**: コード品質・アーキテクチャ・新機能を 3 フェーズで一気に改修し、保守性と使い勝手を向上させる
- **承認状況**: Phase 1〜3 すべてユーザー承認済み

---

## 1. 背景と現状の課題

`finance_web` は React 18 + TypeScript + Vite で書かれた家計管理アプリ。データは AES-GCM 暗号化して localStorage に保存し、PWA ではないがブラウザだけで完結する。コアロジックは動いており、Threads ボット等の稼働中システムには影響しない独立アプリ。

コードを全ファイル読んだ結果、改修すべき課題を 3 階層に整理した。

### Critical（最優先 — 動作・保守性に直結）

| 課題 | 場所 | 影響 |
|---|---|---|
| `App.tsx` が 430 行の god component | `src/App.tsx` | 変更コスト高、再レンダリング多発、テスト困難 |
| `usePersist.ts` でモジュールレベル `let mem` が共有 | `src/hooks/usePersist.ts` | 別キーの値が混ざる潜在バグ |
| `MN` (MonthNav) / `ST` (StatBlock) が App 内部で定義 | `src/App.tsx` | 毎レンダリングで新インスタンス → 子の state リセット、パフォーマンス低下 |
| 空 catch ブロック多数（`try { } catch (_) {}`） | `usePersist`, `crypto`, `PasswordGate`, `LoanSection` | エラーが握りつぶされて原因追跡不能 |

### High（品質・型安全に直結）

| 課題 | 場所 | 影響 |
|---|---|---|
| 略称命名が読みづらい（`tx`, `fx`, `lo`, `cf`, `bl`, `inc`, `a1`-`a9`, `sm`, `sy`, `ms`, `mTx`, `tVar`, `tFx`, `MN`, `ST`） | `App.tsx` | 新規参加者・将来の自分が読めない |
| スタイル定数が 1〜3 文字（`BG`, `T`, `T2`, `T3`, `BD`, `AC`, `POS`, `NEG`, `CARD`, `IS`, `BS`, `OS`） | `src/utils/styles.ts` | 用途不明、grep でヒットしすぎる |
| format/loanCalc も略称（`MLS`, `ECATS`, `EICO`, `mInt`, `tInt`, `cDate`, `yen`） | `src/utils/format.ts`, `src/utils/loanCalc.ts` | 同上 |
| UI コンポーネント名が短すぎ（`Inp`, `Sel`, `Bar`） | `src/components/ui.tsx` | 特に `Bar` は recharts の `Bar` と衝突して混乱 |
| `amount: number \| string` 混在 | `src/types.ts` | 集計時に `Number()` 必須、バグ温床 |
| `useState(null)` で型未指定 | `PasswordGate.tsx` の `cryptoKey` ほか | 型推論が `null` のみになり実値を入れた時に型エラー |
| 派生値の useMemo 未使用 | `App.tsx` | `totalVariable`, `monthlyTransactions` 等を毎レンダリング再計算 |

### Medium（UX・機能不足）

| 課題 | 影響 |
|---|---|
| PWA ではないのでホーム画面追加・オフライン起動不可 | スマホで使うときに毎回ブラウザ起動 |
| 取引と口座が紐づいていない | 残高が口座別に追えない、振替の概念がない |
| 取引検索・絞り込みなし | 件数が増えると目的の取引を探せない |
| カテゴリがハードコード（`ECATS` 等） | ユーザーごとの家計事情に合わない |

---

## 2. Phase 1 — コード品質改善

### 2-1. 命名統一（リネーム）

#### `src/utils/styles.ts`

| Before | After | 用途 |
|---|---|---|
| `BG` | `COLOR_BACKGROUND` | ページ背景 |
| `T` | `COLOR_TEXT_PRIMARY` | メインテキスト |
| `T2` | `COLOR_TEXT_SECONDARY` | サブテキスト |
| `T3` | `COLOR_TEXT_HINT` | ヒント・補足 |
| `BD` | `COLOR_BORDER` | ボーダー |
| `AC` | `COLOR_ACCENT` | アクセント |
| `POS` | `COLOR_POSITIVE` | プラス・収入の緑 |
| `NEG` | `COLOR_NEGATIVE` | マイナス・支出の赤 |
| `CARD` | `STYLE_CARD` | カード共通スタイル |
| `IS` | `STYLE_INPUT` | 入力欄共通 |
| `BS` | `STYLE_BUTTON_PRIMARY` | プライマリボタン |
| `OS` | `STYLE_BUTTON_OUTLINE` | セカンダリボタン |

#### `src/utils/format.ts`

| Before | After |
|---|---|
| `MLS` | `MONTH_LABELS` |
| `ECATS` | `EXPENSE_CATEGORIES` |
| `FCATS` | `FIXED_EXPENSE_CATEGORIES` |
| `ICATS` | `INCOME_CATEGORIES` |
| `EICO` | `EXPENSE_CATEGORY_ICONS` |
| `FICO` | `FIXED_EXPENSE_CATEGORY_ICONS` |
| `IICO` | `INCOME_CATEGORY_ICONS` |
| `yen` | `formatYen` |
| `parseAmount` | `parseYenAmount` |
| `formatAmount` | （維持。すでに分かりやすい） |

#### `src/utils/loanCalc.ts`

| Before | After |
|---|---|
| `mInt` | `calculateMonthlyInterest` |
| `tInt` | `calculateTotalInterest` |
| `cDate` | `calculateCompletionDate` |
| `RATE_TABLES` | （維持） |

#### `src/components/ui.tsx`

| Before | After | 補足 |
|---|---|---|
| `Inp` | `Input` | |
| `Sel` | `Select` | |
| `Bar` | `ProgressBar` | recharts の `Bar` と衝突回避 |
| `Stat` | `StatLabel` | |
| `PwInput` | `PasswordInput` | |
| `Toast` | （維持） | |
| `Dlg` | `ConfirmDialog` | 用途明示 |

#### `src/App.tsx`

| Before | After |
|---|---|
| `tx` / `setTx` | `transactions` / `setTransactions` |
| `fx` / `setFx` | `fixedExpenses` / `setFixedExpenses` |
| `lo` / `setLo` | `loans` / `setLoans` |
| `cf` / `setCf` | `cashFlow` / `setCashFlow` |
| `bl` / `setBl` | `balance` / `setBalance` |
| `inc` / `setInc` | `incomes` / `setIncomes` |
| `a1`〜`a9` | 口座 ID をキーにした構造体へ変更。既存データの口座順序を変えないため、実装時に現在の localStorage 値を読み取り、配列添字（0〜8）と新キー名（例: `account_0`, `account_1`, …）の対応表を作って 1:1 で移行する。表示名はユーザーが UI で編集できるようにする |
| `sm` | `selectedMonth` |
| `sy` | `selectedYear` |
| `ms` | `monthString` |
| `mTx` | `monthlyTransactions` |
| `mInc` | `monthlyIncomes` |
| `tVar` | `totalVariableExpense` |
| `tFx` | `totalFixedExpense` |
| `tRep` | `totalLoanRepayment` |
| `tInc` | `totalIncome` |
| `tBur` | `totalBurden` |
| `MN` | `MonthNav`（外部ファイル化、後述） |
| `ST` | `StatBlock`（外部ファイル化、後述） |

### 2-2. 型安全強化

#### `src/types.ts`

```ts
// Before
interface Tx { amount: number | string; ... }

// After
interface Tx { amount: number; ... }
```

文字列で保持していたのはフォーム入力中の一時状態のため。フォーム側で `parseYenAmount(text)` を経由して `number` に変換してから保存する。

#### `src/utils/crypto.ts`

すべての関数に型を付ける:

```ts
// Before
export function simpleHash(s) { ... }

// After
export function simpleHash(input: string): string { ... }

export async function makeNewHash(password: string): Promise<string> { ... }
export async function verifyNewHash(password: string, savedHash: string): Promise<boolean> { ... }
export function isLegacyHash(hash: string): boolean { ... }
export async function deriveEncryptionKey(password: string, salt: Uint8Array): Promise<CryptoKey> { ... }
export function getOrCreateEncSalt(): Uint8Array { ... }
```

#### useState のジェネリック明示

```ts
// Before
const [cryptoKey, setCryptoKey] = useState(null);

// After
const [cryptoKey, setCryptoKey] = useState<CryptoKey | null>(null);
```

`PasswordGate.tsx`, `BudgetSection.tsx` の `actual`, `draft` などを `Record<string, number>` / `Record<string, string>` で明示。

### 2-3. エラーハンドリング

```ts
// Before
try { localStorage.setItem(...); } catch(_){}

// After
try {
  localStorage.setItem(...);
} catch (error) {
  console.warn("[usePersist] localStorage 書き込み失敗", { key, error });
}
```

対象:
- `src/hooks/usePersist.ts`(line 33, 42, 49, 56, 71 付近)
- `src/utils/crypto.ts`(line 91, 94 付近)
- `src/components/PasswordGate.tsx`(line 21, 62, 117 付近)
- `src/components/LoanSection.tsx`の空 catch

ユーザー操作起因のエラー（ログイン失敗の鍵派生エラー等）は `Toast` で通知する。バックグラウンドの軽微なエラーは `console.warn` のみ。

### 2-4. 互換性保証（Phase 1）

- localStorage キー全て不変: `kk_pw_hash`, `ff_auth`, `ff_fail`, `ff_lock`, 暗号化エントリ
- AES-GCM 鍵派生（PBKDF2 100000 iterations, SHA-256, 16-byte salt）変更なし → 既存データは引き続き読める
- 既存 Vitest 全 pass
- 新規テスト追加: 旧ハッシュ形式→新形式アップグレード、暗号化往復、エラーハンドリングのログ出力

---

## 3. Phase 2 — アーキテクチャ改善

### 3-1. App.tsx 分割

現状 430 行を、約 100 行のルーター + 各 view に分割。

```
src/
├─ App.tsx              # state 保持・タブ切替のみ（~100行）
└─ views/
   ├─ DashboardView.tsx     # トップ画面（月次サマリ・グラフ・予算）
   ├─ IncomeView.tsx        # 収入タブ
   ├─ FixedExpenseView.tsx  # 固定費タブ
   ├─ ExpenseView.tsx       # 変動支出タブ
   └─ LoanView.tsx          # ローン・借金タブ
```

※ Phase 3 で `SettingsView.tsx`（カテゴリ管理 UI）を追加。Phase 2 では空タブとして枠だけ用意するのではなく Phase 3 のタイミングで追加する。

state（`transactions`, `incomes`, `fixedExpenses`, `loans`, `accounts`, `budget` 等）は App.tsx に集約。各 view には必要なものだけ props で渡す。setter も props で渡す。

### 3-2. インラインコンポーネント外部化

- `src/components/MonthNav.tsx`（旧 MN）— 月選択 UI
- `src/components/StatBlock.tsx`（旧 ST）— サマリ表示ブロック

App.tsx 内に書いてあるとレンダリングごとに新コンポーネント扱いになるため、外部ファイルへ。

### 3-3. メモ化

App.tsx の派生値を `useMemo` で包む:

```ts
const monthString = useMemo(
  () => `${selectedYear}-${String(selectedMonth + 1).padStart(2, "0")}`,
  [selectedYear, selectedMonth]
);

const monthlyTransactions = useMemo(
  () => transactions.filter(t => t.date?.startsWith(monthString)),
  [transactions, monthString]
);

const monthlyIncomes = useMemo(
  () => incomes.filter(i => i.date?.startsWith(monthString)),
  [incomes, monthString]
);

const totalVariableExpense = useMemo(
  () => monthlyTransactions.reduce((sum, t) => sum + Number(t.amount || 0), 0),
  [monthlyTransactions]
);

// totalFixedExpense, totalLoanRepayment, totalIncome, totalBurden も同様
```

### 3-4. usePersist のモジュールレベル `mem` バグ修正

```ts
// Before
let mem: any;  // モジュールトップ — 全フックインスタンスで共有！

export function usePersist<T>(key: string, initialValue: T) {
  // mem を使う処理 ...
}

// After
export function usePersist<T>(key: string, initialValue: T) {
  const memRef = useRef<T | null>(null);
  // memRef.current を使う処理 ...
}
```

`useRef` でフック内部に閉じ込めることで、別キーのインスタンス間で値が混ざるバグを根絶。

### 3-5. カスタムフック抽出

#### `src/hooks/useMonthlyData.ts`

```ts
export function useMonthlyData(
  transactions: Tx[],
  incomes: Income[],
  selectedYear: number,
  selectedMonth: number,
) {
  const monthString = useMemo(...);
  const monthlyTransactions = useMemo(...);
  const monthlyIncomes = useMemo(...);
  return { monthString, monthlyTransactions, monthlyIncomes };
}
```

#### `src/hooks/useAutoPayment.ts`

App.tsx 内で `useEffect` 経由で動かしている固定費・ローンの月次自動引き落とし処理（毎月 1 日に当月分の取引を自動生成）をそのまま hook へ移植する。ロジックは変更せず、依存配列・副作用のタイミング・冪等性ガード（同じ月に二重実行しない仕組み）も既存の挙動を維持する。

#### `src/hooks/useDataExport.ts`

CSV/JSON エクスポート関数を提供。React 外でも使えるよう、純粋関数は `src/utils/dataExport.ts` に置きつつ、ファイルダウンロード処理（Blob 生成・`<a>` クリック）は hook で扱う。

### 3-6. ユーティリティ抽出

#### `src/utils/dataExport.ts`

```ts
export function transactionsToCsv(transactions: Tx[]): string { ... }
export function exportAsJson(data: object): string { ... }
export function downloadFile(filename: string, content: string, mime: string): void { ... }
```

### 3-7. 互換性保証（Phase 2）

- 機能変更なし、内部構造のみ整理
- 既存 localStorage キー不変
- 既存テストはすべて pass
- 新規テスト追加:
  - `useMonthlyData` の月境界テスト（月初・月末・年またぎ）
  - `usePersist` の複数キー並行使用テスト（modular `mem` バグ再発防止）
  - 各 view コンポーネントの描画スモークテスト

---

## 4. Phase 3 — 新機能

### 4-1. PWA 化

#### 追加ライブラリ（要承認）

- `vite-plugin-pwa`（npm install 前に承認確認）

#### 設定

- `vite.config.ts` に PWA プラグイン追加
- `public/manifest.webmanifest`:
  ```json
  {
    "name": "家計管理",
    "short_name": "家計",
    "theme_color": "#070b14",
    "background_color": "#070b14",
    "display": "standalone",
    "start_url": "/",
    "icons": [
      { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png" },
      { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png" }
    ]
  }
  ```
- Service Worker: 静的アセット（index.html, JS, CSS, アイコン）を precache
- データはオフラインでも localStorage で動作（変更不要）
- iOS Safari の Add to Home Screen 対応のため、`index.html` に `apple-touch-icon` リンクも追加

### 4-2. 口座ひも付け＋振替機能

#### 型拡張（後方互換）

```ts
// src/types.ts
interface Tx {
  // ... 既存フィールド
  accountId?: string;  // 新規・任意。引き落とし元口座 ID
}

interface Income {
  // ... 既存
  accountId?: string;  // 新規・任意。入金先口座 ID
}

interface Transfer {  // 完全新規型
  id: string;
  date: string;
  fromAccountId: string;
  toAccountId: string;
  amount: number;
  memo?: string;
}
```

`accountId` を optional にすることで既存データはそのまま読める。

#### UI

- 取引フォーム（変動支出・固定費・収入）に「口座」セレクター追加（任意、未選択でも保存可）
- ダッシュボードに「振替」セクション追加（新規型 Transfer の一覧と追加フォーム）
- 口座残高計算ロジック更新:
  - 残高 = 初期残高 + 紐づく入金 - 紐づく出金 - 振替送金 + 振替受取
  - `accountId` 未設定の取引は残高計算に含めない（互換のため）

#### 永続化

- `transfers` を新規 localStorage キーで保存（暗号化対象に追加）
- キー名: `kk_transfers`

### 4-3. 取引検索・絞り込み

`src/views/ExpenseView.tsx` 上部に検索バー追加:

- **テキスト検索**: メモ・カテゴリ名で部分一致（大文字小文字無視）
- **カテゴリ絞り込み**: 複数選択チェックボックス
- **期間絞り込み**: 開始日〜終了日
- **金額レンジ**: 最小〜最大
- **並び替え**: 日付昇降、金額昇降

検索条件は `useState` でコンポーネント内に持つ。リロードでリセット。フィルタリングは `useMemo`。

同様の検索 UI を `IncomeView.tsx` にも追加（収入の絞り込み用）。

### 4-4. カテゴリカスタマイズ

#### 型拡張

```ts
// src/types.ts
interface CategoryItem {
  name: string;
  icon: string;
}

interface CategoryConfig {
  expense: CategoryItem[];
  fixedExpense: CategoryItem[];
  income: CategoryItem[];
}
```

#### 初期値・フォールバック

- 初期値は現在の `EXPENSE_CATEGORIES` + `EXPENSE_CATEGORY_ICONS` をマージしたもの
- localStorage に未保存なら初期値を返す → 既存ユーザーは挙動が変わらない
- 暗号化対象に `kk_categories` 追加

#### UI

- 新規 `src/views/SettingsView.tsx` を追加し、その中にカテゴリ管理 UI を配置（タブとして「設定」を追加）
- カテゴリの追加・編集・削除・並び替え
- 既存取引のカテゴリは名前ベース参照のため、リネーム時は紐づく取引のカテゴリ名も書き換え（バッチ更新）
- 削除時のガード: 既存取引で使われているカテゴリは削除前に確認ダイアログ（「○件の取引に紐づいています。先にカテゴリを変更してください」）
- 「カテゴリをリセット」ボタン: カテゴリ設定だけ初期化（取引データは触らない）

### 4-5. 互換性保証（Phase 3）

- 既存 localStorage データは Phase 3 後も読める（新フィールドはすべて optional）
- カテゴリ未保存ユーザーは初期値が表示される
- 振替・口座紐付けを使わなくても既存機能はそのまま動く

---

## 5. 横断事項

### 5-1. データモデル変更まとめ

| ファイル | 変更内容 | 互換性 |
|---|---|---|
| `src/types.ts` | `amount: number \| string` → `amount: number` | フォーム側で文字列→数値変換するので既存データの読み込みには影響なし |
| `src/types.ts` | `Tx.accountId?`, `Income.accountId?` 追加 | optional なので既存データそのまま読める |
| `src/types.ts` | `Transfer` 型新規 | 新規データ型、既存に影響なし |
| `src/types.ts` | `CategoryConfig` 型新規 | 未保存時は初期値フォールバック |
| localStorage | `kk_transfers`, `kk_categories` 追加 | 既存キー不変 |

### 5-2. テスト戦略

#### Phase 1
- 既存テストの命名追従（リネーム）
- 新規: crypto 関数の型安全テスト、空 catch 廃止後のエラーログテスト

#### Phase 2
- `useMonthlyData` の月境界テスト（年またぎ、月初月末）
- `usePersist` 複数キー並行使用テスト（`mem` バグ再発防止）
- 各 view の描画スモークテスト

#### Phase 3
- PWA manifest 検証（ビルド成果物に manifest が含まれるか）
- Transfer 振替時の残高計算テスト
- 検索フィルタの各条件テスト（テキスト・カテゴリ・期間・金額・並び替え）
- カテゴリリネーム時の取引データ書き換えテスト
- カテゴリ削除ガードテスト

### 5-3. 移行計画

実装は Phase 1 → 2 → 3 の順に進める。各 Phase の完了基準:

- **Phase 1 完了**: 既存テスト全 pass、リネーム後の grep で旧名称が残っていない、空 catch がゼロ
- **Phase 2 完了**: App.tsx が 100 行以下、各 view が独立ファイル、`useMemo` で派生値メモ化、`mem` バグテスト pass
- **Phase 3 完了**: ホーム画面追加が動作、振替で残高が正しく増減、検索で目的の取引が見つかる、カテゴリのカスタマイズと取引データ整合性確保

### 5-4. リスクと対策

| リスク | 対策 |
|---|---|
| リネームでビルドが壊れる | 1 ファイルずつリネーム→ビルド確認のループ、IDE のリネーム機能を活用 |
| `amount: number` 化で既存データ読み込み失敗 | 読み込み時に `Number(value)` で正規化、テストで旧データ形式を確認 |
| `usePersist` の useRef 化で復号タイミングがズレる | 既存テスト + 複数キーテストで検証、`ready` フラグの返却タイミング不変を確認 |
| PWA 化で iOS Safari がキャッシュを掴んで更新されない | Service Worker のバージョニング、ユーザー向けに「アプリを再インストール」手順を README に記載 |
| 振替機能追加で口座残高の二重計上 | 残高計算ロジックの単体テスト、`accountId` 未設定の取引を残高計算から除外 |
| カテゴリリネームで取引データの参照が壊れる | リネーム時にバッチで取引データの category フィールドも書き換え、トランザクション的に処理 |

### 5-5. やらないこと（YAGNI）

- 外部 API 連携（銀行口座連携、レシート OCR 等）
- マルチユーザー対応
- クラウド同期
- 多通貨対応
- 詳細レポート（年次・週次グラフ等、Phase 4 以降検討）
- アクセシビリティ強化（ARIA 属性、キーボードナビ等、別 PR）
