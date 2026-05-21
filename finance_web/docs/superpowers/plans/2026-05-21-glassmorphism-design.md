# グラスモーフィズム強化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** finance_webのカード・入力欄・ボタン・ナビゲーションにグラスモーフィズム（すりガラス）効果を適用し、高級感のあるフィンテックUIに仕上げる

**Architecture:** `src/utils/styles.ts` の共通スタイル定数を更新するだけで、全ビューに変更が自動反映される。個別ビューは触らない。`App.tsx` のインラインスタイル2箇所と `ui.tsx` の2コンポーネントのみ追加修正する。

**Tech Stack:** React 18 + TypeScript + Vite（インラインCSS-in-JS、Tailwind不使用）

---

### Task 1: `styles.ts` — スタイル定数の更新と新定数追加

**Files:**
- Modify: `src/utils/styles.ts`

- [ ] **Step 1: `COLOR_BORDER_GLOW` 定数を追加**

`COLOR_BORDER` の直下に1行追加する。

```ts
export const COLOR_BORDER_GLOW = "rgba(34,211,238,0.18)"; // シアン寄りの微光ボーダー（ヘッダー・アクセント用）
```

- [ ] **Step 2: `STYLE_CARD` を更新**

現在の行（line 16）をそのまま置き換える。

```ts
// カードのスタイル（グラスモーフィズム：すりガラス効果でカードに奥行きを出す）
export const STYLE_CARD = {background:"rgba(15,23,42,0.7)",backdropFilter:"blur(20px)",border:"1px solid rgba(148,163,184,0.18)",borderRadius:18,padding:20,marginBottom:14,boxShadow:"0 4px 24px rgba(0,0,0,0.3),0 1px 0 rgba(255,255,255,0.04) inset"};
```

- [ ] **Step 3: `STYLE_INPUT` を更新**

`backdropFilter:"blur(8px)"` を追加する。

```ts
// 入力欄（input/select）の共通スタイル（すりガラス効果を追加）
export const STYLE_INPUT = {background:"rgba(148,163,184,0.06)",backdropFilter:"blur(8px)",border:`1px solid ${COLOR_BORDER}`,borderRadius:12,padding:"12px 14px",color:COLOR_TEXT_PRIMARY,fontSize:16,outline:"none",width:"100%",fontFamily:"inherit",minHeight:46,boxSizing:"border-box" as const};
```

- [ ] **Step 4: `STYLE_BUTTON_PRIMARY` を更新**

`boxShadow` でシアングローを追加する。

```ts
// プライマリボタン（保存・追加など）の共通スタイル（シアングローを追加）
export const STYLE_BUTTON_PRIMARY = {border:"none",borderRadius:12,padding:"13px 0",cursor:"pointer",fontSize:15,fontWeight:700,background:COLOR_ACCENT,color:"#070b14",width:"100%",fontFamily:"inherit",minHeight:46,boxShadow:"0 0 20px rgba(34,211,238,0.3),0 0 40px rgba(34,211,238,0.1)"};
```

- [ ] **Step 5: ビルドエラーがないか確認**

```
cd /home/kenta_kamijyo/finance_web && npm run build
```

期待値: エラーなし（`dist/` が生成される）

- [ ] **Step 6: コミット**

```
cd /home/kenta_kamijyo/finance_web
git add src/utils/styles.ts
git commit -m "style: グラスモーフィズム強化 - styles.ts 定数更新"
```

---

### Task 2: `App.tsx` — ヘッダーとボトムナビのグロー強化

**Files:**
- Modify: `src/App.tsx:1-10`（importに `COLOR_BORDER_GLOW` を追加）
- Modify: `src/App.tsx:151`（ヘッダーの borderBottom）
- Modify: `src/App.tsx:281`（アクティブタブのインジケーター boxShadow）

- [ ] **Step 1: `COLOR_BORDER_GLOW` を import に追加**

App.tsx の先頭にある styles.ts の import 行に `COLOR_BORDER_GLOW` を追記する。

現在の import（行番号はファイル先頭付近）:
```ts
import { COLOR_BACKGROUND, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_HINT, COLOR_BORDER, COLOR_ACCENT, COLOR_POSITIVE, COLOR_NEGATIVE, STYLE_CARD, STYLE_INPUT, STYLE_BUTTON_PRIMARY, STYLE_BUTTON_OUTLINE, COLOR_SURFACE } from "./utils/styles";
```

変更後（`COLOR_BORDER_GLOW` を追加）:
```ts
import { COLOR_BACKGROUND, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_HINT, COLOR_BORDER, COLOR_BORDER_GLOW, COLOR_ACCENT, COLOR_POSITIVE, COLOR_NEGATIVE, STYLE_CARD, STYLE_INPUT, STYLE_BUTTON_PRIMARY, STYLE_BUTTON_OUTLINE, COLOR_SURFACE } from "./utils/styles";
```

