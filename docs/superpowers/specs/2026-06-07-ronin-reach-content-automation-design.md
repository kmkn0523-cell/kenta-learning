# @RoninWords reach加速：コンテンツ強化＋自動化 設計書

作成日: 2026-06-07
対象アカウント: @RoninWords（書道カード・武士道/禅/戦略を英語で欧米男性に届ける）
前提合意: 2026-06-06 メモ `project-ronin-monetize-reach`（reach最優先・自動化最優先・月$100目標）

---

## 0. 結論（この設計が解くこと）

Threadsで非フォロワーに広がる条件は「投稿直後のリプライ」。現状はいいね0.9・閲覧35・コメント0.1・シェア0でここが死んでいる。
全施策を **「リプライを生む」一点** に集約する。既存400本（`threads_posts.json`）は触らず、新規追加と仕組み側で強化する。

直す3つ:
1. コメント誘発が弱い → 新カテゴリ「engagement post」を生成
2. ハッシュタグ固定5個 → 動的ローテーション（越境タグで新規流入）
3. 5/07の最適化エンジンが完全停止 → 「今のデータで実際に効く動作」をする版に作り直し

---

## 1. 現状診断（コード実測 2026-06-07）

- 在庫: 200日分 × 朝夜 = 400本。消費 `index 164/400`（約41%）。ネタ切れではない。
- **最適化エンジンが停止**: `ronin/ronin_optimization_index.json` が `analysis_phase: "learning" / days_accumulated: 0 / next_post_queue: []`。
  `ronin_threads_action.py` の `should_use_optimization()` は `analysis_phase == "optimizing"` のときだけ最適化に入る設計 → **一度も発動せず、毎回ただの順番ローテーション**。
- **ハッシュタグ固定**: 全投稿に `#JapaneseWisdom #Bushido #Zen #Samurai #Wisdom` を付与（`ronin_threads_action.py` の `HASHTAGS` 定数）。
- CTA: Gumroad/Substackを14投稿に1回交互に**本文末尾**へ挿入（`cycle == 0` / `cycle == 7`）。
- 配信時刻: ET最適化済（`ronin_threads_post.yml` cron= UTC 12/16:30/22/0 = ET 8:00/12:30/18:00/20:00）。効果は今後のデータ待ち。
- コンテンツ構造: 監査 `ronin/content_audit_2026-05.md` の通り全本同一構造・夜は「What did you ___ today?」型化・完全重複1組（day18e/day43e）。

---

## 2. 確定した設計判断

| 項目 | 決定 |
|---|---|
| 既存400本(`threads_posts.json`) | 触らない（重複1組の修正のみ・別途承認） |
| マネタイズCTAリンク | 本文から外し、自動first-commentへ移す（本文クリーン化で配信抑制を回避） |
| 初回engagement投稿の本数 | 30本（約1〜1.5ヶ月分の差し込み在庫・後で増減可） |
| データ駆動の型別ランキング | 今はやらない（ゼロ反応＝学習不能。反応が有意になってから後付け＝YAGNI） |
| 配信スケジュール | 変更なし（昨日ET最適化済） |

---

## 3. コンポーネント設計

### 3-1. engagement post 新カテゴリ（コンテンツ強化の中核）

ロニンの世界観を保ったまま、ワンタップで返信したくなる短文を量産する。

6型をローテーション:

```
二者択一:  Train for a war that never comes — wise or wasteful? 🅰 / 🅱
穴埋め:    The hardest discipline is ___. Finish it.
1つ挙げる:  Name one thing you quit this year that made you stronger.
賛否:      Loyalty is overrated. Skill is the only honor. Agree?
順位づけ:  Courage, patience, humility — which is hardest for you right now?
告白:      The discipline you keep failing at. No judgment — drop it below.
```

- 保存先: 新ファイル `ronin/ronin_engagement_posts.json`（`threads_posts.json` と分離 → 安全）
- 各エントリ構造（案）:
  ```json
  {
    "id": "eng001",
    "archetype": "either_or",
    "text": "...",
    "seed_comment": "...",
    "theme": "discipline"
  }
  ```
- 生成方法: Workflowで「生成 → 別エージェントが世界観/品質を対抗レビュー → 重複チェック」を通過した分だけ採用。テンプレ直書きはしない（ロボット臭防止）。
- 監査反映: 締めの4型分散（A問いかけ / B断定 / C行動命令 / D余韻 = 4:2:2:2）、比喩を刀鍛冶・茶道・自然へ拡張。**この新規分にのみ反映**（既存は触らない）。
- 品質基準: 英文として自然・500字以内・ロニンの声（武士道/禅/戦略）・既存および新規内で重複なし・返信を1アクションで促す締め。

### 3-2. 動的ハッシュタグ・ローテーション

固定5個をやめ、4セットを投稿ごとに回す。ターゲット（欧米の自己鍛錬・ストイック層）が既にいるタグへ越境する。

```
A 王道:    #JapaneseWisdom #Bushido #Zen
B 越境:    #StoicMindset #SelfDiscipline #Mindset
C 行動:    #Discipline #Resilience #Focus
D ブランド: #Samurai #Kanji #RoninWords
```

- 新モジュール `ronin/ronin_hashtags.py`（純粋関数）。
- API: `pick_hashtag_set(index_or_count) -> str`。投稿カウントで `A→B→C→D→A...` を回す。
- 1投稿あたりタグ3個前後に抑える（過剰タグはスパム判定リスク）。

### 3-3. first-comment 自動シーディング（最大の新武器）

投稿公開**直後に自分の投稿へ返信を1本**自動投稿する（Threads API `reply_to_id`）。早期リプライで「会話が起きている」とアルゴリズムに認識させ拡散を狙う。

