# skin Instagram カルーセル 30テーマ クラスター再設計 実装計画書

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** skin Instagram の 30 テーマを 5 クラスター × 6 本の診断チェック型カルーセルに再設計し、Batch 1 のリライト含め 2026-07-12 までに全 8 バッチを順次リリースする。

**Architecture:** スライド 8 枚構造を維持しつつ、point スライドを「事実 → 影響 → 打ち手」3 段構造の check スライドに刷新。スコア判定スライドを CTA 直前に追加し、保存率を引き上げる。CTA はクラスター内 6 本の固定サイクルでローテーション。テーマ毎の中身は `carousel_content.json` に集約し、画像描画は `skin_instagram_image_gen_v4.py` を v2.1 対応に拡張。

**Tech Stack:** Python 3 + Pillow (画像生成) / JSON (テーマ定義) / GitHub Actions (自動投稿) / bash (バッチ運用)

---

## セッション再開ガイド (中断後はここから読む)

セッションがリミットで切れた次回は、以下の手順で迷わず再開できる:

1. このファイル全体を Read で開く
2. ファイル先頭から `- [ ]`（未完了）と `- [x]`（完了）を grep で確認
3. 直前に `[x]` が並んでいるブロックの次の `- [ ]` から作業を再開
4. 各タスクには **完了基準** が付いている。曖昧な場合はその基準を再チェックしてから次へ進む
5. 進行中のブランチ名は `skin-instagram-cluster-redesign`。`git status` と `git branch --show-current` で現状を確認

```bash
git branch --show-current
grep -nE '^\- \[(x| )\]' docs/superpowers/plans/2026-05-22-skin-instagram-cluster-redesign-plan.md | head -50
```

---

## 全体ファイル構成

| ファイル | 操作 | 役割 |
|---|---|---|
| `skin/carousel_content.json` | 大規模 modify | テーマ 1–20 リライト + 21–30 追加 |
| `skin/skin_instagram_batch_progress.json` | 構造変更 modify | 5 → 8 バッチに拡張 (例外的に手動編集) |
| `skin/skin_instagram_image_gen_v4.py` | modify | check スライドとスコア判定スライドの描画追加 |
| `docs/skin_instagram_batch_workflow.md` | modify | 新 CTA ローテルール (クラスター内 6 本サイクル) 追記 |
| `skin/skin_instagram_carousels/` | 出力 | 8 × 30 = 240 枚の PNG が最終的に置かれる |

---

## Phase 0: 準備とブランチ作成

### Task 0.1: 現状把握と作業ブランチ作成

**Files:** なし (git 操作のみ)

- [ ] **Step 1: main を最新化してブランチを切る**

```bash
git checkout main
git pull origin main
git checkout -b skin-instagram-cluster-redesign
git tag skin-instagram-cluster-redesign-before main
git push origin skin-instagram-cluster-redesign-before
```

完了基準: `git branch --show-current` が `skin-instagram-cluster-redesign` を返す。タグ `skin-instagram-cluster-redesign-before` が origin に push 済み。

- [ ] **Step 2: 現状の v2 テーマ数と progress.json の状態を確認**

```bash
python3 -c "import json; d=json.load(open('skin/carousel_content.json')); print('v2 themes:', sum(1 for t in d['themes'] if t.get('version')=='v2'))"
python3 -c "import json; d=json.load(open('skin/skin_instagram_batch_progress.json')); print('batches:', d['total_batches'], 'current:', d['current_batch'])"
```

完了基準: 出力に `v2 themes: 4`（theme01-04）と `batches: 5 current: 1` または `current: 2` が見える。

---

## Phase 1: 基盤実装 (v2.1 対応)

### Task 1.1: carousel_content.json のスキーマ拡張

**Files:**
- Modify: `skin/carousel_content.json`

スライドタイプとして `check`（新規）と `score`（新規）を許容する。`point` タイプは Batch 1 のリライトで全て `check` に置き換わるが、後方互換のためコード側では残しておく (画像生成側は両方サポート)。

- [ ] **Step 1: スキーマ拡張の必要性をコメントで明文化**

`carousel_content.json` の先頭にあるテーマ群に v2.1 仕様を追加する。**ファイル自体には JSON しか書けないため、メモは設計書を正とし、コードのスキーマは Task 1.2-1.3 で実装する。** よってこの Step では、新フォーマットの参照用 JSON サンプルを設計メモとして `docs/skin_instagram_v2_1_sample.json` に書き出す。

```json
{
  "id": 99,
  "version": "v2.1",
  "slide_count": 8,
  "cluster": "cluster1_food",
  "hook_type": "number",
  "cta_type": "save",
  "hook": "肌を荒らす食卓 5 チェック",
  "fixed_hashtags": ["肌荒れ", "大人ニキビ", "肌改善"],
  "theme_hashtags": ["食事と肌", "血糖値", "腸活", "食改善", "糖質", "ニキビ食事"],
  "size_mix_hashtags": ["30代肌悩み", "20代ニキビ", "肌トラブル"],
  "slides": [
    {"type": "cover", "cluster_tag": "食卓と肌の関係", "title": "肌を荒らす食卓\n5 チェック", "subtitle": "あなたはいくつ当てはまる？"},
    {"type": "hook", "body": "肌荒れの原因はスキンケアではなく、毎日の食卓にあるかもしれません。", "bullets": ["朝食の落とし穴", "間食の選び方", "夜の炭水化物"]},
    {"type": "check", "item": "朝に菓子パンを食べている", "fact": "精製糖は血糖値を急上昇させる", "impact": "インスリン急増 → 皮脂分泌が増える", "action": "今夜から朝はゆで卵+果物に置換"},
    {"type": "check", "item": "ジュースで水分補給している", "fact": "果糖は中性脂肪に変わりやすい", "impact": "炎症体質 → ニキビが悪化", "action": "炭酸水+レモンに切り替え"},
    {"type": "check", "item": "夜にラーメンを食べる", "fact": "高 GI 食品 + 油の連打", "impact": "夜間血糖値スパイク → 翌朝の肌くすみ", "action": "夜は雑穀ご飯+味噌汁にする"},
    {"type": "check", "item": "牛乳を毎日飲んでいる", "fact": "乳糖と乳製品ホルモンが皮脂を刺激", "impact": "皮脂量増加 → 毛穴詰まり", "action": "2 週間だけ豆乳に切り替えて様子見"},
    {"type": "check", "item": "サラダ油で炒め物をする", "fact": "オメガ 6 過多は炎症を促す", "impact": "肌の赤み・かゆみが増える", "action": "オリーブ油・米油に置換"},
    {"type": "cta", "score_levels": [{"count": "0", "label": "優等生", "comment": "今の食卓を続けて OK"}, {"count": "1-2", "label": "黄信号", "comment": "1 つから直そう"}, {"count": "3+", "label": "赤信号", "comment": "食卓の見直しを優先"}], "cta_text": "保存して食卓を見直そう", "cta_sub": "@skin_reset_jp で続きをチェック"}
  ],
  "caption": ""
}
```

```bash
cat > docs/skin_instagram_v2_1_sample.json <<'EOF'
（上の JSON 全文）
EOF
```

完了基準: `docs/skin_instagram_v2_1_sample.json` が存在し、`python3 -c "import json; json.load(open('docs/skin_instagram_v2_1_sample.json'))"` がエラーを返さない。

- [ ] **Step 2: コミット**

