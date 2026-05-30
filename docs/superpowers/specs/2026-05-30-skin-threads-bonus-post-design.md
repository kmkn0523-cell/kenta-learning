# skin Threads バズ追撃ボーナス投稿 設計書

- 作成日: 2026-05-30
- 対象: skin アカウント Threads 自動投稿
- 方針: 案A「クリーン加速」＋ Phase 0（反応データ収集バグ修正）を先行

---

## 1. 目的

skin Threads は現在1日4回の定時投稿（JST 7:30 / 12:30 / 18:30 / 21:30）。
反応が良かった翌日に「ボーナス投稿」を1本だけ追加し、伸びているときに畳み掛けて露出とフォロワー増を狙う。

制約（絶対に守る）:

- 進行中のA/Bテーマ検証（〜2026-06-06）を一切汚さない
- 通常4枠の投稿には手を加えない
- 1日に増やすのは最大 +1本。最低本数は4本を維持
- 乱発しない（反応が本当に良かった日だけ撃つ）

---

## 2. 全体構成（2フェーズ）

`Phase 0` → `Phase 1` の順。Phase 0 を先に直さないと、ボーナスのトリガーに使う反応データが埋まらない。

### Phase 0: 反応データ収集バグの修正（前提）

現状 `skin/skin_data_collector.py` が反応データを集められておらず、`skin/skin_analytics.json` の `posts_history` が 2026-05-17 で止まっている。原因は2つ。

1. `identify_day_and_type` が存在しない `threads` キーを走査している
   - 現在の投稿JSONは `threads_a` / `threads_b` 構造。`threads` キーが無いため全件スキップされ、履歴が凍結している
   - 修正: `threads_a` と `threads_b` の両方を走査する
2. `fetch_threads_data` が取得件数を絞らず、デフォルトの最近25件しか取れない
   - 過去12日（約50件）に届かない
   - 修正: API リクエストの `params` に `"limit": 100` を追加する
   - `limit` の上限は実装時に context7 で Threads API 仕様を確認する

修正後の埋め戻し:

- `skin_analytics_daily.yml` を `workflow_dispatch` で1回手動実行する
- `post_id` で重複排除しつつ過去分（5/18〜5/29）を埋める
- ページネーションは作らない（YAGNI。`limit: 100` で当面足りる）

Phase 0 完了の確認:

- `posts_history` が 5/29 まで埋まっていること
- `last_updated` だけでなく実データが増えていること

---

## 3. Phase 1: ボーナス投稿本体

### 3-1. トリガー設計（どの日を「バズった」と判定するか）

判定は**3条件のAND**。すべて満たしたときだけ発火する。
判定対象は **JST前日に投稿したもの**（1本でも跳ねたら追撃＝畳み掛け）。

| 条件 | 内容 | 役割 |
|------|------|------|
| 1 | `views >= 15` | 足切り（絶対）。低viewでengagement_rateが暴れるのを排除 |
| 2 | `likes >= 2` | 足切り（絶対）。今の自己ベスト級 |
| 3 | `engagement_rate >= 直近14日平均 × 1.5` | 主軸（相対）。自己ベスト比で「いつもより跳ねた」を見る |

判定ロジック（純関数）:

```text
should_fire_bonus(posts_history, today) -> bool
  1. JST前日の投稿を posts_history から抽出（posted_at の UTC を JST に変換して日付一致）
  2. 前日の投稿が無ければ False
  3. 直近14日の全投稿から engagement_rate の平均を出す（views=0・rate=0 のレコードも母集団に含める）
  4. 前日の投稿のうち、3条件すべてを満たすものが1本でもあれば True（any 判定）
  5. それ以外は False（安全側 = 撃たない）
```

過去12日での検証結果（後期＝運用中データ）:

- `5/15` のみ発火（day45 views19/likes2/rate10.53、day46 views36-42/likes2/rate4.76-5.56）
- `5/16`・`5/17` は likes1 で足切り脱落
- `5/14` は views11 で脱落
- → 月1〜2回ペース。乱発しない

### 3-2. 本数刻み

- 増やすのは **+1本のみ**（上限 +1）
- 最低4本は常に維持（通常枠は不変なので自動的に保証される）
- ボーナスは「撃つ／撃たない」の二択。本数を2本以上増やしたり減らしたりはしない（将来の案Bで検討）

### 3-3. ボーナス弾の調達（専用プール新設）

- ボーナス専用のテーマを別ファイル `skin/skin_threads_bonus_posts.json` に数本用意する
- 通常投稿（`skin_threads_posts.json` の `threads_a` / `threads_b`）とは**絶対に被らない**ので、投稿重複の心配がない
- 弾が尽きたら、発火条件を満たしていても撃たずにスキップ（安全側）。Kenta が弾を補充する運用
- 弾の選択は専用カウンタ `bonus_index` で順番に1本

> 補充ルール: 編集後は `/validate-threads-posts` を通す（重複NGの担保）。