- 新モジュール `ronin/ronin_comment_seeder.py`。
- 返信文: 投稿の型に合わせた問いかけ（engagement postは `seed_comment` を使用、教えの投稿は汎用問い）。
- CTAサイクル時のみ、返信末尾に Gumroad/Substack リンクを載せる（本文には載せない）。
- Threads API手順: `POST /{user-id}/threads`（`media_type=TEXT`, `reply_to_id=<親のmedia_id>`, `text=...`）→ 30秒待機 → `POST /{user-id}/threads_publish`。
- **実装の最初に**「自分の投稿へ1本返信できるか」をテスト投稿で確認してから本線に組み込む（API挙動の不確実性をつぶす）。
- 失敗時: 本投稿は成功扱いのまま、返信失敗をログに残しスキップ（本投稿を巻き戻さない）。

### 3-4. 最適化エンジンを「実際に動く版」へ作り直し

- 停止している複雑な最適化ゲート（`should_use_optimization` 経由の `post_optimized`）は、**ゼロ反応データでは無意味**なので本線から外す（コードは即削除せず、後で復活できるよう温存 or 明示コメント化）。
- ポスターは毎回 3-2（タグローテ）・3-1/3-3（engagement注入＋first-comment）を確実に実行する形へ。これが「動く版」の実体。
- `ronin/ronin_analyzer.py` の「現在: 0日」バグを修正し、**データ収集とダッシュボード表示を正常化**（反応が貯まるまで蓄積に徹する）。
  - 原因調査ポイント: `posts_history[0]["posted_at"]` の値と並び順（末尾が最新か先頭が最新か）。`should_analyze()` の日数計算が0に張り付く理由を特定して直す。
- 反応が有意になった段階で「型別ランキングで投稿選択」を後付けする（今回はやらない）。

### 3-5. 完全重複の修正

`day18-evening` と `day43-evening`（どちらも "Discipline gets you started." 始まり）の片方を別フックへ差し替え。
- `threads_posts.json` を編集するため **ユーザー承認 ＋ 編集後 `/validate-threads-posts`** を必須とする。

---

## 4. 自動化の全体フロー（改造後 `ronin_threads_action.py`）

```
1. 90分スキップ判定（既存）
2. 投稿種別を決定: 「教えの投稿(既存400)」か「engagement投稿(新規)」か
   → 4投稿に1回はengagement投稿を差し込む（history件数 % 4 == 3 で判定）。残り3回は教えの投稿。
3. 本文を組む: ハッシュタグはローテーション・外部リンクは入れない
4. 本投稿を公開（画像は教えの投稿のみ既存通り添付）
5. 直後に first-comment を自動返信（型に合った問い＋CTAサイクルならリンク）
6. 進捗・分析データ記録（既存 progress / analytics）
```

---

## 5. モジュール分割・責務・テスト

| ファイル | 役割 | 依存 | テスト |
|---|---|---|---|
| `ronin/ronin_hashtags.py` | タグセット選択（純粋関数） | なし | pytest |
| `ronin/ronin_engagement_posts.json` | コメント誘発の新在庫 | — | validator（重複/字数/必須キー） |
| `ronin/ronin_comment_seeder.py` | 1コメ目の文生成＋返信投稿 | requests | pytest（API部はモック） |
| content generator（Workflow） | 新在庫＋多様化本文の生成・品質ゲート | — | レビューで担保 |
| `ronin/ronin_threads_action.py`（改造） | 全体オーケストレーション | 上記 | pytest（dry-run） |
| `ronin/ronin_analyzer.py`（修正） | 0日バグ修正・分析正常化 | — | pytest |

設計原則: 各モジュールは単一責務・純粋関数はI/Oから分離してテスト可能に。`ronin_threads_action.py` には `--dry-run` を用意し、API送信せず組み立て結果を出力できるようにする。

---

## 6. エラーハンドリング方針

- first-comment失敗 → 本投稿は成功のまま、ログ記録してスキップ（巻き戻さない）。
- engagement在庫切れ → 教えの投稿へフォールバック。
- ハッシュタグ/型選択は例外を投げず安全なデフォルトへ。
- 既存のリトライ（コンテナ作成2回・公開3回・90分重複防止）は維持。

---

## 7. 触る本番資産とリスク

| 資産 | 操作 | 安全策 |
|---|---|---|
| `ronin_threads_action.py`（稼働ポスター） | 改造 | dry-runで先に検証・pytest |
| `threads_posts.json` | 1組のみ編集（3-5） | 要承認＋`/validate-threads-posts` |
| `ronin_engagement_posts.json` ほか新モジュール | 新規 | 単体で完結・既存に影響なし |
| `ronin_threads_post.yml` | 変更なし | スケジュールは現状維持 |

**使用量**: 3-1の本文生成＋品質レビューをWorkflowで回すためセッションのプラン使用量をそこそこ消費する。本数（初回30本）で見積もり、20%を超えそうなら都度確認する。

---

## 8. 成功の見方（着手後の観測指標）

- 短期(1〜2週): engagement投稿のコメント数・1コメ目以降の自然リプライ有無。
- 中期(3〜4週): 平均閲覧35→2倍、コメント0.1→1以上、非フォロワー流入（ハッシュタグ/おすすめ経由）の発生。
- 連動: 反応が貯まったら 3-4 の型別ランキングを後付けする判断材料にする。

---

## 9. スコープ外（今回やらない）

- 既存400本のリライト（重複1組を除く）。
- データ駆動の型別投稿選択（反応が有意になってから）。
- 手動リプライ運用・手動DM（自動化最優先の方針のため後回し）。
- X / LinkedIn / Instagram 側の同等改修（ronin Threads に集中）。