```bash
git add docs/skin_instagram_v2_1_sample.json
git commit -m "docs: v2.1 サンプル JSON を仕様メモとして追加"
```

完了基準: `git log -1 --oneline` で本コミットが先頭に立つ。

---

### Task 1.2: skin_instagram_image_gen_v4.py に check スライド描画を追加

**Files:**
- Modify: `skin/skin_instagram_image_gen_v4.py`

- [ ] **Step 1: `draw_check()` 関数を追加（point とは別関数で並存）**

`draw_point` の直後に以下を追加する:

```python
def draw_check(slide, colors, output_path, check_number):
    """スライド3〜7: 診断チェック項目（事実→影響→打ち手の3段構造）"""
    dark, accent, pale = colors
    img  = Image.new("RGB", (W, H), (250, 249, 246))
    draw = ImageDraw.Draw(img)

    badge_size = 90
    badge_x    = PAD_X
    badge_y    = PAD_Y
    draw.ellipse([badge_x, badge_y, badge_x + badge_size, badge_y + badge_size], fill=accent)
    font_num = ImageFont.truetype(FONT_JP, 36)
    num_text = f"{check_number}/5"
    bb = draw.textbbox((0, 0), num_text, font=font_num)
    nw, nh = bb[2] - bb[0], bb[3] - bb[1]
    draw.text((badge_x + (badge_size - nw) // 2, badge_y + (badge_size - nh) // 2 - 5), num_text, font=font_num, fill=(255, 255, 255))

    font_item = ImageFont.truetype(FONT_JP, 50)
    item_text = "□ " + slide.get("item", "")
    draw_left_aligned(draw, item_text, font_item, dark, x=PAD_X, y=badge_y + badge_size + 40, gap=12)

    font_label = ImageFont.truetype(FONT_JP, 24)
    font_body  = ImageFont.truetype(FONT_JP, 30)
    y_cursor = badge_y + badge_size + 200

    for label, key, color in [
        ("▼ なぜダメか (事実)", "fact",   (90, 90, 90)),
        ("▼ どうなるか (影響)", "impact", (90, 90, 90)),
        ("▼ 今夜の打ち手",      "action", accent),
    ]:
        draw.text((PAD_X, y_cursor), label, font=font_label, fill=color)
        y_cursor += 36
        body = slide.get(key, "")
        y_cursor = draw_left_aligned(draw, body, font_body, (28, 34, 28), x=PAD_X, y=y_cursor, gap=10)
        y_cursor += 28

    draw_footer_bar(draw, dark)
    img.save(output_path, "PNG")
```

完了基準: ファイルに `def draw_check(` が grep でヒットする。

- [ ] **Step 2: `draw_score_cta()` 関数を追加**

`draw_cta` の直後に追加:

```python
def draw_score_cta(slide, colors, output_path):
    """スライド8: スコア判定 + CTA"""
    dark, accent, pale = colors
    img  = Image.new("RGB", (W, H), dark)
    draw = ImageDraw.Draw(img)

    font_score_title = ImageFont.truetype(FONT_JP, 36)
    font_score_count = ImageFont.truetype(FONT_JP, 44)
    font_score_label = ImageFont.truetype(FONT_JP, 32)
    font_score_note  = ImageFont.truetype(FONT_JP, 24)

    draw.text((PAD_X, 100), "【あなたの当てはまり度】", font=font_score_title, fill=pale)

    y = 170
    for level in slide.get("score_levels", []):
        count_text = f"{level.get('count', '')} 個"
        label_text = level.get("label", "")
        note_text  = level.get("comment", "")
        draw.text((PAD_X,        y),      count_text, font=font_score_count, fill=accent)
        draw.text((PAD_X + 200,  y + 6),  label_text, font=font_score_label, fill=pale)
        draw.text((PAD_X + 200,  y + 50), note_text,  font=font_score_note,  fill=pale)
        y += 110

    draw.rectangle([PAD_X, y + 20, W - PAD_X, y + 24], fill=accent)

    font_cta_main = ImageFont.truetype(FONT_JP, 60)
    font_cta_sub  = ImageFont.truetype(FONT_JP, 28)
    cta_text = slide.get("cta_text", "")
    bottom   = draw_center_lines(draw, cta_text, font_cta_main, pale, y=y + 60, gap=14)
    cta_sub  = slide.get("cta_sub", "")
    if cta_sub:
        draw_center_lines(draw, cta_sub, font_cta_sub, pale, y=bottom + 30, gap=8)

    draw_footer_bar(draw, dark)
    img.save(output_path, "PNG")
```

完了基準: ファイルに `def draw_score_cta(` が grep でヒットする。

- [ ] **Step 3: cover の clusterタグ表示と generate_theme() のディスパッチを更新**

`draw_cover` の冒頭を以下に置き換え:

```python
def draw_cover(slide, colors, output_path):
    """スライド1: カバー（クラスタータグ＋フック＋著者）"""
    dark, accent, pale = colors
    img  = Image.new("RGB", (W, H), dark)
    draw = ImageDraw.Draw(img)

    font_cluster = ImageFont.truetype(FONT_JP, 28)
    cluster_tag  = slide.get("cluster_tag", "")
    if cluster_tag:
        bb = draw.textbbox((0, 0), cluster_tag, font=font_cluster)
        cw = bb[2] - bb[0]
        draw.text(((W - cw) // 2, 120), cluster_tag, font=font_cluster, fill=accent)

    font_title = ImageFont.truetype(FONT_JP, 72)
    font_sub   = ImageFont.truetype(FONT_JP, 30)

    title  = slide["title"]
    bottom = draw_center_lines(draw, title, font_title, pale, y=H // 2 - 220, gap=20)

    draw.rectangle([(W - 80) // 2, bottom + 30, (W + 80) // 2, bottom + 34], fill=accent)

    if slide.get("subtitle"):
        draw_center_lines(draw, slide["subtitle"], font_sub, pale, y=bottom + 60, gap=8)

    draw_footer_bar(draw, dark)
    img.save(output_path, "PNG")
```

そして `generate_theme()` 内のディスパッチを更新（既存の `if/elif` ブロックに行を追加）:

```python
    check_number = 0
    for i, slide in enumerate(slides, start=1):
        output = OUTPUT_DIR / f"theme{theme_id:02d}_slide{i}.png"
        slide_type = slide.get("type")

        if slide_type == "cover":
            draw_cover(slide, colors, output)
        elif slide_type == "hook":
            draw_hook(slide, colors, output)
        elif slide_type == "check":
            check_number += 1
            draw_check(slide, colors, output, check_number)
        elif slide_type == "point":
            point_number += 1
            draw_point(slide, colors, output, point_number)
        elif slide_type == "score" or slide_type == "cta":
            if "score_levels" in slide:
                draw_score_cta(slide, colors, output)
            else:
                draw_cta(slide, colors, output)
        else:
            print(f"  ⚠️ theme{theme_id:02d} slide{i}: 未対応タイプ '{slide_type}'")
            continue

        print(f"  ✅ theme{theme_id:02d}_slide{i}.png ({slide_type})")
```

注意: `point_number = 0` の初期化は既存行のままにする。`check_number = 0` を新規に追加する。

完了基準: `python3 -c "import skin.skin_instagram_image_gen_v4 as m; print(hasattr(m, 'draw_check'), hasattr(m, 'draw_score_cta'))"` が `True True` を返す。

- [ ] **Step 4: THEME_COLORS を 30 テーマに拡張**

