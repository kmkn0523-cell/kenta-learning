# finance_web デザイン改善：グラスモーフィズム強化

**日付**: 2026-05-21  
**対象アプリ**: `/home/kenta_kamijyo/finance_web/`  
**ステータス**: 設計承認済み

---

## 背景と目的

現在のfinance_webはダークネイビー×シアンのフィンテックデザインを採用しているが、カードに `backdropFilter` が未設定で、ボーダーも不透明度0.12と非常に薄い。グラスモーフィズム（すりガラス）効果を全体に適用し、高級感のある洗練されたUIに仕上げる。

## 変更方針

- **既存の定数名はそのまま維持**（後方互換性を保つ）
- **定数の中身だけ更新**（各ビュー・コンポーネントの個別修正は不要）
- ビジネスロジック・計算処理・データ永続化は一切変更しない

---

## 変更ファイルと内容

### 1. `src/utils/styles.ts`

#### 既存定数の更新

| 定数 | 変更内容 |
|---|---|
| `STYLE_CARD` | `backdropFilter:"blur(20px)"` / `boxShadow:"0 4px 24px rgba(0,0,0,0.3),0 1px 0 rgba(255,255,255,0.04) inset"` / `border` の不透明度を 0.12→0.18 に引き上げ / `background` を `rgba(15,23,42,0.7)` に変更（現在は0.9） |
| `STYLE_INPUT` | `backdropFilter:"blur(8px)"` を追加 |
| `STYLE_BUTTON_PRIMARY` | `boxShadow:"0 0 20px rgba(34,211,238,0.3),0 0 40px rgba(34,211,238,0.1)"` でシアングロー追加 |

#### 新規追加定数

```ts
// シアン寄りのボーダー色（ヘッダー・アクセントカード用）
export const COLOR_BORDER_GLOW = "rgba(34,211,238,0.18)";
```

### 2. `src/App.tsx`

変更箇所は2カ所のみ（インライン `style` 属性）：

1. **ヘッダーの `borderBottom`**  
   `1px solid ${COLOR_BORDER}` → `1px solid ${COLOR_BORDER_GLOW}`  
   （シアン寄りの微光ボーダーに変更）

2. **ボトムナビのアクティブインジケーター**  
   アクティブタブの2px バーの `boxShadow` を  
   `0 0 8px ${COLOR_ACCENT}` → `0 0 8px ${COLOR_ACCENT},0 0 16px rgba(34,211,238,0.4)` に強化

### 3. `src/components/ui.tsx`

変更対象は2コンポーネント：

1. **`StatLabel`（統計ラベル）**  
   現在: `background:rgba(15,23,42,0.9)`, `border:1px solid ${COLOR_BORDER}`  
   変更後: `backdropFilter:"blur(12px)"` / `boxShadow:"0 2px 12px rgba(0,0,0,0.2)"` / ボーダー不透明度 0.12→0.16

2. **`ProgressBar`（プログレスバー）**  
   バーの `background` をフラットな `COLOR_ACCENT` から  
   `linear-gradient(90deg,#22d3ee,#38bdf8)` のグラデーションに変更

---

## 変更しないもの

- `DashboardView.tsx` / `IncomeView.tsx` / `FixedExpenseView.tsx` / `ExpenseView.tsx` / `LoanView.tsx` / `SettingsView.tsx` の構造・ロジック
- `hooks/` 配下のすべてのカスタムフック
- `utils/format.ts`, `utils/loanCalc.ts` などの計算ユーティリティ
- `types.ts` の型定義
- テストファイル

---

## 検証方法

1. `cd finance_web && npm run dev` でローカル起動
2. ブラウザで `http://localhost:5173` を開く
3. 各タブ（概要・収入・固定費・支出・ローン・設定）を開いてカードのすりガラス感を確認
4. ボタンをタップしてシアングローが表示されることを確認
5. 入力フォーム（支出追加など）を開いて入力欄のガラス感を確認
6. `npm run build` でビルドエラーがないことを確認
