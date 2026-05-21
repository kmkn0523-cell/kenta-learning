# チュートリアル機能 設計仕様書

## 概要

家計管理アプリ（finance_web）に初回起動時チュートリアルと再表示機能を追加する。
初回訪問ユーザーがアプリの使い方をすぐ理解できるよう、6ページのスライド式モーダルで各タブを紹介する。

---

## 要件

### 機能要件

- 初回アクセス時に自動でチュートリアルモーダルを表示する
- `localStorage["kk_tutorial_done"] === "1"` のとき表示しない（2回目以降）
- SettingsView に「使い方を見る」ボタンを追加し、いつでも再表示できる
- モーダルを閉じると `localStorage["kk_tutorial_done"] = "1"` をセットする
- ×ボタン・「はじめる」ボタンのどちらで閉じても同じ動作

### 非機能要件

- 既存の暗号化・パスワード認証フローには一切影響しない
- 新しい npm パッケージは追加しない
- 既存のスタイル変数（`utils/styles.ts`）を使う

---

## アーキテクチャ

```
App.tsx
├── showTutorial state（初期値: localStorage["kk_tutorial_done"] !== "1"）
├── handleCloseTutorial() → localStorage セット → showTutorial=false
├── <TutorialModal open={showTutorial} onClose={handleCloseTutorial} />
└── SettingsView に onOpenTutorial={() => setShowTutorial(true)} を渡す

src/components/TutorialModal.tsx（新規作成）
├── props: open: boolean, onClose: () => void
├── state: page: number（0〜5）
├── PAGES 配列（6要素）でコンテンツを管理
└── open=false のとき null を返す

src/views/SettingsView.tsx（変更）
├── props に onOpenTutorial: () => void を追加
└── カテゴリ管理カードの下に「使い方を見る」ボタンを追加
```

---

## コンポーネント仕様: TutorialModal

### Props

```tsx
interface TutorialModalProps {
  open: boolean;
  onClose: () => void;
}
```

### 内部 State

```tsx
const [page, setPage] = useState(0);
```

モーダルが開くたびに page を 0 にリセット（useEffect で open 変化を監視）。

### PAGES 配列

```tsx
const PAGES = [
  {
    icon: "💰",
    title: "ようこそ！",
    desc: "このアプリは収入・支出・ローン・貯金目標をまとめて管理できる家計管理ツールです。データはすべてこの端末に暗号化保存されます。",
  },
  {
    icon: "💰",
    title: "収入タブ",
    desc: "給与・副業・ボーナスなどの収入を登録します。カテゴリごとに分類でき、月ごとの合計が自動集計されます。",
  },
  {
    icon: "📌",
    title: "固定費タブ",
    desc: "家賃・保険・サブスクなど毎月決まって出ていく費用を登録します。年払いも月割りで自動換算されます。",
  },
  {
    icon: "💸",
    title: "支出タブ",
    desc: "食費・交通費など変動する日々の出費を記録します。カテゴリ別に集計・グラフ表示されます。",
  },
  {
    icon: "🏦",
    title: "ローンタブ",
    desc: "住宅ローン・カーローンなどを登録し、返済シミュレーションができます。繰り上げ返済の効果も試算できます。",
  },
  {
    icon: "⚙️",
    title: "設定タブ",
    desc: "カテゴリの追加・編集・並び替えができます。データのバックアップ（JSON書き出し）と復元もここから行えます。",
  },
];
```

### UI レイアウト

```
┌──────────────────────────────┐
│                           ✕  │  ← 右上：いつでも閉じる
│                              │
│         💰（大アイコン）        │
│      ようこそ！（タイトル）      │
│   このアプリは…（説明文2〜3行）  │
│                              │
│   ●○○○○○  ← ページドット    │
│                              │
│  [      次へ      ]          │  ← 最終ページは「はじめる」
└──────────────────────────────┘
```

### スタイル方針

- 背景オーバーレイ: `rgba(0,0,0,0.72)`、タップしても閉じない（誤操作防止）
- モーダル本体: `rgba(15,23,42,0.98)`、`backdropFilter:"blur(20px)"`、borderRadius:22
- 「次へ」ボタン: `STYLE_BUTTON_PRIMARY`
- 「はじめる」ボタン: `STYLE_BUTTON_PRIMARY`（緑系: `#34d399`）
- ページドット: 現在ページ `#818cf8`、他 `rgba(255,255,255,0.2)`

---

## App.tsx への変更

```tsx
// 追加する state
const [showTutorial, setShowTutorial] = useState(
  () => localStorage.getItem("kk_tutorial_done") !== "1"
);

// 追加する関数
function handleCloseTutorial() {
  localStorage.setItem("kk_tutorial_done", "1");
  setShowTutorial(false);
}
```

JSX に追加:
```tsx
<TutorialModal open={showTutorial} onClose={handleCloseTutorial} />
```

SettingsView の呼び出しに追加:
```tsx
<SettingsView ... onOpenTutorial={() => setShowTutorial(true)} />
```

---

## SettingsView.tsx への変更

### Props 変更

```tsx
interface SettingsViewProps {
  // ... 既存
  onOpenTutorial: () => void;  // 追加
}
```

### ボタン追加箇所

アプリ情報カードの直前（カテゴリ管理カードの下）に追加:

```tsx
<div style={{ ...STYLE_CARD, marginTop: 16 }}>
  <button
    onClick={props.onOpenTutorial}
    style={{ ...STYLE_BUTTON_OUTLINE, width: "100%" }}
  >
    📖 使い方を見る
  </button>
</div>
```

---

## localStorage キー

| キー | 値 | 意味 |
|------|-----|------|
| `kk_tutorial_done` | `"1"` | チュートリアル表示済み |

既存の `kk_*` キーとの命名統一を維持。

---

## テスト観点

1. 初回アクセス（`kk_tutorial_done` なし）→ モーダルが自動表示される
2. 「次へ」を5回押すと「はじめる」が表示される
3. 「はじめる」で閉じると `kk_tutorial_done === "1"` になる
4. 再読み込み後はモーダルが自動表示されない
5. SettingsView の「使い方を見る」でモーダルが開く
6. ✕ボタンで閉じると同じく `kk_tutorial_done === "1"` になる
7. SettingsView 経由で再表示したとき、page が 0 にリセットされる

---

## 影響範囲

| ファイル | 変更種別 |
|---------|---------|
| `src/components/TutorialModal.tsx` | 新規作成 |
| `src/App.tsx` | state 追加・JSX 追加・SettingsView への props 追加 |
| `src/views/SettingsView.tsx` | props 追加・ボタン追加 |