既存 1-20 はそのまま、21-30 を追加する（既存 1-20 の系統色を引き継ぐ）:

```python
    21: ((58, 22, 22),   (200, 80, 80),   (252, 232, 232)),  # cluster4 - エピソード
    22: ((22, 50, 55),   (50, 160, 170),  (228, 246, 248)),  # cluster4 - 数字
    23: ((30, 28, 60),   (110, 100, 200), (238, 236, 252)),  # cluster4 - 逆張り
    24: ((52, 38, 18),   (180, 130, 50),  (252, 244, 224)),  # cluster4 - エピソード
    25: ((55, 32, 18),   (210, 110, 50),  (252, 238, 224)),  # cluster5 - 数字
    26: ((50, 28, 45),   (170, 80, 150),  (250, 232, 246)),  # cluster5 - 逆張り
    27: ((30, 48, 22),   (120, 170, 60),  (238, 248, 224)),  # cluster5 - エピソード
    28: ((20, 46, 36),   (50, 170, 120),  (224, 246, 238)),  # cluster5 - 数字
    29: ((38, 36, 20),   (180, 155, 50),  (252, 248, 220)),  # cluster5 - 逆張り
    30: ((38, 22, 58),   (130, 80, 200),  (240, 232, 252)),  # cluster5 - エピソード
```

完了基準: `THEME_COLORS` 辞書のキーが 1〜30 まで全て存在することを確認。

```bash
python3 -c "from skin.skin_instagram_image_gen_v4 import THEME_COLORS; print(sorted(THEME_COLORS.keys()))"
```

期待出力: `[1, 2, 3, 4, ..., 30]`

- [ ] **Step 5: コミット**

```bash
git add skin/skin_instagram_image_gen_v4.py
git commit -m "feat: image_gen_v4 に check/score スライド描画と 21-30 配色を追加"
```

完了基準: `git log -1 --oneline` で本コミットが先頭。

---

### Task 1.3: progress.json を 5 → 8 バッチに拡張

**Files:**
- Modify: `skin/skin_instagram_batch_progress.json`

**注意:** `progress.json` 系は通常 GitHub Actions が書き換えるため手動編集禁止。本変更は構造変更の 1 回限りの例外として扱う。

- [ ] **Step 1: バッチ 6-8 を追加し total_batches を 8 に更新**

`skin/skin_instagram_batch_progress.json` を全面置換:

```json
{
  "current_batch": 1,
  "total_batches": 8,
  "batches": {
    "1": {
      "themes": [1, 2, 3, 4],
      "status": "released",
      "production_start": "2026-05-18",
      "release_date": "2026-05-24",
      "validation_until": "2026-06-06",
      "notes": "2026-05-24 リリース完了。クラスター再設計で内容を全面リライト予定"
    },
    "2": {
      "themes": [5, 6, 7, 8],
      "status": "pending",
      "production_start": "2026-05-25",
      "release_date": "2026-05-31",
      "validation_until": "2026-06-13",
      "notes": ""
    },
    "3": {
      "themes": [9, 10, 11, 12],
      "status": "pending",
      "production_start": "2026-06-01",
      "release_date": "2026-06-07",
      "validation_until": "2026-06-20",
      "notes": ""
    },
    "4": {
      "themes": [13, 14, 15, 16],
      "status": "pending",
      "production_start": "2026-06-08",
      "release_date": "2026-06-14",
      "validation_until": "2026-06-27",
      "notes": ""
    },
    "5": {
      "themes": [17, 18, 19, 20],
      "status": "pending",
      "production_start": "2026-06-15",
      "release_date": "2026-06-21",
      "validation_until": "2026-07-04",
      "notes": ""
    },
    "6": {
      "themes": [21, 22, 23, 24],
      "status": "pending",
      "production_start": "2026-06-22",
      "release_date": "2026-06-28",
      "validation_until": "2026-07-11",
      "notes": "クラスター 4 (スキンケア習慣) 完結バッチ"
    },
    "7": {
      "themes": [25, 26, 27, 28],
      "status": "pending",
      "production_start": "2026-06-29",
      "release_date": "2026-07-05",
      "validation_until": "2026-07-18",
      "notes": "クラスター 5 (体内環境・ホルモン) 前半"
    },
    "8": {
      "themes": [29, 30],
      "status": "pending",
      "production_start": "2026-07-06",
      "release_date": "2026-07-12",
      "validation_until": "2026-07-25",
      "notes": "クラスター 5 完結。2 本構成 (theme29-30)"
    }
  }
}
```

完了基準: `python3 -c "import json; d=json.load(open('skin/skin_instagram_batch_progress.json')); assert d['total_batches']==8; assert len(d['batches'])==8; print('ok')"` が `ok` を返す。

- [ ] **Step 2: コミット**

```bash
git add skin/skin_instagram_batch_progress.json
git commit -m "chore: バッチを 5 → 8 に拡張 (theme21-30 新規追加)"
```

完了基準: `git log -1 --oneline` で本コミットが先頭。

---

### Task 1.4: バッチ運用手順書を v2.1 仕様に更新

**Files:**
- Modify: `docs/skin_instagram_batch_workflow.md`

- [ ] **Step 1: バッチスケジュール表を 8 バッチに書き換え**

`docs/skin_instagram_batch_workflow.md` 内の「## Batch スケジュール（予定）」セクションを以下に置換:

```markdown
## Batch スケジュール（予定）

| Batch | テーマID | リリース予定 | 検証期間 |
|---|---|---|---|
| 1 [リライト] | theme01〜04 | 2026-05-24 リリース済 | 〜2026-06-06 |
| 2 | theme05〜08 | 2026-05-31 | 〜2026-06-13 |
| 3 | theme09〜12 | 2026-06-07 | 〜2026-06-20 |
| 4 | theme13〜16 | 2026-06-14 | 〜2026-06-27 |
| 5 | theme17〜20 | 2026-06-21 | 〜2026-07-04 |
| 6 [新規] | theme21〜24 | 2026-06-28 | 〜2026-07-11 |
| 7 [新規] | theme25〜28 | 2026-07-05 | 〜2026-07-18 |
| 8 [新規] | theme29〜30 | 2026-07-12 | 〜2026-07-25 |

→ 実際の日付は `skin/skin_instagram_batch_progress.json` の `batches.N.release_date` を参照。
```

完了基準: 上記表が `docs/skin_instagram_batch_workflow.md` に反映されている。

- [ ] **Step 2: CTA ローテーション説明を旧 `id % 4` から新クラスターサイクルに書き換え**

「## フック型・CTA型の自動割り当てルール」セクションを以下に置換:

```markdown
## フック型・CTA 型の自動割り当てルール（v2.1）

新規テーマを v2.1 化するときは、以下のローテーションで型を機械的に決める。

- **フック型**: `id % 3`
  - 1 = 数字型（例: 「肌を荒らす食卓 5 チェック」）
  - 2 = 逆張り型（例: 「化粧水を変えても肌は治りません」）
  - 0 = エピソード型（例: 「8 年気づけなかった食卓のクセ」）

- **CTA 型**: クラスター内 6 本サイクル（旧 `id % 4` ルールは破棄）
  - クラスター内 1 本目 = 保存
  - クラスター内 2 本目 = コメント
  - クラスター内 3 本目 = note 誘導
  - クラスター内 4 本目 = 保存
  - クラスター内 5 本目 = フォロー
  - クラスター内 6 本目 = note 誘導

30 本合計内訳: 保存 × 10、コメント × 5、フォロー × 5、note 誘導 × 10。

クラスター割当は `docs/superpowers/specs/2026-05-22-skin-instagram-cluster-redesign-design.md` を参照。
```

