# 収益ファースト・ブラッシュアップ（v1.6.0）設計書

作成日: 2026-06-11
対象: finance_web（BYB — Before You Broke）
ゴール: **「SNSで紹介投稿を出せる状態」** にアプリを整える。収益導線と集客の受け皿を整備し、壊れた広告リンクを修正する。

## 背景・課題

2026-06-11 時点の調査で見つかった問題:

1. **壊れたアフィリエイトリンクが本番公開中** — `src/views/LoanView.tsx` の `AFFILIATE` 定数 9件中5件が審査待ちプレースホルダーURL（`PROMISE_VISA_PLACEHOLDER` 等）のまま表示されている。タップすると壊れたページに飛ぶ
2. **収益導線がローンタブ最下部のみ** — ローンを使わないユーザーには広告が一切露出しない。家計診断カードが診断結果を収益につなげていない
3. **アプリの「顔」がない** — URLを開くといきなりパスワード画面。SNS流入者に価値が伝わらず、TODOの「SNSで紹介投稿」の受け皿が弱い
4. **品質面の小さなずれ** — `package.json` が `1.2.2` のまま（実態 v1.5.0+）

## スコープ

### やること

| # | 項目 | 内容 |
|---|------|------|
| ① | アフィリエイト整理 | リンク定義を `src/utils/affiliates.ts` に一元化。承認済み4件のみ表示。審査待ち5件はコメント保持で非表示 |
| ② | 診断連動の広告配置 | 家計診断カード下＋月次レポートモーダルに文脈連動の提案枠（**控えめ運用**） |
| ③ | アプリの顔づくり | ログイン画面に機能ハイライト3点・設定タブにシェアボタン・サマリーPNGにURL透かし |
| ④ | SNS紹介投稿文 | `docs/sns_launch_posts.md` に Threads/X 用下書き3パターン＋スクショガイド |
| ⑤ | 品質（触る範囲のみ） | version を 1.6.0 へ・LoanView から広告コード分離・新ロジックのテスト追加 |

### やらないこと

- 複数端末同期（設計合意済み・着手目安 2026/08〜10 のまま後回し）
- TypeScript strict 化・巨大ファイル（DashboardView 761行等）の分割 — 次回「品質ファースト」回で実施
- 概要タブへの常設広告枠（「やや積極的」案は不採用。控えめ運用で信頼重視と決定）
- skin/ronin の自動投稿への組み込み（SNS投稿は手動）

## 各項目の設計

### ① アフィリエイト整理

**新ファイル `src/utils/affiliates.ts`**:

- `AffiliateOffer` 型: `{ id, tag, title, desc, cta, href, context }`
  - `context`: `"invest" | "tax" | "loan"` — どの文脈で出してよいかのラベル
- `APPROVED_OFFERS: AffiliateOffer[]` — 承認済み4件（フジトミ証券 / DMM TOSSY / DMM株 / マネーフォワード確定申告）のみ
- 審査待ち5件（プロミスVISA / 三井住友NL / エポス / リクルート / TOKYU）はコメントとして残す。審査通過後に配列へ追加するだけで復活
- バナーUIを `src/components/AffiliateBanner.tsx` として LoanView から切り出し（PRラベル・`rel="sponsored"` は現行踏襲）

**LoanView の変更**: `AFFILIATE` 定数・`AffiliateBanner`・`AffiliateSection` を削除し、新コンポーネントを import。現行の cf/bl/lo タブ別配置は踏襲し、**承認済み4件のみ表示**（プレースホルダー5件のバナーだけが画面から消える）。

### ② 診断連動の広告配置（控えめ運用）

**選定ロジック `selectAffiliateOffer()`（`src/utils/affiliates.ts` 内の純関数）**:

```
入力: { savingRate, hasAccounts, month }（診断済みの値を受け取るだけ）
出力: AffiliateOffer | null
ルール（上から順に判定・最初にマッチした1件のみ返す）:
  1. month が 2 or 3（確定申告期）→ マネーフォワード
  2. savingRate >= 20 かつ hasAccounts → 証券系（DMM株を代表に1件）
  3. どれにも合わなければ null（何も出さない）
```

**表示箇所（1画面1枠まで・必ずPRラベル）**:

- 🩺家計診断カード（`HealthCheckCard`）の直下: `selectAffiliateOffer()` が返した1件を「あなたへの提案」として表示。null なら何も出さない
- 月次レポートモーダル（`MonthlyReportModal`）の最下部: 同じ関数で1件。null なら非表示

### ③ アプリの顔づくり

**【実装前調査での変更】** 初回アクセス時のランディングページ（ヒーロー・機能カード3つ・セキュリティアピール）は `PasswordGate` に**実装済みだった**ため、機能ハイライト追加は不要。代わりに調査で見つかった「バージョン表記が3箇所バラバラ」問題を解消する:

- `package.json` = 1.2.2 / `PasswordGate` フッター = v1.2.2 / `SettingsView` アプリ情報 = v1.5.0 と不一致
- vite の `define` で `__APP_VERSION__` を `package.json` から注入し、2画面とも自動連動にする（今後ずれない）

**設定タブ（`SettingsView`）に「📣 友達に教える」カード**:

- `navigator.share` 対応（スマホ）→ ネイティブシェアシートで `タイトル＋URL` を共有
- 非対応（PC等）→ `navigator.clipboard.writeText` でURLコピー＋トースト「リンクをコピーしました」
- コピー失敗時はエラートースト
- シェア文言: `BYB — 収支を入力するだけ。グラフで家計が一目でわかる無料の家計簿アプリ https://financeweb-nine.vercel.app`

**サマリーPNG透かし（`src/utils/summaryExport.ts`）**: html2canvas で画像化する要素の最下部に `BYB — financeweb-nine.vercel.app` を小さく（12px・薄いグレー）追加。CSV出力は変更しない。

### ④ SNS紹介投稿文（`docs/sns_launch_posts.md`・finance_web リポジトリ内）

- Threads 用2パターン（共感フック型 / 機能訴求型）＋ X 用1パターン（140字制限考慮）
- スクショ撮影ガイド: 概要タブ（グラフが見える状態）・月次サマリー・診断カードの3枚を推奨
- 投稿は手動。skin/ronin の自動投稿 JSON には混ぜない

### ⑤ 品質

- `package.json` の `version` を `1.6.0` に更新
- 新規ロジックのユニットテスト:
  - `selectAffiliateOffer()` — 確定申告期 / 貯蓄率高 / 該当なし の3系統
  - `AffiliateBanner` — レンダーとPRラベルの存在
- 既存テスト126件の回帰確認（`npx vitest run`）

## エラー処理

- シェアの `navigator.share` 拒否（ユーザーキャンセル）→ 何もしない（正常系）
- クリップボード書き込み失敗 → エラートースト表示
- 承認済み広告が0件になっても `selectAffiliateOffer()` は null を返し、各セクションは非表示（クラッシュしない）

## テスト方針

- 新規純関数・コンポーネントにユニットテスト追加
- `npx vitest run` 全件パスを確認後、`npm run build` でビルド確認
- デプロイは `npx vercel --prod`（GitHub経由ではない・CLAUDE.md の罠メモ通り）

## リリース後の確認

- 本番URLでローンタブの広告が承認済みのみになっていること
- 診断カード下の提案枠が条件どおり出ること（データ未入力なら出ない）
- スマホ実機でシェアシートが開くこと
