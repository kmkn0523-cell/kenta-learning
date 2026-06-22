# 複数端末同期 — 設計書 v2（確定版）

最終更新: 2026-06-22
ステータス: **設計確定（実装待ち）**
前提: v1（`finance_web_sync_design.md`）のストレージ選定＝**Vercel KV（案C）** を踏襲。本書はv1で詰め切れていなかった
「鍵・アカウント・復元・課金ID」を確定させたもの。**アカウント方式＝匿名復元キー方式**（2026-06-22決定）。

---

## 0. v1からの変更点（なぜv2が必要か）

v1には製品化を阻む3つの未解決論点があった。本書はこれを解決する。

| # | v1の問題 | v2の解決 |
|---|---|---|
| 1 | 暗号化salt `kk_enc_salt` が**端末ごとにランダム**→同じパスワードでも別端末で復号不可 | 復号鍵を**復元キー(RK)から決定的に導出**。端末非依存にする |
| 2 | 「パスワード忘れ＝全消失」は課金ユーザーに地雷 | **復元キー(RK)** という復旧経路を1本だけ用意（ゼロ知識は維持） |
| 3 | ゼロ知識とStripe課金（顧客特定が必要）が衝突 | accountIdとStripeを**KV上のマッピング**で結ぶ。メールはStripe側だけが持つ |

---

## 1. 中核アイデア：パスワードとは別に「復元キー」を持つ

役割を2つに分離する。

- **パスワード** = この端末でアプリを開くための**ローカルの鍵**（今まで通り。端末ごとに違ってよい）
- **復元キー (Recovery Key / RK)** = 同期・復号・アカウントの**ルート**。高エントロピーな乱数。同期ONのとき1回だけ表示し、ユーザーが保管する

```
復元キー(RK) ──┬─ deriveAccountId(RK)  → サーバ上のデータの置き場所ID（推測不可）
               ├─ deriveDataKey(RK)    → データ暗号化鍵(DEK)。端末非依存＝どの端末でも同じ
               └─ ローカルではRKをパスワード派生鍵で包んで(wrap)保存
```

これで:
- 別端末は **RKさえあれば** accountId と DEK を再現でき、サーバの暗号文を復号できる（論点1解決）
- RK が復旧経路になる（論点2解決）
- accountId は乱数由来で推測不可（v1の `hash(password)` は弱パスワードだと推測リスクがあった→改善）

### パスワードを忘れたら？
- 同じ端末: RKはローカルにwrap保存されているが、パスワードが無いと開けない → **その端末では復旧不可**
- 別の方法: **RKを入力すれば**新しいパスワードで再ロックして復旧できる
- RKもパスワードも両方失ったら: データは復元不可（ゼロ知識の代償。**RK保管をオンボーディングで強く促す**）

---

## 2. 暗号スキーマ（crypto.ts への追加）

既存の `makeNewHash` / `deriveEncryptionKey` / `encryptValue` はそのまま残す。以下を追加する。

```
// 復元キーを生成（32バイト乱数 → base32の "XXXX-XXXX-..." 形式で表示）
generateRecoveryKey(): { raw: Uint8Array, display: string }

// RK から accountId を導出（サーバのKVキー。HKDF/SHA-256, context="byb-account-id"）
deriveAccountId(rk: Uint8Array): string        // 例: 43文字のbase64url

// RK から AES-GCM データ鍵(DEK)を導出（HKDF, context="byb-data-enc"）※端末非依存
deriveDataKey(rk: Uint8Array): Promise<CryptoKey>

// RK をパスワード派生鍵で包んでローカル保存する文字列にする / 戻す
wrapRecoveryKey(rk, password): Promise<string>
unwrapRecoveryKey(wrapped, password): Promise<Uint8Array>
```

- 既存の `kk_enc_salt`（端末ローカル暗号化）は**ローカル専用のまま温存**。同期に乗せるデータだけ DEK で暗号化する二層構成にする
- 同期ペイロード = `encryptValue(DEK, syncState)` の文字列。中身はサーバから見えない（E2E維持）

---

## 3. 同期するデータと競合解決

### 同期対象
`kk_tx / kk_inc / kk_fx / kk_lo / kk_cf / kk_bl / kk_accounts / kk_budget / kk_tpls / kk_transfers / kk_categories / kk_savingGoal / kk_rec_inc / kk_rec_exp`

### 競合解決：レコード単位マージを基本にする（v1の3択全面採用から改善）

家計データの大半は **UUID付きの追記レコード**（取引・収入など）。これらは端末をまたいでも衝突しにくい。

- **配列系（取引・収入・固定費・ローン・振替）**: `id` でユニオンマージ。各レコードに `updatedAt` を追加し、同IDは新しい方を採用。削除は**トゥームストーン**（削除済みIDの記録）で表現
  - 例: 端末Aで食費追加・端末Bで家賃追加 → **両方残る**（プロンプト不要で自動解決）
- **単一値系（budget / categoryConfig / savingGoal）**: 前回同期以降に両端末で変更があった時だけ衝突。そのときのみ v1 の **3択モーダル**（サーバ版/ローカル版/バックアップして採用）を出す

> MVPを軽くするなら **Phase 1 = ブロック全体のversionロック＋3択** で出して、**Phase 2 でレコードマージ**に格上げしてもよい。ただし家計データは「黙って全上書き」で消えると致命的なので、レコードマージを早めに入れることを推奨。

### スキーマ変更
- 各レコードに `updatedAt: string` を追加（既存データは `dataMigration.ts` で初回に現在時刻を補完）
- 削除時はトゥームストーン `kk_tombstones: { id, deletedAt }[]` に積む（一定期間で掃除）

---

## 4. API 仕様（Vercel Route Handlers）