完了基準: 上記内容が手順書に反映されている。

- [ ] **Step 3: v2 → v2.1 表記の差し替え（slide_count, point→check 等）**

「## Batch N 作業手順」セクション「### 2. v2 コンテンツを反映」を以下に置換:

```markdown
### 2. v2.1 コンテンツを反映

`skin/carousel_content.json` の対象 4 テーマを v2.1 構造（8 枚: cover/hook/check×5/score_cta）に書き換え。

- `version: "v2.1"`、`slide_count: 8`
- `cluster`、`hook_type`、`cta_type` を設定
- `hook`、`fixed_hashtags`、`theme_hashtags`、`size_mix_hashtags` を設定
- `slides` を 8 枚構造（cover / hook / check×5 / score_cta）で記述
- check スライドは `item` / `fact` / `impact` / `action` の 4 フィールド
- 最終スライドは `score_levels` 配列 + `cta_text` / `cta_sub`
- `caption` は空文字で OK
```

完了基準: 「### 2. v2.1 コンテンツを反映」が手順書に存在する。

- [ ] **Step 4: コミット**

```bash
git add docs/skin_instagram_batch_workflow.md
git commit -m "docs: バッチ運用手順を v2.1 仕様 (8 バッチ・新 CTA ルール) に更新"
```

完了基準: `git log -1 --oneline` で本コミットが先頭。

---

## Phase 1.5: Batch 1 (theme01-04) リライト

リリース済の theme01-04 を新設計に乗せ替える。設計書 §5 の移行方針に従う。

### Task 1.5.1: theme01 を「肌を荒らす食卓 5 チェック」にリライト

**Files:**
- Modify: `skin/carousel_content.json`

- [ ] **Step 1: theme01 オブジェクトを v2.1 構造で全面書き換え**

`carousel_content.json` 内 `themes[]` の `id: 1` のオブジェクトを以下に置換:

```json
{
  "id": 1,
  "version": "v2.1",
  "slide_count": 8,
  "cluster": "cluster1_food",
  "hook_type": "number",
  "cta_type": "save",
  "hook": "肌を荒らす食卓 5 チェック",
  "fixed_hashtags": ["肌荒れ", "大人ニキビ", "肌改善"],
  "theme_hashtags": ["食事と肌", "血糖値", "腸活", "食改善", "糖質", "ニキビ食事"],
  "size_mix_hashtags": ["30代肌悩み", "20代ニキビ", "肌トラブル"],
  "slides": [
    {"type": "cover", "cluster_tag": "食卓と肌の関係", "title": "肌を荒らす食卓\n5 チェック", "subtitle": "あなたはいくつ当てはまる？"},
    {"type": "hook", "body": "肌荒れの原因はスキンケアではなく、毎日の食卓にあるかもしれません。\n5 つのチェックで自分の食卓を見直してみましょう。"},
    {"type": "check", "item": "朝に菓子パンを食べている", "fact": "精製糖は血糖値を急上昇させる", "impact": "インスリン急増 → 皮脂分泌が増える", "action": "ゆで卵+果物に置き換える"},
    {"type": "check", "item": "ジュースで水分補給している", "fact": "果糖は中性脂肪に変わりやすい", "impact": "炎症体質 → ニキビが悪化", "action": "炭酸水+レモンに切替"},
    {"type": "check", "item": "夜にラーメンを食べる", "fact": "高 GI 食品 + 油の連打", "impact": "夜間血糖値スパイク → 翌朝の肌くすみ", "action": "夜は雑穀ご飯+味噌汁にする"},
    {"type": "check", "item": "牛乳を毎日飲んでいる", "fact": "乳糖と乳製品ホルモンが皮脂を刺激", "impact": "皮脂量増加 → 毛穴詰まり", "action": "2 週間だけ豆乳に切替えて様子見"},
    {"type": "check", "item": "サラダ油で炒め物をする", "fact": "オメガ 6 過多は炎症を促す", "impact": "肌の赤み・かゆみが増える", "action": "オリーブ油・米油に置換"},
    {"type": "cta", "score_levels": [{"count": "0", "label": "優等生", "comment": "今の食卓を続けて OK"}, {"count": "1-2", "label": "黄信号", "comment": "1 つから直そう"}, {"count": "3+", "label": "赤信号", "comment": "食卓の見直しを優先"}], "cta_text": "保存して食卓を見直そう", "cta_sub": "@skin_reset_jp で続きをチェック"}
  ],
  "caption": ""
}
```

完了基準: `python3 -c "import json; d=json.load(open('skin/carousel_content.json')); t=[t for t in d['themes'] if t['id']==1][0]; assert t['version']=='v2.1' and len(t['slides'])==8; print('ok')"` が `ok` を返す。

- [ ] **Step 2: theme01 の画像を再生成して目視確認**

```bash
python3 skin/skin_instagram_image_gen_v4.py --theme 1
ls -la skin/skin_instagram_carousels/theme01_slide*.png
```

完了基準: `theme01_slide1.png` から `theme01_slide8.png` まで 8 枚生成され、ファイルサイズが 50KB を超えている。

---

### Task 1.5.2: theme02 を「化粧水より先に変えるべき食卓」にリライト

**Files:**
- Modify: `skin/carousel_content.json`

- [ ] **Step 1: theme02 オブジェクトを v2.1 構造で全面書き換え**

cluster: `cluster1_food`、hook_type: `contrarian`、cta_type: `comment`、note LP: `sugar` を踏まえ、theme01 と同じ構造で書く。

```json
{
  "id": 2,
  "version": "v2.1",
  "slide_count": 8,
  "cluster": "cluster1_food",
  "hook_type": "contrarian",
  "cta_type": "comment",
  "hook": "化粧水より先に変えるべき食卓",
  "fixed_hashtags": ["肌荒れ", "大人ニキビ", "肌改善"],
  "theme_hashtags": ["食事と肌", "血糖値", "腸活", "食改善", "糖質", "ニキビ食事"],
  "size_mix_hashtags": ["30代肌悩み", "20代ニキビ", "肌トラブル"],
  "slides": [
    {"type": "cover", "cluster_tag": "食卓と肌の関係", "title": "化粧水より先に\n変えるべき食卓", "subtitle": "あなたはいくつ当てはまる？"},
    {"type": "hook", "body": "スキンケアを高級品に変えても、食卓が荒れていれば肌は整いません。\nまずは砂糖との付き合い方から見直しましょう。"},
    {"type": "check", "item": "毎日 缶コーヒー (加糖) を飲む", "fact": "1 本に角砂糖 5 個分の糖", "impact": "AGEs 蓄積 → 肌のくすみ・たるみ", "action": "1 週間ブラックに切替えて肌を比較"},
    {"type": "check", "item": "夜にチョコや菓子をつまむ", "fact": "夜の糖質は皮脂を刺激", "impact": "翌朝のニキビが悪化", "action": "夜の間食はナッツに置き換え"},
    {"type": "check", "item": "白米と菓子パンが主食", "fact": "精製炭水化物は血糖値スパイクを起こす", "impact": "血糖値の乱高下 → 慢性炎症", "action": "玄米・全粒粉に切替"},
    {"type": "check", "item": "甘いラテで一息つく", "fact": "シロップ 1 杯 = 角砂糖 4 個", "impact": "糖化反応 → コラーゲン劣化", "action": "無糖ラテに豆乳で甘み調整"},
    {"type": "check", "item": "果物ジュースを健康だと思っている", "fact": "果糖の濃度は生の果物の数倍", "impact": "肝臓負担 → 肌のターンオーバー乱れ", "action": "果物は丸ごと食べる"},
    {"type": "cta", "score_levels": [{"count": "0", "label": "優等生", "comment": "甘い物との距離が取れている"}, {"count": "1-2", "label": "黄信号", "comment": "1 個から減らそう"}, {"count": "3+", "label": "赤信号", "comment": "砂糖断ち 2 週間チャレンジを推奨"}], "cta_text": "あなたはいくつ\n当てはまった？", "cta_sub": "コメントで教えてください"}
  ],
  "caption": ""
}
```