- [ ] **Step 2: ヘッダーの `borderBottom` を `COLOR_BORDER_GLOW` に変更**

line 151 付近のヘッダー `<div>` のスタイル内:

変更前:
```ts
borderBottom:`1px solid ${COLOR_BORDER}`
```

変更後:
```ts
borderBottom:`1px solid ${COLOR_BORDER_GLOW}`
```

- [ ] **Step 3: アクティブタブインジケーターの `boxShadow` を強化**

line 281 付近のアクティブインジケーター `<div>` の `boxShadow`:

変更前:
```ts
boxShadow:`0 0 8px ${COLOR_ACCENT}`
```

変更後:
```ts
boxShadow:`0 0 8px ${COLOR_ACCENT},0 0 16px rgba(34,211,238,0.4)`
```

- [ ] **Step 4: ビルドエラーがないか確認**

```
cd /home/kenta_kamijyo/finance_web && npm run build
```

期待値: エラーなし

- [ ] **Step 5: コミット**

```
cd /home/kenta_kamijyo/finance_web
git add src/App.tsx
git commit -m "style: グラスモーフィズム強化 - App.tsx ヘッダー・ナビグロー"
```

---

### Task 3: `ui.tsx` — `StatLabel` と `ProgressBar` の強化

**Files:**
- Modify: `src/components/ui.tsx:77`（StatLabel のスタイル）
- Modify: `src/components/ui.tsx:97`（ProgressBar のバーの background）

- [ ] **Step 1: `StatLabel` のスタイルを更新**

line 77 の `<div>` スタイルを置き換える（`backdropFilter`・`boxShadow`・ボーダー不透明度 0.12→0.16）。

変更前:
```ts
<div style={{background:"rgba(148,163,184,0.05)",border:`1px solid ${COLOR_BORDER}`,borderRadius:14,padding:"14px 8px",textAlign:"center"}}>
```

変更後:
```ts
<div style={{background:"rgba(15,23,42,0.6)",backdropFilter:"blur(12px)",border:"1px solid rgba(148,163,184,0.16)",borderRadius:14,padding:"14px 8px",textAlign:"center",boxShadow:"0 2px 12px rgba(0,0,0,0.2)"}}>
```

- [ ] **Step 2: `ProgressBar` のバーを線形グラデーションに変更**

line 97 の内側 `<div>` の `background` 属性を変更する。

変更前:
```ts
<div style={{height:"100%",borderRadius:4,background:color,width:Math.min(100,(value/(max||1))*100)+"%",transition:"width 0.4s ease"}}/>
```

変更後:
```ts
<div style={{height:"100%",borderRadius:4,background:`linear-gradient(90deg,#22d3ee,#38bdf8)`,width:Math.min(100,(value/(max||1))*100)+"%",transition:"width 0.4s ease"}}/>
```

> **注意:** `color` プロップは引き続き受け取るが（型互換のため）、バー表示はグラデーションに統一する。

- [ ] **Step 3: ビルドエラーがないか確認**

```
cd /home/kenta_kamijyo/finance_web && npm run build
```

期待値: エラーなし

- [ ] **Step 4: コミット**

```
cd /home/kenta_kamijyo/finance_web
git add src/components/ui.tsx
git commit -m "style: グラスモーフィズム強化 - ui.tsx StatLabel・ProgressBar"
```

---

### Task 4: 目視確認とデプロイ

**Files:** なし（確認のみ）

- [ ] **Step 1: ローカルで起動**

```
cd /home/kenta_kamijyo/finance_web && npm run dev
```

- [ ] **Step 2: ブラウザで `http://localhost:5173` を開いて確認**

以下を順番に確認する:
1. 概要タブ → カードがすりガラスになっているか（背後の背景がうっすら見えるか）
2. 支出タブ → 「支出を追加」フォームを開き、入力欄にガラス感があるか
3. ローンタブ → StatLabel の小パーツが奥行きあるガラス感か
4. ボトムナビ → 「概要」タブのアクティブインジケーターにグロー（光の滲み）があるか
5. 保存ボタン（支出追加など）→ シアンのグロー光が出ているか

- [ ] **Step 3: 本番デプロイ**

```
cd /home/kenta_kamijyo/finance_web && npx vercel --prod
```

期待値: デプロイ完了 URL が表示される

- [ ] **Step 4: デプロイ後の動作確認**

スマホ（またはブラウザのDevTools モバイルエミュレーター）で本番 URL を開き、Step 2 と同じ箇所を確認する。