### `GET /api/sync?accountId={id}`
- 課金状態を確認 → 有効なら最新ペイロードを返す
- レスポンス: `{ version: number, data: string, updatedAt: string } | null`

### `PUT /api/sync`
```json
{ "accountId": "…", "version": 5, "data": "DEKで暗号化済みのJSON" }
```
- `version` がサーバと一致 → `version+1` で保存し200
- 不一致 → **409 Conflict** + サーバ最新を返す（クライアントがマージして再PUT）
- **課金が無効なら 402 Payment Required**（同期書き込みは有料機能）

### `POST /api/billing/checkout`
- `{ accountId }` → Stripe Checkout セッションを作成しURLを返す

### `POST /api/billing/confirm`
- `{ accountId, sessionId }` → サーバが Stripe API で session を検証し、KVに
  `billing:{accountId} = { stripeCustomerId, subscriptionId, status, currentPeriodEnd }` を書く
- Stripe Webhook（`/api/billing/webhook`）で更新・解約・支払い失敗を同期

### KVキー設計
```
sync:{accountId}     = { version, data, updatedAt }     # 暗号文
billing:{accountId}  = { stripeCustomerId, status, currentPeriodEnd }
```

---

## 5. 課金とアカウントの紐付け（論点3の解決）

- **我々のサーバはメールを持たない**。identity は匿名の `accountId`（RK由来）
- Stripe Checkout 完了 → `confirm` で `accountId ↔ stripeCustomerId` を KV にマップ
- メール（領収書・支払い催促）は **Stripe 側だけ**が保持 → ゼロ知識を崩さない
- 別端末で **RKで復元すれば accountId は同一** → サブスクもそのまま引き継がれる
- 注意: RKを完全に失うと「データ」も「自分の課金への到達」も失う。解約は Stripe からのメールで可能。**オンボーディングでRK保管を必須級に強調**

### 無料 / 有料の線引き（案）
- 無料: 今まで通りローカル単体（同期なし）。バックアップJSONも継続
- **¥500/月（有料）: 複数端末同期**。`PUT /api/sync` を課金ゲートで保護

---

## 6. 画面・UX 追加

| 画面 | 内容 |
|---|---|
| 設定タブ「☁️ クラウド同期」 | 同期ON/OFF・最終同期日時・「この端末を同期に追加」 |
| 同期有効化フロー | ①RK生成 → ②**RKを1回だけ表示し保存を確認させる**（コピー/スクショ/印刷）→ ③課金 Checkout |
| 別端末で復元 | 「復元キーで復元」→ RK入力 → pull・復号 → この端末用パスワード設定 |
| 競合モーダル | 単一値の衝突時のみ3択（v1のUIを流用） |
| 課金ページ | プラン説明・特定商取引法・プライバシーポリシー・利用規約へのリンク |

---

## 7. 実装ステップ（確定）

| Step | 内容 | 工数 | 依存 |
|---|---|---|---|
| 1 | Vercel KV を Marketplace から追加・env設定 | 0.5h | — |
| 2 | crypto.ts: RK生成 / deriveAccountId / deriveDataKey / wrap・unwrap ＋単体テスト | 1日 | — |
| 3 | レコードに `updatedAt` 追加・トゥームストーン・`dataMigration` 拡張＋テスト | 1日 | — |
| 4 | `/api/sync`（GET/PUT・versionロック・課金ゲート） | 1日 | 1,2 |
| 5 | `useCloudSync` フック（pull→merge→push, 5秒debounce, 30秒poll） | 1.5日 | 3,4 |
| 6 | マージ実装（配列ユニオン＋単一値LWW＋3択フォールバック） | 1日 | 3,5 |
| 7 | 設定UI・RK表示/復元フロー | 1日 | 5 |
| 8 | Stripe: checkout / confirm / webhook ＋課金ゲート | 1.5〜2日 | 4 |
| 9 | 法務ページ（特商法・プライバシー・規約）・パンくず | 0.5日 | — |
| 10 | E2Eで2端末シナリオ検証（追加/編集/削除/競合/復元/解約） | 1日 | 全部 |

合計: **同期コア 約5.5日 ＋ 課金・法務 約3日 ＝ 8〜9日**

---

## 8. リスクと対策

| リスク | 対策 |
|---|---|
| RK紛失で全消失 | オンボーディングで保管必須化・バックアップJSONも併用・「RK未保存だと復元不可」を赤字警告 |
| 黙ってデータ全上書き | レコードマージで自動保全。単一値だけ3択。pull前に必ずローカルへ自動バックアップ |
| 弱いaccountId推測 | accountIdはRK（256bit乱数）由来で推測不可。レート制限もかける |
| Stripe Webhook 取りこぼし | confirm時のポーリング＋Webhookの二重化。currentPeriodEndで猶予判定 |
| 無料↔有料の移行で同期切れ | 解約後は読み取り専用pullをN日許可してから停止（データ取り出しの猶予） |
| オフライン編集 | ローカルが常に真実の単一ソース。オンライン復帰時に push/merge |

---

## 9. 着手判断チェックリスト（v1から継続）

- [ ] finance_web 月間アクティブ >= 10人
- [ ] パスワードリセット機能が安定稼働
- [ ] Stripe の知見（別プロジェクトで素振り）
- [ ] バックアップJSON利用ログで「同期したい」需要を観測

---

## 10. 関連
- 旧設計: `finance_web_sync_design.md`（ストレージ選定・コスト試算・マネタイズ試算はこちらが有効）
- 暗号: `src/utils/crypto.ts` / 永続化: `src/hooks/usePersist.ts` / バックアップ: `src/hooks/useBackup.ts`
- マネタイズ目標: 100人で月¥50,000（半年ロードマップと整合）