完了基準: 同じく `theme02` の `version == "v2.1"` と `len(slides) == 8` が確認できる。

- [ ] **Step 2: 画像を再生成**

```bash
python3 skin/skin_instagram_image_gen_v4.py --theme 2
ls skin/skin_instagram_carousels/theme02_slide*.png | wc -l
```

完了基準: `8` が出力される。

---

### Task 1.5.3: theme03 を「8 年気づけなかった私の食卓のクセ 5 つ」にリライト

**Files:**
- Modify: `skin/carousel_content.json`

- [ ] **Step 1: theme03 オブジェクトを v2.1 構造で全面書き換え**

```json
{
  "id": 3,
  "version": "v2.1",
  "slide_count": 8,
  "cluster": "cluster1_food",
  "hook_type": "episode",
  "cta_type": "note",
  "hook": "8 年気づけなかった私の食卓のクセ 5 つ",
  "fixed_hashtags": ["肌荒れ", "大人ニキビ", "肌改善"],
  "theme_hashtags": ["食事と肌", "血糖値", "腸活", "食改善", "糖質", "ニキビ食事"],
  "size_mix_hashtags": ["30代肌悩み", "20代ニキビ", "肌トラブル"],
  "slides": [
    {"type": "cover", "cluster_tag": "食卓と肌の関係", "title": "8 年気づけなかった\n食卓のクセ 5 つ", "subtitle": "あなたはいくつ当てはまる？"},
    {"type": "hook", "body": "肌荒れに 8 年悩んだ私が、ようやく気づいた食卓のクセ。\n意外なところに原因が隠れていました。"},
    {"type": "check", "item": "朝食を抜いて昼に大盛り", "fact": "空腹からの一気食いは血糖値スパイク", "impact": "皮脂量が翌朝ピーク", "action": "朝に味噌汁 1 杯+ご飯少量"},
    {"type": "check", "item": "和食でも醤油・味噌の取りすぎ", "fact": "塩分過多は水分代謝を乱す", "impact": "むくみ → 肌のくすみ・赤み", "action": "減塩タイプに切替+カリウム食材を増やす"},
    {"type": "check", "item": "外食ばかりで野菜不足", "fact": "ビタミン B 群・食物繊維欠乏", "impact": "腸内環境悪化 → 肌荒れ", "action": "外食でもサラダを 1 皿足す"},
    {"type": "check", "item": "甘い飲み物で「ご褒美」する", "fact": "糖質依存ループに入る", "impact": "肌の状態が一定しない", "action": "ご褒美は無糖紅茶+ハチミツに変更"},
    {"type": "check", "item": "夜遅くにアイスやスナック", "fact": "就寝前の糖質は炎症の引き金", "impact": "睡眠の質低下 → 肌の修復力ダウン", "action": "就寝 3 時間前で食事を終える"},
    {"type": "cta", "score_levels": [{"count": "0", "label": "優等生", "comment": "良い食習慣を維持中"}, {"count": "1-2", "label": "黄信号", "comment": "1 個から手放そう"}, {"count": "3+", "label": "赤信号", "comment": "腸活から始めることをおすすめ"}], "cta_text": "私の腸活ストーリーを\nプロフ note で公開中", "cta_sub": "プロフィールから読めます"}
  ],
  "caption": ""
}
```

完了基準: `theme03` の `version == "v2.1"` が確認できる。

- [ ] **Step 2: 画像再生成**

```bash
python3 skin/skin_instagram_image_gen_v4.py --theme 3
```

完了基準: 8 枚生成。

---

### Task 1.5.4: theme04 を「血糖値が荒らす肌 5 チェック」にリライト

**Files:**
- Modify: `skin/carousel_content.json`

- [ ] **Step 1: theme04 オブジェクトを v2.1 構造で全面書き換え**

設計書 §4 クラスター 1 の theme04 = 「血糖値が荒らす肌 5 チェック」(数字型・保存 CTA・note LP: bloodsugar)。

```json
{
  "id": 4,
  "version": "v2.1",
  "slide_count": 8,
  "cluster": "cluster1_food",
  "hook_type": "number",
  "cta_type": "save",
  "hook": "血糖値が荒らす肌 5 チェック",
  "fixed_hashtags": ["肌荒れ", "大人ニキビ", "肌改善"],
  "theme_hashtags": ["食事と肌", "血糖値", "腸活", "食改善", "糖質", "ニキビ食事"],
  "size_mix_hashtags": ["30代肌悩み", "20代ニキビ", "肌トラブル"],
  "slides": [
    {"type": "cover", "cluster_tag": "食卓と肌の関係", "title": "血糖値が荒らす肌\n5 チェック", "subtitle": "あなたはいくつ当てはまる？"},
    {"type": "hook", "body": "肌荒れと血糖値、実は強く結びついています。\n食後の眠気やイライラがある人は要チェック。"},
    {"type": "check", "item": "食後 1 時間以内に強い眠気が来る", "fact": "血糖値が急上昇 → 急降下している", "impact": "皮脂腺刺激 → 炎症性ニキビ", "action": "野菜・タンパクから食べる順番に変更"},
    {"type": "check", "item": "甘い物の直後にイライラする", "fact": "低血糖反応が起きている", "impact": "コルチゾール上昇 → 肌のバリア低下", "action": "甘い物の前にタンパクを入れる"},
    {"type": "check", "item": "白米だけでお腹を満たす", "fact": "高 GI 食品のみの食事", "impact": "血糖値スパイク連発", "action": "雑穀・もち麦をブレンド"},
    {"type": "check", "item": "間食でクッキー・パン", "fact": "精製糖質の追加投下", "impact": "1 日の血糖値変動が増える", "action": "間食はナッツ or 茹で卵"},
    {"type": "check", "item": "夜遅い炭水化物が多い", "fact": "就寝前の糖質は最も太りやすい", "impact": "睡眠時の修復力が低下", "action": "夜は炭水化物を半量にする"},
    {"type": "cta", "score_levels": [{"count": "0", "label": "優等生", "comment": "血糖値コントロール良好"}, {"count": "1-2", "label": "黄信号", "comment": "1 つから直そう"}, {"count": "3+", "label": "赤信号", "comment": "ベジファースト習慣を最優先"}], "cta_text": "保存して食事順を意識しよう", "cta_sub": "@skin_reset_jp で続きをチェック"}
  ],
  "caption": ""
}
```

完了基準: 8 枚生成可能・version v2.1 で保存される。

- [ ] **Step 2: 画像再生成**

