# skin Instagram Batch N リリース手順書

Batch 1（theme01〜04）のリライト完了後、Batch 2〜5 を同じ流れで展開するための共通手順。

元の実装計画: `docs/superpowers/plans/2026-05-18-skin-instagram-rewrite.md`

---

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

---

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

---

## Batch N 作業手順

### 1. ブランチ作成 & バックアップタグ

```bash
git checkout main
git pull origin main
git checkout -b skin-instagram-batch-N
git tag skin-instagram-batch-N-before main
git push origin skin-instagram-batch-N-before
```

### 2. v2.1 コンテンツを反映

`skin/carousel_content.json` の対象 4 テーマを v2.1 構造（8 枚: cover/hook/check×5/score_cta）に書き換え。

- `version: "v2.1"`、`slide_count: 8`
- `cluster`、`hook_type`、`cta_type` を設定
- `hook`、`fixed_hashtags`、`theme_hashtags`、`size_mix_hashtags` を設定
- `slides` を 8 枚構造（cover / hook / check×5 / score_cta）で記述
- check スライドは `item` / `fact` / `impact` / `action` の 4 フィールド
- 最終スライドは `score_levels` 配列 + `cta_text` / `cta_sub`
- `caption` は空文字で OK

### 3. 画像生成（Task 10 と同じ）

```bash
python3 skin/skin_instagram_image_gen_v4.py --theme N1
python3 skin/skin_instagram_image_gen_v4.py --theme N2
python3 skin/skin_instagram_image_gen_v4.py --theme N3
python3 skin/skin_instagram_image_gen_v4.py --theme N4
ls skin/skin_instagram_carousels/theme0[A-D]_slide*.png | wc -l   # 32
```

→ 目視確認: カバーのフックの読みやすさ、フッターバー、番号バッジ、文字のはみ出し、配色。

### 4. 旧バッチの検証レポートを確認

```bash
python3 skin/skin_instagram_report.py --batch (N-1)
```

→ 黄信号（-10%下落で3日連続）または赤信号（-30%下落で2日連続）が出ていないか確認。出ていればロールバックを検討。

### 5. 学習を反映

伸び悩んだテーマがあれば、フック型・CTA型を変えて作り直す。例:
- 数字型で伸びなかった → 逆張り型に変更
- note誘導CTAでクリックが伸びなかった → 保存CTAに変更

### 6. バッチ進行管理を更新 & リリース（Task 12 と同じ）

```bash
python3 - <<'EOF'
import json
from pathlib import Path
p = Path("skin/skin_instagram_batch_progress.json")
d = json.loads(p.read_text(encoding="utf-8"))
d["current_batch"]            = N + 1
d["batches"][str(N)]["status"] = "released"
d["batches"][str(N)]["notes"]  = "YYYY-MM-DD リリース完了"
p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"✅ Batch {N} を released に更新")
EOF

git add skin/carousel_content.json skin/skin_instagram_carousels/ skin/skin_instagram_batch_progress.json
git commit -m "feat: Batch N (themeNN〜NN) を v2 化してリリース"
git checkout main
git merge --no-ff skin-instagram-batch-N
git push origin main
```

### 7. 初動チェック（24時間後）

- @skin_reset_jp に v2 カルーセルが投稿されているか
- 画像が8枚正しく表示されているか
- キャプションのフック・CTAが新設計通りか
- 警告コメント・薬機法指摘がないか

→ 異常があれば即ロールバック:

```bash
git checkout skin-instagram-batch-N-before -- skin/carousel_content.json skin/skin_instagram_carousels/
git commit -m "Rollback skin Instagram batch N"
git push origin main
```

---

## Batch 1 リリース後に対応する追加実装

`skin/skin_instagram_report.py` の `get_v2_save_rates_by_theme` は初版が暫定実装（空辞書を返す）。Batch 1 の投稿データが2週間分蓄積されたら以下に差し替える:

```python
def get_v2_save_rates_by_theme(analytics: dict, target_theme_ids: list[int]) -> dict[int, list[float]]:
    """
    v2投稿をテーマ別に集計する。
    投稿のキャプション冒頭（フック）と carousel_content.json の hook 文字列を突き合わせて
    テーマIDを逆引きする。
    """
    # 1. carousel_content.json から hook -> theme_id の対応表を作る
    content    = load_json(CONTENT_FILE)
    hook_to_id = {}
    for theme in content["themes"]:
        if theme.get("version") != "v2":
            continue
        hook_to_id[theme.get("hook", "")] = theme["id"]

    # 2. analytics の各投稿のcaption冒頭をマッチさせる
    result = {tid: [] for tid in target_theme_ids}
    for post_id, post_data in analytics.get("posts", {}).items():
        caption = post_data.get("caption", "")
        for hook, tid in hook_to_id.items():
            if hook and caption.startswith(hook[:30]):  # 先頭30字でマッチ
                if tid in target_theme_ids:
                    result[tid].append(post_data.get("save_rate", 0.0))
                break
    return result
```

---

## 全Batch完走時の到達状態（2026-07-04 目標）

- 全20テーマが v2 化済み
- `skin_instagram_analytics.json` に2週間以上の v2 データ蓄積
- 全テーマで保存率 +30% 以上を達成（または絶対値で改善）

→ 達成後の発展候補:
- 21〜30テーマの新規追加
- カバー画像を Higgsfield AI で生成
- ronin Instagram に同フレーム展開
