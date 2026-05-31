# @RoninWords Threads コンテンツ診断レポート

作成日: 2026-05-31
対象: `threads_posts.json`（200日分 / 本文400本）、`ronin_threads_progress.json`

---

## 0. 結論

**ネタ切れではない。** 在庫は約60%残っている（残り約119日分=238本）。
問題があるとすれば在庫量ではなく「夜投稿の問いかけテンプレの型化」と「全投稿が同一構造」というマンネリの芽。

---

## 1. 在庫状況

| 指標 | 数値 |
|---|---|
| ネタ総数 | 200日分（1日分=朝+夜の2本）= 本文400本 |
| 現在の消費位置 | index: 81 / 200（約40%消費・残り約60%） |
| 残り在庫 | 約119日分 = 約238本が未投稿 |
| 実投稿回数（history） | 681回 |
| 本文の長さ | 平均275字 / 最短52字 / 最長553字 |

`index: 81` =「200日分のうち81日目まで使った」。残り119日分が手つかず。

---

## 2. テーマの偏り

ハッシュタグ分布（=テーマ）:

```
#Bushido        27   ← 突出
#JapaneseWisdom 17
#Zen            16
#Strategy       14
#Resilience     14
#Mastery / #Presence / #Courage / #Patience / #Humility ...
```

頻出語:

```
today 74 / person 66 / samurai 57 / moment 50 / path 39 / bushido 35
```

所見: 武士道・禅・戦略の3本柱に集中。世界観は一貫していて強み。
ただし samurai / bushido / path / warrior への依存が高く、メタファーが擦り切れ始める手前。

---

## 3. マンネリ判定（類似ペア検出）

400本を総当たりで文章類似度を計算:

- 類似度0.6以上: 6ペアのみ
- 類似度0.55以上: 18ペア

→ 重複率は低く健全。ただし明確なクセが1つ。

### 3-1. 夜投稿の「問いかけ型」が型化

類似ペアの大半が evening（夜）投稿の締めの問いかけに集中:

```
day122e「What trained you today?」      ↔  day152e「What path did you begin making today?」
day160e「What did you continue today?」  ↔  day171e「What did you build today?」
day114e「Where did you resist today?」   ↔  day198e「How many words did you use today?」
day128e「What did you delay today?」
```

`What did you ___ today?` という振り返り質問のテンプレが夜投稿の定番化。

### 3-2. 完全重複が1組

```
day18-evening と day43-evening
→ どちらも「Discipline gets you started.」で始まる同一フック
```

意図的な再利用でなければ重複の取りこぼし。

---

## 4. 文章構造の固定化

ほぼ全投稿が同じ鋳型:

```
① 英語のフック（短く強い断定 or 問い）
② 日本語概念（漢字 → ローマ字 → 英訳の3点セット）
③ 具体例・展開
④ 問いかけ or 締めの一言
⑤ ハッシュタグ
```

完成度は高いが、400本すべてがこの型だと熱心なフォロワーほどフォーマットを覚えてしまう。
マンネリの正体は内容より構造の単調さ。

---

## 5. 改善提案（優先度順）

1. 夜投稿の問いかけテンプレを2〜3パターンに分散
   `What did you ___ today?` 一辺倒をやめ、「断定で締める」「行動を1つ指定する」「あえて問わず余韻で終わる」型を混ぜる。

2. 完全重複（day18e / day43e）を解消
   どちらかを別フックに差し替え。※`threads_posts.json` の編集は要承認＋編集後 `/validate-threads-posts` 必須。

3. 比喩のレパートリーを samurai/path 以外へ拡張
   職人（刀鍛冶）・茶道・自然（稲穂・雨）系を増やし、武士比喩の濃度を下げる。

4. 構造のバリエーション枠を1割ほど用意
   「日本語概念なしの短い1文だけ」「問いだけ」など型を崩した投稿を意図的に混ぜる。

5. 残り在庫（119日分）を作るときに上記を反映
   今ある400本は触らず、これから足すネタで多様性を上げるのが安全。

---

## 6. 分析メソッド（再現用メモ）

- 本文抽出: 各エントリの `morning` / `evening` キー（計400本）
- 頻度集計: 英単語 `[A-Za-z]{4,}`、漢語 `[一-龯]{2,}`、ハッシュタグ `#\w+`
- 類似度: `difflib.SequenceMatcher`（ハッシュタグ除去後の本文で総当たり）
- 在庫判定: `ronin_threads_progress.json` の `index` を 200 と比較

---

## 7. 夜投稿テンプレ分散の書き換え案（改善提案1の具体化）

### 7-1. 現状

夜投稿200本のうち多数が `What/Where/How did you ___ today?` という
「1日の振り返り質問」で締めている（型化）。質問自体は良い手法だが、
同じ構文の連発で読者がパターンを覚えてしまう。

### 7-2. 締めを4パターンに分散する

| 型 | 役割 | 配分の目安 |
|---|---|---|
| A. 問いかけ型（既存） | 読者に内省させる | 40% |
| B. 断定で締める型 | 余韻と説得力 | 20% |
| C. 行動指定の命令型 | 明日の具体行動を1つ渡す | 20% |
| D. 余韻型（問わず終わる） | 詩的に幕を引く | 20% |

### 7-3. before → after 書き換え例

元ネタは既存の夜投稿の締め（本文は触らず締めの2〜3行だけ差し替える想定）。

**例1（day122 evening の締め）**

before（A・問いかけ型）:
```
What did you forge today?
What will you refine for the next 10,000?
```

after-C（行動指定の命令型）:
```
Name one skill you forged today.
Tomorrow, refine it once. That is the 10,000-day path.
```

after-D（余韻型）:
```
Forging ends in a day.
Refining never ends.
The 10,000 days are already counting.
```

**例2（day1 evening の締め）**

before（A・問いかけ型）:
```
What did you avoid today?
That was your training.
```

after-B（断定で締める型）:
```
The thing you avoided today was the training.
Everything else was rehearsal.
```

**例3（day14 evening ― すでに良い形）**

```
What stands between you and starting? Name it.
Then step over it. The obstacle is usually imagined.
```
→ 問いかけ＋命令が混ざった理想形。これを他の回でも真似る。

### 7-4. 運用ルール（残り在庫 day82以降に適用）

1. 既存400本（day1〜）は触らない。重複1組（day18e / day43e）の解消だけ別途。
2. 新規ネタを作るとき、夜の締めを上の A:B:C:D = 4:2:2:2 で割り当てる。
3. 連続する数日で同じ型が3回続かないようにする（朝→夜の流れも含めて確認）。

### 7-5. 反映時の注意

`threads_posts.json` の編集は要承認。編集後は必ず:
```
/validate-threads-posts
```
で重複チェックを通すこと（Threads投稿の重複はNG）。