```bash
python3 skin/skin_instagram_image_gen_v4.py --theme 4
ls skin/skin_instagram_carousels/theme0[1-4]_slide*.png | wc -l
```

完了基準: 出力が `32` (4 テーマ × 8 枚)。

- [ ] **Step 3: Batch 1 リライトをコミット**

```bash
git add skin/carousel_content.json skin/skin_instagram_carousels/theme0[1-4]_slide*.png
git commit -m "feat: Batch 1 (theme01-04) を v2.1 (クラスター 1 食卓と肌) にリライト"
```

完了基準: `git log -1 --oneline` で本コミットが先頭。

---

## Phase 2: Batch 2 リリース (theme05-08)

**バッチ共通テンプレ（以後 Batch 3-8 でも同じ手順）:**

各バッチで以下の Task を順番に実行する:

1. **Task N.1: テーマ別 v2.1 コンテンツ作成**（4 本 or 2 本）
2. **Task N.2: 画像生成と目視確認**
3. **Task N.3: 旧バッチの保存率レポート確認**
4. **Task N.4: progress.json を released に更新 + main マージ + push**
5. **Task N.5: 24 時間後の初動チェック**

### Task 2.1: theme05-08 を v2.1 コンテンツに置換

**Files:**
- Modify: `skin/carousel_content.json`

各テーマの設計書 §4 マッピング:
- theme05 = 「「ヘルシー」が実は肌荒れの原因」(逆張り・フォロー CTA・dairy)
- theme06 = 「グルテンを抜いて変わった私の肌」(エピソード・note CTA・gluten)
- theme07 = 「肌に効く栄養素ベスト 5」(数字・保存 CTA・zinc) ※クラスター 2 へ移行
- theme08 = 「サプリより食卓で取るべき栄養」(逆張り・コメント CTA・omega3)

注意: theme05-06 はクラスター 1 (食卓と肌)、theme07-08 はクラスター 2 (栄養素と肌)。クラスター切替時は `cluster` フィールドと `theme_hashtags` を切り替える。

- [ ] **Step 1: theme05 を Task 1.5.1 と同じ JSON 構造で記述**

カバー文・5 チェック項目・スコア判定文を以下の仕様で執筆 (cluster=cluster1_food, theme_hashtags はクラスター 1 のもの):

```
カバー: 「『ヘルシー』が実は肌荒れの原因」
hook: ヘルシー食品でも肌に悪いものがある衝撃を共感喚起
check 1-5:
  1. 朝のスムージーで生野菜大量
     fact: 生野菜の冷えが胃腸の働きを下げる
     impact: 腸内環境悪化 → ニキビ
     action: スムージーは常温野菜+生姜を加える
  2. グラノーラを朝食にしている
     fact: 砂糖と植物油が大量
     impact: 血糖値上昇 → 皮脂分泌
     action: 無糖オートミール+ナッツに変更
  3. プロテインバーで栄養補給
     fact: 人工甘味料と乳製品由来ホルモン
     impact: 腸内細菌の偏り
     action: 茹で卵+果物に置き換え
  4. 豆乳ラテを毎日飲む
     fact: 大豆イソフラボン過多はホルモンバランスを乱す
     impact: 生理周期前の肌荒れ悪化
     action: 隔日にしてアーモンドミルクと交互
  5. ヨーグルトでお腹整える
     fact: 個人差で乳糖不耐の場合は逆効果
     impact: 腸内ガス → 肌くすみ
     action: 2 週間止めて様子見、必要なら甘酒に
score_levels: 0/1-2/3+ で食卓と肌の関係
cta: フォロー (「@skin_reset_jp で続きを毎日配信中」)
```

完了基準: theme05 の `version == "v2.1"`、`cluster == "cluster1_food"`、`cta_type == "follow"`。

- [ ] **Step 2: theme06 を同様に v2.1 構造で記述**

```
カバー: 「グルテンを抜いて変わった私の肌」
note LP: gluten
check 1-5:
  1. パン・パスタが主食
  2. 醤油・味噌に隠れた小麦
  3. 揚げ物の衣で小麦
  4. お菓子はほぼ小麦
  5. ビール・ハイボールも小麦
score_levels & cta: note 誘導 (「2 週間グルテン抜き実験を note で公開」)
cluster: cluster1_food, theme_hashtags は cluster1 のもの
```

完了基準: theme06 の `version == "v2.1"`、`cta_type == "note"`。

- [ ] **Step 3: theme07 を v2.1 構造（クラスター 2 = 栄養素と肌）で記述**

```
カバー: 「肌に効く栄養素ベスト 5」
note LP: zinc
cluster: cluster2_nutrient
theme_hashtags: ["栄養と肌", "亜鉛", "ビタミンD", "鉄分", "サプリ", "栄養不足"]
check 1-5: 亜鉛/ビタミンD/オメガ3/鉄/タンパク不足チェック（その人がどの栄養素不足か診断）
score_levels & cta: 保存
```

完了基準: theme07 の `cluster == "cluster2_nutrient"`。

- [ ] **Step 4: theme08 を v2.1 構造（クラスター 2）で記述**

```
カバー: 「サプリより食卓で取るべき栄養」
note LP: omega3
cluster: cluster2_nutrient
check 1-5: サプリ偏重チェック、食卓で取れる代替提案
score_levels & cta: コメント
```

完了基準: theme08 の `cluster == "cluster2_nutrient"`、`cta_type == "comment"`。

- [ ] **Step 5: theme05-08 すべての画像を生成**

```bash
python3 skin/skin_instagram_image_gen_v4.py --theme 5
python3 skin/skin_instagram_image_gen_v4.py --theme 6
python3 skin/skin_instagram_image_gen_v4.py --theme 7
python3 skin/skin_instagram_image_gen_v4.py --theme 8
ls skin/skin_instagram_carousels/theme0[5-8]_slide*.png | wc -l
```

完了基準: 出力が `32`。

- [ ] **Step 6: 旧 Batch 1 (theme01-04) の保存率レポート確認**

```bash
python3 skin/skin_instagram_report.py --batch 1
```

完了基準: コマンドが落ちずに何らかの集計を返す。黄信号・赤信号が出ていたらロールバック検討。

- [ ] **Step 7: progress.json を released に更新 + main マージ**

```bash
python3 - <<'EOF'
import json
from pathlib import Path
p = Path("skin/skin_instagram_batch_progress.json")
d = json.loads(p.read_text(encoding="utf-8"))
d["current_batch"] = 3
d["batches"]["2"]["status"] = "released"
d["batches"]["2"]["notes"]  = "2026-05-31 リリース完了"
p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print("ok")
EOF

git add skin/carousel_content.json skin/skin_instagram_carousels/theme0[5-8]_slide*.png skin/skin_instagram_batch_progress.json
git commit -m "feat: Batch 2 (theme05-08) を v2.1 でリリース"
git checkout main
git merge --no-ff skin-instagram-cluster-redesign
git push origin main
git checkout skin-instagram-cluster-redesign
```

完了基準: `main` に Batch 2 が反映されていて push 済み。

- [ ] **Step 8: 24 時間後の初動チェック**

リリース翌日に以下を確認:
- @skin_reset_jp に新画像が投稿されているか
- 8 枚すべて表示されているか
- キャプションのフック・CTA が新設計通りか
- 警告コメント・薬機法指摘がないか