### 3-4. A/B非干渉の担保（最重要）

ボーナス投稿は専用エントリポイント `--bonus` で起動し、通常の `main()` 経路には一切入らない。

触らないもの:

- `daily_index`
- `ab_index_per_theme`
- `ab_results`
- `flip_ab_variant`（呼ばない）
- **`last_posted_at`（読まない・書かない）**

最後の `last_posted_at` が最重要。これを更新すると通常の `21:30` 枠が
`check_should_skip(skip_minutes=90)` で「直前に投稿済み」と誤判定してスキップし、
A/B検証に穴が空く。完全独立にすることで、進行中のA/B検証（〜6/6）は元のまま動く。

ボーナスが更新するのは専用キーだけ:

- `bonus_index`（次に使う弾の番号）
- `last_bonus_date`（最後にボーナスを撃った日付）

### 3-5. 発火の仕組み（新ワークフロー）

新しいワークフロー `skin_threads_bonus.yml` を1本追加する。

- cron で1日1回。JST `20:00` 頃に起動
  - 通常4枠（7:30 / 12:30 / 18:30 / 21:30）の隙間。前後の `18:30`・`21:30` から90分ずつ空く位置
- 起動したら判定スクリプトが `posts_history` を読み、3条件をチェック
  - 満たす → `skin_threads_action.py --bonus` で1本投稿
  - 満たさない → 何もせず終了
- concurrency group は専用（`skin-threads-bonus`）。投稿系・分析系と競合させない
- `workflow_dispatch` も付ける（手動テスト用）

データ更新タイミングとの整合:

- `skin_analytics_daily.yml` は JST 15:00 にデータ更新
- ボーナスは JST 20:00 起動なので、当日15:00時点の最新データ（前日分を含む）を見られる
- 前日深夜の投稿は views が伸び切らずボーナス判定で取りこぼす可能性があるが、安全側（撃たない方向）なので許容

### 3-6. 二重投稿防止

- ボーナスは **1日1本まで**。`last_bonus_date` が今日の日付なら、条件を満たしていても撃たずに終了
- これは通常の `check_should_skip` とは**別系統**の独自スキップ判定
- ワークフロー側の concurrency group（`skin-threads-bonus`）でも二重起動を防ぐ

### 3-7. テスト

- 判定ロジックを純関数 `should_fire_bonus(posts_history, today) -> bool` に切り出す
- `skin/tests/` に pytest を追加（投稿APIは叩かず、判定ロジックだけ検証）

| ケース | 期待 |
|--------|------|
| `5/15` 相当データ（views19/likes2/rate10.53） | True |
| likes1 の日 | False |
| views不足（15未満）の日 | False |
| 相対閾値未達の日 | False |
| `posts_history` が空 | False（安全側） |

---

## 4. 調整可能な定数（ファイル先頭に置く）

| 定数 | 初期値 | 意味 |
|------|--------|------|
| `BONUS_MIN_VIEWS` | `15` | views 足切り |
| `BONUS_MIN_LIKES` | `2` | likes 足切り |
| `BONUS_LOOKBACK_DAYS` | `14` | 相対平均を取る期間（日） |
| `BONUS_RATE_MULTIPLIER` | `1.5` | 相対閾値の倍率 |
| `BONUS_MAX_PER_DAY` | `1` | 1日に撃つ上限本数（= +1本） |

A/B検証が終わる 6/6 以降、反応が育ってきたら `BONUS_MIN_LIKES` を引き上げて基準を厳しくできる。

---

## 5. スコープ外（YAGNI / 将来）

今回は作らない:

- ページネーション（`limit: 100` で当面足りる）
- 本数を2本以上増やす／減らす方向の調整
- 通常4枠の時刻変更
- ボーナス弾の自動生成

将来の発展余地:

- 案B（複数信号での増減）へ育てる
- `BONUS_MIN_LIKES` などの基準引き上げ

---

## 6. 触るファイル一覧

| ファイル | 操作 | フェーズ |
|----------|------|----------|
| `skin/skin_data_collector.py` | 修正（`threads` キー走査 → `threads_a`+`threads_b`、`limit: 100` 追加） | Phase 0 |
| `skin/skin_analytics.json` | 手動実行で埋め戻し（直接編集はしない） | Phase 0 |
| `skin/skin_threads_action.py` | `--bonus` エントリポイント・判定関数・ボーナス投稿処理を追加 | Phase 1 |
| `skin/skin_threads_bonus_posts.json` | 新規（ボーナス専用の弾プール） | Phase 1 |
| `skin/skin_threads_progress.json` | 新キー `bonus_index`・`last_bonus_date` を追加 | Phase 1 |
| `.github/workflows/skin_threads_bonus.yml` | 新規（発火ワークフロー） | Phase 1 |
| `skin/tests/` | 判定ロジックの pytest を追加 | Phase 1 |

既存の `threads_post.yml`（通常4枠）と `skin_analytics_daily.yml` の挙動には手を加えない。