完了基準: 異常がなければ Phase 3 へ。異常時は `git checkout skin-instagram-cluster-redesign-before -- skin/carousel_content.json skin/skin_instagram_carousels/` でロールバック。

---

## Phase 3: Batch 3 リリース (theme09-12)

設計書 §4 クラスター 2 (栄養素と肌) 残り + クラスター 3 開始。

- theme09 = 「亜鉛で人生が変わった話」(エピソード・note CTA・zinc)
- theme10 = 「ビタミン D 不足 5 チェック」(数字・保存 CTA・vitamind)
- theme11 = 「「鉄分」より大事な栄養」(逆張り・フォロー CTA・iron)
- theme12 = 「発酵食を 1 ヶ月続けた結果」(エピソード・note CTA・probiotics)

### Task 3.1〜3.5: Batch 2 と同じテンプレで実装

- [ ] **Step 1: theme09 を v2.1 で執筆 (cluster=cluster2_nutrient, cta_type=note)**

完了基準: `cluster == "cluster2_nutrient"`、`cta_type == "note"`。check 内容は亜鉛が肌にもたらす変化・エピソード性のあるチェック項目を 5 つ。

- [ ] **Step 2: theme10 を v2.1 で執筆 (cluster=cluster2_nutrient, cta_type=save)**

完了基準: `cta_type == "save"`、check はビタミン D 不足サインを 5 つ（疲れやすい・骨弱い・気分沈み・風邪引きやすい・肌乾燥）。

- [ ] **Step 3: theme11 を v2.1 で執筆 (cluster=cluster2_nutrient, cta_type=follow)**

完了基準: 逆張り型ヘッドラインで、鉄より重要な栄養素 (例: B12、葉酸) を扱う。`cta_type == "follow"`。

- [ ] **Step 4: theme12 を v2.1 で執筆 (cluster=cluster2_nutrient, cta_type=note)**

完了基準: エピソード型で 1 ヶ月発酵食実験の結果を check 形式に変換 (味噌・納豆・キムチ・ヨーグルト・甘酒の習慣化チェック)。

- [ ] **Step 5: 画像生成 + 旧バッチレポート + リリース (Batch 2 Step 5-8 と同じ手順)**

完了基準: theme09-12 の 32 枚が生成され、`progress.json` の batch 3 が `released`、main に push 済み。

---

## Phase 4: Batch 4 リリース (theme13-16)

クラスター 3 (睡眠・自律神経と肌) スタート。

- theme13 = 「自律神経が乱れる夜習慣 5」(数字・保存・sleepquality)
- theme14 = 「「8 時間睡眠」が肌を荒らす理由」(逆張り・コメント・sleepquality)
- theme15 = 「枕を変えて肌が整った話」(エピソード・note・pillow)
- theme16 = 「ストレス肌 5 チェック」(数字・保存・stress)

### Task 4.1〜4.5: Batch 2 と同じテンプレで実装

- [ ] **Step 1-4: theme13-16 を v2.1 で執筆 (cluster=cluster3_sleep, theme_hashtags=["睡眠と肌","自律神経","ストレスケア","睡眠改善","寝る前"])**

完了基準: 4 テーマすべて `version == "v2.1"`、`cluster == "cluster3_sleep"`。CTA タイプはクラスター位置 (1=保存, 2=コメント, 3=note, 4=保存) のサイクル通り。

- [ ] **Step 5: 画像生成 + リリース手順 (Batch 2 Step 5-8 と同じ)**

完了基準: main に Batch 4 が反映され push 済み。

---

## Phase 5: Batch 5 リリース (theme17-20)

クラスター 3 完結 + クラスター 4 開始。

- theme17 = 「お酒より怖い『夜カフェ』」(逆張り・フォロー・caffeine)
- theme18 = 「体温を上げて変わった肌」(エピソード・note・bodytemp)
- theme19 = 「洗顔の落とし穴 5 チェック」(数字・保存・cleansing) ※クラスター 4
- theme20 = 「化粧水を変えても肌は治りません」(逆張り・コメント・skincare) ※クラスター 4

### Task 5.1〜5.5

- [ ] **Step 1: theme17 を執筆 (cluster3_sleep, hook=contrarian, cta=follow)**

完了基準: cta_type が follow。

- [ ] **Step 2: theme18 を執筆 (cluster3_sleep, hook=episode, cta=note)**

完了基準: cta_type が note、クラスター 3 を完結。

- [ ] **Step 3: theme19 を執筆 (cluster4_skincare, hook=number, cta=save, theme_hashtags=["スキンケア","洗顔","保湿","大人ニキビ対策","朝のスキンケア"])**

完了基準: cluster が cluster4_skincare に切替わる。

- [ ] **Step 4: theme20 を執筆 (cluster4_skincare, hook=contrarian, cta=comment)**

完了基準: 旧 theme02 の「化粧水を変えても肌は治りません」題材を活かしつつ、v2.1 構造で書き直されている。

- [ ] **Step 5: 画像生成 + リリース (Batch 2 Step 5-8 と同じ)**

完了基準: main に Batch 5 反映、push 済み。

---

## Phase 6: Batch 6 リリース (theme21-24, 新規)

クラスター 4 完結。

- theme21 = 「洗顔を減らしたら肌が整った話」(エピソード・note・skincare)
- theme22 = 「保湿の誤解 5 チェック」(数字・保存・hydration)
- theme23 = 「シャンプーが肌荒れの原因かも」(逆張り・フォロー・shampoo)
- theme24 = 「口内ケアで変わった私の肌」(エピソード・note・oral)

### Task 6.1〜6.5

- [ ] **Step 1: theme21 を執筆 (cluster4_skincare, episode, note)**

完了基準: 旧 theme04 の素材を新フォーマットで書き直し。`cta_type == "note"`。

- [ ] **Step 2: theme22 を執筆 (cluster4_skincare, number, save)**

完了基準: 保湿に関する誤解 5 つを check 化。

- [ ] **Step 3: theme23 を執筆 (cluster4_skincare, contrarian, follow)**

完了基準: シャンプーの選び方・洗髪頻度などのチェック。

- [ ] **Step 4: theme24 を執筆 (cluster4_skincare, episode, note)**

完了基準: 口内ケアと肌の関連の体験談チェック。

- [ ] **Step 5: 画像生成 + リリース (Batch 2 Step 5-8 と同じ手順)**

完了基準: main に Batch 6 が反映され push 済み。

---

## Phase 7: Batch 7 リリース (theme25-28, 新規)

クラスター 5 (体内環境・ホルモン) 前半。

- theme25 = 「ホルモン乱れ 5 チェック」(数字・保存・hormone)
- theme26 = 「『日焼け止め』だけでは紫外線対策不足」(逆張り・コメント・uv)
- theme27 = 「運動を始めて肌が変わった話」(エピソード・note・exercise)
- theme28 = 「リーキーガット 5 チェック」(数字・保存・leakygut)

### Task 7.1〜7.5

- [ ] **Step 1: theme25 を執筆 (cluster5_hormone, number, save, theme_hashtags=["ホルモンバランス","紫外線対策","運動と肌","リーキーガット","体質改善"])**

完了基準: cluster が cluster5_hormone に切替わる。

- [ ] **Step 2: theme26 を執筆 (cluster5_hormone, contrarian, comment)**

完了基準: UV ケアに関する逆張りチェック。

- [ ] **Step 3: theme27 を執筆 (cluster5_hormone, episode, note)**

完了基準: 運動 → 肌変化の体験談チェック。

- [ ] **Step 4: theme28 を執筆 (cluster5_hormone, number, save)**

完了基準: リーキーガット症状チェック。

- [ ] **Step 5: 画像生成 + リリース**

完了基準: main に Batch 7 反映・push 済み。

---

## Phase 8: Batch 8 リリース (theme29-30, 完結)

クラスター 5 完結。2 本のみ。

- theme29 = 「ファスティングが合わない肌タイプ」(逆張り・フォロー・fasting)
- theme30 = 「1 年かけた肌改善ロードマップ」(エピソード・note・roadmap)

### Task 8.1〜8.4 (Step 数 4 に削減: 2 本のみ)

- [ ] **Step 1: theme29 を執筆 (cluster5_hormone, contrarian, follow)**

完了基準: ファスティングが向かない肌タイプチェック。

- [ ] **Step 2: theme30 を執筆 (cluster5_hormone, episode, note)**

完了基準: 1 年スパンの肌改善ロードマップを各四半期のチェック項目で構成。

- [ ] **Step 3: 画像生成 (2 テーマ × 8 枚 = 16 枚)**

```bash
python3 skin/skin_instagram_image_gen_v4.py --theme 29
python3 skin/skin_instagram_image_gen_v4.py --theme 30
ls skin/skin_instagram_carousels/theme29_slide*.png skin/skin_instagram_carousels/theme30_slide*.png | wc -l
```

完了基準: 出力が `16`。

- [ ] **Step 4: リリース + 全完走確認**

```bash
python3 - <<'EOF'
import json
from pathlib import Path
p = Path("skin/skin_instagram_batch_progress.json")
d = json.loads(p.read_text(encoding="utf-8"))
d["current_batch"] = 8  # 最終バッチに到達
d["batches"]["8"]["status"] = "released"
d["batches"]["8"]["notes"]  = "2026-07-12 リリース完了 (全 30 テーマ完走)"
p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print("ok")
EOF

git add skin/carousel_content.json skin/skin_instagram_carousels/theme29_slide*.png skin/skin_instagram_carousels/theme30_slide*.png skin/skin_instagram_batch_progress.json
git commit -m "feat: Batch 8 (theme29-30) リリースで全 30 テーマ完走"
git checkout main
git merge --no-ff skin-instagram-cluster-redesign
git push origin main
```

最終確認:

```bash
python3 -c "import json; d=json.load(open('skin/carousel_content.json')); v21=[t for t in d['themes'] if t.get('version')=='v2.1']; print(f'v2.1 themes: {len(v21)}'); assert len(v21)==30, f'expected 30 got {len(v21)}'; print('全 30 テーマ v2.1 化完了')"
ls skin/skin_instagram_carousels/theme*_slide*.png | wc -l
```

完了基準: 1 行目が `v2.1 themes: 30` を返し、2 行目が `240` を返す。

---

## 全完走チェックリスト (Phase 8 完了後)

- [ ] 全 30 テーマが `version: "v2.1"` で書かれている
- [ ] 各テーマに `cluster`、`hook_type`、`cta_type` が設定されている
- [ ] `theme_hashtags` がクラスター別に正しく設定されている (cluster1: 食事系 / cluster2: 栄養系 / cluster3: 睡眠系 / cluster4: スキンケア系 / cluster5: ホルモン系)
- [ ] CTA タイプ内訳が 保存×10、コメント×5、note×10、フォロー×5 になっている
- [ ] 画像 PNG が 240 枚 (30 × 8) 生成されている
- [ ] `skin/skin_instagram_batch_progress.json` の `total_batches == 8`、batch 1-8 すべて `released`
- [ ] `docs/skin_instagram_batch_workflow.md` の表が 8 バッチに更新済み
- [ ] `git log main --oneline | head -10` で 8 バッチ分のリリースコミットが見える

確認コマンド:

```bash
python3 - <<'EOF'
import json
d = json.load(open('skin/carousel_content.json'))
ctas = {}
for t in d['themes']:
    if t.get('version') == 'v2.1':
        ctas[t.get('cta_type', '?')] = ctas.get(t.get('cta_type', '?'), 0) + 1
print('CTA 内訳:', ctas)
assert ctas.get('save') == 10, f"save 期待 10、実際 {ctas.get('save')}"
assert ctas.get('comment') == 5, f"comment 期待 5、実際 {ctas.get('comment')}"
assert ctas.get('note') == 10, f"note 期待 10、実際 {ctas.get('note')}"
assert ctas.get('follow') == 5, f"follow 期待 5、実際 {ctas.get('follow')}"
print('OK 全完走')
EOF
```

期待出力: `CTA 内訳: {'save': 10, 'comment': 5, 'note': 10, 'follow': 5}` と `OK 全完走`。

---

## ロールバック手順 (どのフェーズでも使用可)

異常検知時 (黄信号・赤信号・薬機法警告・画像表示不良など):

```bash
git checkout skin-instagram-cluster-redesign-before -- skin/carousel_content.json skin/skin_instagram_carousels/
git commit -m "Rollback: skin Instagram クラスター再設計を一時停止"
git push origin main
```

ロールバック後、原因を分析してから該当 Phase の Task を再実行。

---

## 参考: テーマ別 note LP 対応表 (設計書 §4 より)

| theme ID | クラスター | hook型 | CTA型 | note LP |
|---|---|---|---|---|
| 1 | 食卓と肌 | 数字 | 保存 | food |
| 2 | 食卓と肌 | 逆張り | コメント | sugar |
| 3 | 食卓と肌 | エピソード | note | chokatsu |
| 4 | 食卓と肌 | 数字 | 保存 | bloodsugar |
| 5 | 食卓と肌 | 逆張り | フォロー | dairy |
| 6 | 食卓と肌 | エピソード | note | gluten |
| 7 | 栄養素と肌 | 数字 | 保存 | zinc |
| 8 | 栄養素と肌 | 逆張り | コメント | omega3 |
| 9 | 栄養素と肌 | エピソード | note | zinc |
| 10 | 栄養素と肌 | 数字 | 保存 | vitamind |
| 11 | 栄養素と肌 | 逆張り | フォロー | iron |
| 12 | 栄養素と肌 | エピソード | note | probiotics |
| 13 | 睡眠と肌 | 数字 | 保存 | sleepquality |
| 14 | 睡眠と肌 | 逆張り | コメント | sleepquality |
| 15 | 睡眠と肌 | エピソード | note | pillow |
| 16 | 睡眠と肌 | 数字 | 保存 | stress |
| 17 | 睡眠と肌 | 逆張り | フォロー | caffeine |
| 18 | 睡眠と肌 | エピソード | note | bodytemp |
| 19 | スキンケア | 数字 | 保存 | cleansing |
| 20 | スキンケア | 逆張り | コメント | skincare |
| 21 | スキンケア | エピソード | note | skincare |
| 22 | スキンケア | 数字 | 保存 | hydration |
| 23 | スキンケア | 逆張り | フォロー | shampoo |
| 24 | スキンケア | エピソード | note | oral |
| 25 | ホルモン | 数字 | 保存 | hormone |
| 26 | ホルモン | 逆張り | コメント | uv |
| 27 | ホルモン | エピソード | note | exercise |
| 28 | ホルモン | 数字 | 保存 | leakygut |
| 29 | ホルモン | 逆張り | フォロー | fasting |
| 30 | ホルモン | エピソード | note | roadmap |
