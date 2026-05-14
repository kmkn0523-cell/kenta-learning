# skin Instagram カルーセル投稿＋フォロワー増加 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 静止画1枚投稿をカルーセル（5枚スライド）に切り替え、保存率を上げてフォロワーを増やす

**Architecture:** HTML→PNG方式で保存系カルーセル画像を20テーマ×5枚=100枚一括生成し、GitHubにコミット。Instagram Graph APIのカルーセル投稿フロー（子コンテナ×N枚→カルーセルコンテナ→公開）に対応したスクリプトに改修する。コメント活動ガイドを手動運用で並行実施。

**Tech Stack:** Python 3.12, playwright（HTML→PNG生成/ローカルのみ）, requests（Instagram Graph API）, pytest

---

## ファイル構成

| 操作 | パス | 役割 |
|------|------|------|
| 新規作成 | `skin/carousel_content.json` | 20テーマのスライド内容定義 |
| 新規作成 | `skin/skin_instagram_image_gen_v3.py` | HTML→PNG画像生成スクリプト（ローカル実行のみ） |
| 新規作成 | `skin/skin_instagram_carousels/` | 生成した100枚の画像置き場 |
| 新規作成 | `tests/test_carousel.py` | 生成・投稿ロジックのテスト |
| 変更 | `skin/skin_instagram_auto_post.py` | カルーセルAPI対応に改修 |
| 変更 | `skin/skin_instagram_progress.json` | カルーセル単位にリセット |

---

## Task 1: playwright をインストールする

> ⚠️ 新しいライブラリのインストールになるため、実行前にKentaさんの承認を得ること

**Files:**
- なし（環境セットアップのみ）

- [ ] **Step 1: playwright をインストールする**

```bash
pip install playwright
playwright install chromium
```

- [ ] **Step 2: インストール確認する**

```bash
python3 -c "from playwright.sync_api import sync_playwright; print('OK')"
```

期待出力: `OK`

- [ ] **Step 3: コミット（不要。環境のみの変更）**

---

## Task 2: carousel_content.json を作成する

**Files:**
- 新規作成: `skin/carousel_content.json`

- [ ] **Step 1: ファイルを作成する**

`skin/carousel_content.json` に以下の内容を書く。

```json
{
  "themes": [
    {
      "id": 1,
      "caption": "これ全部やってたら、スキンケアを変えても治りません。\n内側に問題があるサインです。\n保存して一つずつ確認してみてください。\n\n#肌荒れ #大人ニキビ #スキンケア #腸活 #美肌習慣 #肌改善 #敏感肌 #ニキビ #肌荒れ改善",
      "slides": [
        {"type": "cover", "title": "肌荒れが治らない人の\n共通点7つ", "subtitle": "当てはまるほど内側から治すべきサイン"},
        {"type": "list", "heading": "共通点 ①〜③", "items": ["甘い飲み物を毎日飲んでいる", "就寝が日付変わる頃", "パン・麺が主食になっている"]},
        {"type": "list", "heading": "共通点 ④〜⑤", "items": ["洗顔を1日3回以上している", "高い化粧品を重ね塗りしている"]},
        {"type": "list", "heading": "共通点 ⑥〜⑦", "items": ["便秘または下痢が続いている", "ストレスで食いしばり・歯ぎしり癖がある"]},
        {"type": "cta", "text": "保存して\nチェックに使ってね", "sub": "プロフィールのnoteに\n改善の全工程をまとめています"}
      ]
    },
    {
      "id": 2,
      "caption": "スキンケアより先に見直すべき食べ物があります。\n保存して今日の食事から変えてみてください。\n\n#肌荒れ #大人ニキビ #スキンケア #腸活 #美肌習慣 #肌改善 #敏感肌 #ニキビ #肌荒れ改善",
      "slides": [
        {"type": "cover", "title": "肌に悪い食べ物\nワースト5", "subtitle": "知らずに毎日食べているかもしれない"},
        {"type": "list", "heading": "ワースト ①〜②", "items": ["砂糖入り飲み物（コーヒーミルク含む）", "白い小麦製品（パン・パスタ・うどん）"]},
        {"type": "list", "heading": "ワースト ③〜④", "items": ["乳製品の摂りすぎ（牛乳・チーズ）", "揚げ物・スナック菓子（酸化した油）"]},
        {"type": "list", "heading": "ワースト ⑤", "items": ["アルコール（特に毎日飲む習慣）", "→ 腸の炎症を悪化させ、肌荒れが長引く"]},
        {"type": "cta", "text": "保存して\n食事の見直しに使ってね", "sub": "プロフィールのnoteに\n改善の全工程をまとめています"}
      ]
    },
    {
      "id": 3,
      "caption": "肌荒れが続く人と改善した人、習慣の違いはここです。\n保存してどちら側かチェックしてみてください。\n\n#肌荒れ #大人ニキビ #スキンケア #腸活 #美肌習慣 #肌改善 #敏感肌 #ニキビ #肌荒れ改善",
      "slides": [
        {"type": "cover", "title": "肌荒れを繰り返す人\nvs 改善した人の習慣", "subtitle": "違いはスキンケアではなかった"},
        {"type": "comparison", "heading": "水分補給", "left": "甘い飲み物で喉を潤す", "right": "水・緑茶を1日2L飲む"},
        {"type": "comparison", "heading": "食事", "left": "パン・麺が毎食の主食", "right": "玄米・芋類に少しずつ変えた"},
        {"type": "comparison", "heading": "睡眠とスキンケア", "left": "遅寝＋高い美容液を重ねる", "right": "23時就寝＋化粧水1本だけ"},
        {"type": "cta", "text": "保存して\nどちら側か確認してね", "sub": "プロフィールのnoteに\n改善の全工程をまとめています"}
      ]
    },
    {
      "id": 4,
      "caption": "肌改善には正しい順番があります。\n順番を間違えると何をやっても効果が出ません。\n保存して順番通りに試してください。\n\n#肌荒れ #大人ニキビ #スキンケア #腸活 #美肌習慣 #肌改善 #敏感肌 #ニキビ #肌荒れ改善",
      "slides": [
        {"type": "cover", "title": "肌改善の\n正しい順番4ステップ", "subtitle": "スキンケアは最後でいい"},
        {"type": "list", "heading": "Step 1（最初にやること）", "items": ["睡眠を23時前就寝に固定する", "→ 成長ホルモンで肌が再生される"]},
        {"type": "list", "heading": "Step 2（次にやること）", "items": ["砂糖と白い小麦を週1回以下に減らす", "→ 血糖値スパイクが肌炎症の元凶"]},
        {"type": "list", "heading": "Step 3〜4（仕上げ）", "items": ["腸活（発酵食品・水・食物繊維）", "スキンケアをシンプルにする（引き算）"]},
        {"type": "cta", "text": "保存して\nStep 1から始めてね", "sub": "プロフィールのnoteに\n改善の全工程をまとめています"}
      ]
    },
    {
      "id": 5,
      "caption": "腸活に本当に効いた食べ物だけ厳選しました。\nサプリより先にこれを試してください。\n保存してください。\n\n#肌荒れ #大人ニキビ #スキンケア #腸活 #美肌習慣 #肌改善 #敏感肌 #ニキビ #肌荒れ改善",
      "slides": [
        {"type": "cover", "title": "腸活に本当に効いた\n食べ物TOP5", "subtitle": "サプリより先にこれを食べてほしい"},
        {"type": "list", "heading": "TOP ①〜②", "items": ["みそ汁（毎朝1杯で腸が動き出す）", "ぬか漬け・キムチ（生きた菌をそのまま摂取）"]},
        {"type": "list", "heading": "TOP ③〜④", "items": ["納豆（ナットウキナーゼ＋食物繊維）", "玄米（腸内環境を整える不溶性食物繊維）"]},
        {"type": "list", "heading": "TOP ⑤", "items": ["緑茶（カテキンで腸の悪玉菌を抑制）", "→ 1日2杯から始めると効果を感じやすい"]},
        {"type": "cta", "text": "保存して\n今日の食事から取り入れてね", "sub": "プロフィールのnoteに\n改善の全工程をまとめています"}
      ]
    },
    {
      "id": 6,
      "caption": "朝のルーティンで肌荒れを悪化させていませんか。\n保存して明日の朝から見直してください。\n\n#肌荒れ #大人ニキビ #スキンケア #腸活 #美肌習慣 #肌改善 #敏感肌 #ニキビ #肌荒れ改善",
      "slides": [
        {"type": "cover", "title": "肌荒れを悪化させる\n朝のNGルーティン5つ", "subtitle": "よかれと思ってやっていることが原因かも"},
        {"type": "list", "heading": "NG ①〜②", "items": ["起きてすぐコーヒー（胃腸に負担＋血糖急上昇）", "甘いヨーグルトを「腸活」として食べる"]},
        {"type": "list", "heading": "NG ③〜④", "items": ["朝食にパン・シリアル（血糖スパイク）", "洗顔フォームをゴシゴシ（皮脂を取りすぎ）"]},
        {"type": "list", "heading": "NG ⑤", "items": ["日焼け止めを忘れる", "→ 紫外線で炎症が悪化し、ニキビ跡が濃くなる"]},
        {"type": "cta", "text": "保存して\n明日の朝から確認してね", "sub": "プロフィールのnoteに\n改善の全工程をまとめています"}
      ]
    },
    {
      "id": 7,
      "caption": "スキンケアを減らしたら逆に肌が良くなりました。\n保存して試してみてください。\n\n#肌荒れ #大人ニキビ #スキンケア #腸活 #美肌習慣 #肌改善 #敏感肌 #ニキビ #肌荒れ改善",
      "slides": [
        {"type": "cover", "title": "スキンケアを\n引き算したら起きた変化", "subtitle": "足すより引く。これが逆転の発想"},
        {"type": "comparison", "heading": "洗顔回数", "left": "1日3回＋洗顔フォーム", "right": "夜1回のみ（ぬるま水で朝洗顔）"},
        {"type": "comparison", "heading": "保湿アイテム", "left": "美容液5種類を重ねる", "right": "シンプルな化粧水1本だけ"},
        {"type": "comparison", "heading": "結果", "left": "乾燥→追加保湿→毛穴詰まりのループ", "right": "2週間で皮脂バランスが安定した"},
        {"type": "cta", "text": "保存して\n引き算スキンケアを試してね", "sub": "プロフィールのnoteに\n改善の全工程をまとめています"}
      ]
    },
    {
      "id": 8,
      "caption": "亜鉛不足は肌荒れの原因の一つです。\nサプリより先に食事から補える食べ物を知ってください。\n保存してください。\n\n#肌荒れ #大人ニキビ #スキンケア #腸活 #美肌習慣 #肌改善 #敏感肌 #ニキビ #肌荒れ改善",
      "slides": [
        {"type": "cover", "title": "亜鉛が摂れる食べ物\nランキングTOP5", "subtitle": "肌の修復に必要なミネラルを食事で補う"},
        {"type": "list", "heading": "TOP ①〜②", "items": ["牡蠣（亜鉛含有量No.1。週1回でOK）", "牛肩ロース・赤身肉（手軽に摂りやすい）"]},
        {"type": "list", "heading": "TOP ③〜④", "items": ["高野豆腐・豆腐（植物性でも摂取可能）", "カシューナッツ・アーモンド（おやつ代わりに）"]},
        {"type": "list", "heading": "TOP ⑤", "items": ["卵（毎日1〜2個が摂取の目安）", "→ 亜鉛は肌細胞の生まれ変わりに不可欠"]},
        {"type": "cta", "text": "保存して\n今週の食事に取り入れてね", "sub": "プロフィールのnoteに\n改善の全工程をまとめています"}
      ]
    },
    {
      "id": 9,
      "caption": "睡眠の質で肌の再生速度が変わります。\n保存して今夜から取り入れてください。\n\n#肌荒れ #大人ニキビ #スキンケア #腸活 #美肌習慣 #肌改善 #敏感肌 #ニキビ #肌荒れ改善",
      "slides": [
        {"type": "cover", "title": "睡眠で肌を整える\n4つのルール", "subtitle": "高い美容液より、良い眠りが肌を作る"},
        {"type": "list", "heading": "ルール ①〜②", "items": ["就寝は23時まで（成長ホルモンの分泌ピークに間に合わせる）", "寝る30分前にスマホをやめる（ブルーライトで眠りが浅くなる）"]},
        {"type": "list", "heading": "ルール ③〜④", "items": ["寝る直前の食事をやめる（内臓が休めず睡眠が浅くなる）", "室温を18〜22℃に保つ（深部体温が下がると深眠りになる）"]},
        {"type": "list", "heading": "睡眠改善の順番", "items": ["まず就寝時間を固定（23時）", "次にスマホオフの習慣", "慣れたら食事と室温を調整"]},
        {"type": "cta", "text": "保存して\n今夜から1つだけ試してね", "sub": "プロフィールのnoteに\n改善の全工程をまとめています"}
      ]
    },
    {
      "id": 10,
      "caption": "グルテンをやめたら肌に変化が起きました。\n試した人だけが知る変化を共有します。\n保存してください。\n\n#肌荒れ #大人ニキビ #スキンケア #腸活 #美肌習慣 #肌改善 #敏感肌 #ニキビ #肌荒れ改善",
      "slides": [
        {"type": "cover", "title": "グルテンをやめて\n1ヶ月で起きた変化", "subtitle": "小麦が肌に与える影響は想像以上だった"},
        {"type": "list", "heading": "1〜2週間目の変化", "items": ["便通がスムーズになってきた", "お腹のハリが少し和らいだ"]},
        {"type": "list", "heading": "3〜4週間目の変化", "items": ["頬の赤みが落ち着いてきた", "新しいニキビができる頻度が減った"]},
        {"type": "list", "heading": "1ヶ月後の感想", "items": ["完全禁止じゃなくて週2→週1に減らしただけ", "パンをやめたくない人は「量を減らす」から始めると続く"]},
        {"type": "cta", "text": "保存して\nグルテンを1週間減らしてみてね", "sub": "プロフィールのnoteに\n改善の全工程をまとめています"}
      ]
    },
    {
      "id": 11,
      "caption": "大人ニキビには4つのタイプがあります。\nタイプを間違えると効果がでません。\n保存して自分のタイプを確認してください。\n\n#肌荒れ #大人ニキビ #スキンケア #腸活 #美肌習慣 #肌改善 #敏感肌 #ニキビ #肌荒れ改善",
      "slides": [
        {"type": "cover", "title": "大人ニキビが治らない\n4つのタイプ別原因", "subtitle": "一括りの対策では治らない理由はここにある"},
        {"type": "list", "heading": "タイプA・B", "items": ["A：皮脂過多型（Tゾーンテカる・甘いもの好き）→ 糖質を減らすと変化が出やすい", "B：腸荒れ型（パン主食・便通不調）→ 腸活と食事改善が最優先"]},
        {"type": "list", "heading": "タイプC・D", "items": ["C：ホルモン乱れ型（生理前悪化・夜更かし）→ 睡眠と血糖コントロールが鍵", "D：ストレス型（頬の赤み・食いしばり）→ マグネシウム摂取と副交感神経ケア"]},
        {"type": "list", "heading": "タイプ別の優先対策まとめ", "items": ["A→ 砂糖・白米を減らす", "B→ 発酵食品・食物繊維", "C→ 就寝時間の固定", "D→ マグネシウムと深呼吸習慣"]},
        {"type": "cta", "text": "保存して\n自分のタイプを確認してね", "sub": "プロフィールのnoteに\n改善の全工程をまとめています"}
      ]
    },
    {
      "id": 12,
      "caption": "洗顔の回数を減らしたら逆に肌が整いました。\n信じられないかもしれませんが本当の話です。\n保存してください。\n\n#肌荒れ #大人ニキビ #スキンケア #腸活 #美肌習慣 #肌改善 #敏感肌 #ニキビ #肌荒れ改善",
      "slides": [
        {"type": "cover", "title": "洗顔を減らしたら\n起きた5つの変化", "subtitle": "洗いすぎが原因だとは気づかなかった"},
        {"type": "comparison", "heading": "洗顔頻度", "left": "朝昼夜の1日3回（泡洗顔）", "right": "夜1回のみ（朝はぬるま水のみ）"},
        {"type": "list", "heading": "2週間で起きた変化", "items": ["Tゾーンのテカりが落ち着いた（皮脂の過剰分泌が収まった）", "頬の乾燥感が消えた（バリア機能が回復）", "新しいニキビができにくくなった"]},
        {"type": "list", "heading": "さらに1ヶ月後", "items": ["毛穴の詰まりが減った", "ファンデーションのノリが良くなった"]},
        {"type": "cta", "text": "保存して\n明日の朝から試してね", "sub": "プロフィールのnoteに\n改善の全工程をまとめています"}
      ]
    },
    {
      "id": 13,
      "caption": "肌改善に3ヶ月かかる理由と、正しいロードマップを共有します。\n保存してください。\n\n#肌荒れ #大人ニキビ #スキンケア #腸活 #美肌習慣 #肌改善 #敏感肌 #ニキビ #肌荒れ改善",
      "slides": [
        {"type": "cover", "title": "内側から肌を整える\n3ヶ月ロードマップ", "subtitle": "焦らなくていい。順番通りにやれば変わる"},
        {"type": "list", "heading": "1ヶ月目：土台を作る", "items": ["就寝を23時に固定する", "砂糖・白い小麦を週1以下に", "水を1日1.5L以上飲む"]},
        {"type": "list", "heading": "2ヶ月目：腸を整える", "items": ["みそ汁・納豆・ぬか漬けを毎日", "朝食に玄米か芋類を取り入れる", "スキンケアをシンプルに減らす"]},
        {"type": "list", "heading": "3ヶ月目：定着させる", "items": ["良かった習慣を週7→週5でキープ", "noteの内容と照らし合わせて振り返り", "完璧を目指さず8割続けることが勝ち"]},
        {"type": "cta", "text": "保存して\n1ヶ月目から始めてね", "sub": "プロフィールのnoteに\n改善の全工程をまとめています"}
      ]
    },
    {
      "id": 14,
      "caption": "サプリは補助です。でも正しく選べば肌に効きます。\n試した中から本当に効いたものだけを紹介します。\n保存してください。\n\n#肌荒れ #大人ニキビ #スキンケア #腸活 #美肌習慣 #肌改善 #敏感肌 #ニキビ #肌荒れ改善",
      "slides": [
        {"type": "cover", "title": "肌荒れに効いた\nサプリTOP5", "subtitle": "食事で補えない分だけ。これ以上は要らない"},
        {"type": "list", "heading": "TOP ①〜②", "items": ["亜鉛（15〜30mg/日。肌の修復を助ける）", "ビタミンD（2000IU/日。免疫と肌荒れ予防）"]},
        {"type": "list", "heading": "TOP ③〜④", "items": ["マグネシウム（夜に300mg。ストレス型ニキビに効く）", "オメガ3（EPA・DHA。抗炎症作用で肌の赤みが引く）"]},
        {"type": "list", "heading": "TOP ⑤＋注意点", "items": ["乳酸菌（善玉菌を補充。腸活の補助）", "注意：全部一気に飲まない。1種類ずつ2週間試すこと"]},
        {"type": "cta", "text": "保存して\n1種類から試してね", "sub": "プロフィールのnoteに\n改善の全工程をまとめています"}
      ]
    },
    {
      "id": 15,
      "caption": "糖質を減らしたら肌に変化が起きました。\n完全断糖じゃなくても変わります。\n保存してください。\n\n#肌荒れ #大人ニキビ #スキンケア #腸活 #美肌習慣 #肌改善 #敏感肌 #ニキビ #肌荒れ改善",
      "slides": [
        {"type": "cover", "title": "糖質を減らしたら\n肌に起きた6つの変化", "subtitle": "完全禁止じゃなくていい。「減らす」だけで変わる"},
        {"type": "list", "heading": "1〜2週間の変化", "items": ["顔のむくみが取れた（血糖スパイクが収まったため）", "皮脂のテカりが減った"]},
        {"type": "list", "heading": "3〜4週間の変化", "items": ["新しいニキビができる頻度が減った", "頬の赤みが落ち着いてきた"]},
        {"type": "list", "heading": "1〜2ヶ月の変化", "items": ["肌のキメが整ってきた", "ファンデが厚塗りしなくてよくなった"]},
        {"type": "cta", "text": "保存して\n糖質を「半分」に減らすところから始めてね", "sub": "プロフィールのnoteに\n改善の全工程をまとめています"}
      ]
    },
    {
      "id": 16,
      "caption": "ホルモンバランスの乱れが肌荒れの原因になることがあります。\n当てはまるものが多い人は要注意です。\n保存してください。\n\n#肌荒れ #大人ニキビ #スキンケア #腸活 #美肌習慣 #肌改善 #敏感肌 #ニキビ #肌荒れ改善",
      "slides": [
        {"type": "cover", "title": "ホルモンバランスが\n乱れているサインチェック", "subtitle": "肌荒れの原因がホルモンかどうか確認する"},
        {"type": "list", "heading": "チェック ①〜③", "items": ["□ 生理前に必ず肌が荒れる", "□ 夜更かしが週3回以上ある", "□ 甘いものへの強い欲求がある"]},
        {"type": "list", "heading": "チェック ④〜⑥", "items": ["□ 疲れやすく、やる気が出ない日が多い", "□ 食いしばり・歯ぎしり癖がある", "□ 便通が不規則（便秘か下痢を繰り返す）"]},
        {"type": "list", "heading": "3つ以上当てはまったら", "items": ["まず睡眠を23時就寝に固定する", "血糖値を安定させる（砂糖・白い炭水化物を減らす）", "マグネシウムを夜に補給する"]},
        {"type": "cta", "text": "保存して\nいくつ当てはまるかチェックしてね", "sub": "プロフィールのnoteに\n改善の全工程をまとめています"}
      ]
    },
    {
      "id": 17,
      "caption": "水を飲む習慣だけで肌が変わりました。\nお金をかけずにできる最初の一手です。\n保存してください。\n\n#肌荒れ #大人ニキビ #スキンケア #腸活 #美肌習慣 #肌改善 #敏感肌 #ニキビ #肌荒れ改善",
      "slides": [
        {"type": "cover", "title": "水を1日2L飲み続けて\n30日で起きた変化", "subtitle": "最もコストゼロで効いた習慣だった"},
        {"type": "list", "heading": "1週間目の変化", "items": ["甘い飲み物が自然と減った（水で代替できるようになった）", "便通が少し改善した"]},
        {"type": "list", "heading": "2〜3週間目の変化", "items": ["肌の乾燥感が和らいできた", "むくみが取れて顔がスッキリした"]},
        {"type": "list", "heading": "1ヶ月後の変化", "items": ["肌のくすみが薄くなった", "ニキビができても回復が早くなった", "水を飲まないと違和感を感じるようになった（習慣化）"]},
        {"type": "cta", "text": "保存して\n今日から水を意識して飲んでね", "sub": "プロフィールのnoteに\n改善の全工程をまとめています"}
      ]
    },
    {
      "id": 18,
      "caption": "夕食の時間を変えただけで肌が変わりました。\n試した変化を正直に共有します。\n保存してください。\n\n#肌荒れ #大人ニキビ #スキンケア #腸活 #美肌習慣 #肌改善 #敏感肌 #ニキビ #肌荒れ改善",
      "slides": [
        {"type": "cover", "title": "夜の食事を18時台に\n変えたら起きた変化", "subtitle": "食べる「量」より「時間」を変えるほうが早かった"},
        {"type": "comparison", "heading": "以前の食事時間", "left": "夜22〜23時に食事（就寝まで2時間以内）", "right": "18〜19時に食事（就寝まで4〜5時間）"},
        {"type": "list", "heading": "2週間で起きた変化", "items": ["朝起きたときの顔のむくみが消えた", "睡眠が深くなり、朝の肌のコンディションが良くなった"]},
        {"type": "list", "heading": "1ヶ月で起きた変化", "items": ["内臓が休めるようになり、腸の調子が安定した", "ニキビの回復スピードが上がった", "夜遅く食べたくなる欲求自体が減った"]},
        {"type": "cta", "text": "保存して\n今週から18時台の夕食を試してね", "sub": "プロフィールのnoteに\n改善の全工程をまとめています"}
      ]
    },
    {
      "id": 19,
      "caption": "発酵食品を毎日食べ続けたら腸が変わり、肌が変わりました。\n保存してください。\n\n#肌荒れ #大人ニキビ #スキンケア #腸活 #美肌習慣 #肌改善 #敏感肌 #ニキビ #肌荒れ改善",
      "slides": [
        {"type": "cover", "title": "発酵食品を毎日食べたら\n起きた変化TOP5", "subtitle": "サプリで腸活する前に、これを試してほしい"},
        {"type": "list", "heading": "変化 ①〜②", "items": ["便通が毎日安定するようになった", "お腹のハリ・ガスが減った"]},
        {"type": "list", "heading": "変化 ③〜④", "items": ["肌の赤みが1ヶ月で落ち着いた", "生理前の肌荒れが軽くなった"]},
        {"type": "list", "heading": "変化 ⑤＋実践方法", "items": ["気分の波が少し安定した（腸-脳-肌の連動）", "実践：みそ汁（朝）＋納豆（夜）を毎日から始める"]},
        {"type": "cta", "text": "保存して\n明日のみそ汁から始めてね", "sub": "プロフィールのnoteに\n改善の全工程をまとめています"}
      ]
    },
    {
      "id": 20,
      "caption": "難しいことは何もありません。今日からできることだけ集めました。\n保存してチェックリストとして使ってください。\n\n#肌荒れ #大人ニキビ #スキンケア #腸活 #美肌習慣 #肌改善 #敏感肌 #ニキビ #肌荒れ改善",
      "slides": [
        {"type": "cover", "title": "今日から始める\n肌改善ToDoリスト7選", "subtitle": "お金ゼロ・今すぐできるものだけ厳選"},
        {"type": "list", "heading": "ToDo ①〜③", "items": ["□ 今夜23時に布団に入る", "□ 明日の朝、コーヒーの前に水200mLを飲む", "□ 今日の昼食のパンを玄米かご飯に変える"]},
        {"type": "list", "heading": "ToDo ④〜⑤", "items": ["□ 今日の夜、みそ汁を1杯飲む", "□ 今夜のスキンケアを化粧水1本だけにする"]},
        {"type": "list", "heading": "ToDo ⑥〜⑦", "items": ["□ 就寝30分前にスマホを手の届かない場所に置く", "□ 今日の食事で「甘い飲み物」を水か緑茶に変える"]},
        {"type": "cta", "text": "保存して\n今日の1つ目から始めてね", "sub": "プロフィールのnoteに\n改善の全工程をまとめています"}
      ]
    }
  ]
}
```

- [ ] **Step 2: JSONの形式を確認する**

```bash
python3 -c "import json; data=json.load(open('skin/carousel_content.json')); print(f'テーマ数: {len(data[\"themes\"])}件')"
```

期待出力: `テーマ数: 20件`

- [ ] **Step 3: コミットする**

```bash
git add skin/carousel_content.json
git commit -m "追加: カルーセル投稿コンテンツ定義（20テーマ）"
```

---

## Task 3: skin_instagram_image_gen_v3.py を作成する

**Files:**
- 新規作成: `skin/skin_instagram_image_gen_v3.py`
- 新規作成: `skin/skin_instagram_carousels/`（スクリプト実行時に自動作成）

- [ ] **Step 1: テストを書く**

`tests/test_carousel.py` に以下を書く。

```python
# tests/test_carousel.py
# カルーセル生成スクリプトのテスト

import json
import os
import pytest


def test_carousel_content_json_structure():
    """carousel_content.json の形式が正しいことを確認する"""
    # skin/carousel_content.json を読み込む
    json_path = os.path.join(os.path.dirname(__file__), '..', 'skin', 'carousel_content.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    assert 'themes' in data
    assert len(data['themes']) == 20  # 20テーマあること

    for theme in data['themes']:
        assert 'id' in theme
        assert 'caption' in theme
        assert 'slides' in theme
        assert len(theme['slides']) == 5  # 各テーマ5枚あること
        assert theme['slides'][0]['type'] == 'cover'  # 1枚目はカバー
        assert theme['slides'][-1]['type'] == 'cta'   # 最後はCTA


def test_carousel_content_no_empty_fields():
    """各スライドに空のフィールドがないことを確認する"""
    json_path = os.path.join(os.path.dirname(__file__), '..', 'skin', 'carousel_content.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for theme in data['themes']:
        assert theme['caption'].strip() != ''
        for slide in theme['slides']:
            assert slide.get('type', '').strip() != ''
```

- [ ] **Step 2: テストを実行して失敗することを確認する（まだファイルがないので通る）**

```bash
cd /home/kenta_kamijyo && python3 -m pytest tests/test_carousel.py -v
```

期待出力: `2 passed`（carousel_content.json は Task 2 で作成済みのため通る）

- [ ] **Step 3: 画像生成スクリプトを作成する**

`skin/skin_instagram_image_gen_v3.py` に以下を書く。

```python
# skin_instagram_image_gen_v3.py
# カルーセル投稿用の画像をHTML→PNG方式で一括生成するスクリプト
# 使い方: python3 skin/skin_instagram_image_gen_v3.py
# ※ローカル環境でのみ実行する（GitHub Actionsでは不要）

import json  # JSONファイルを読み込む道具
import os    # ファイルパスを扱う道具

from playwright.sync_api import sync_playwright  # HTML→PNGに変換する道具


# =============================
# 設定
# =============================
SCRIPT_DIR    = os.path.dirname(__file__)                                  # このスクリプトの場所
CONTENT_FILE  = os.path.join(SCRIPT_DIR, 'carousel_content.json')          # テーマ定義ファイル
OUTPUT_DIR    = os.path.join(SCRIPT_DIR, 'skin_instagram_carousels')        # 画像の出力先
IMAGE_SIZE    = 1080                                                         # Instagram推奨サイズ（正方形）

# デザインカラー
COLOR_BG      = '#0f0f0f'   # 背景（ほぼ黒）
COLOR_TEXT    = '#f0ede8'   # メインテキスト（温かみのある白）
COLOR_ACCENT  = '#c8a97e'   # アクセント（ゴールドベージュ）
COLOR_SUB     = '#888888'   # サブテキスト（グレー）
ACCOUNT_NAME  = '@skin_reform_jp'  # アカウント名（必要に応じて変更）


# =============================
# HTMLテンプレート生成
# =============================

def make_base_html(body_content: str) -> str:
    """全スライド共通のHTMLラッパーを作る"""
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap" rel="stylesheet">
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      width: {IMAGE_SIZE}px;
      height: {IMAGE_SIZE}px;
      background: {COLOR_BG};
      font-family: 'Noto Sans JP', 'Hiragino Kaku Gothic ProN', 'Meiryo', sans-serif;
      color: {COLOR_TEXT};
      overflow: hidden;
    }}
  </style>
</head>
<body>
{body_content}
</body>
</html>"""


def make_cover_html(title: str, subtitle: str) -> str:
    """カバー（1枚目）スライドのHTMLを作る"""
    title_escaped    = title.replace('\n', '<br>')
    subtitle_escaped = subtitle.replace('\n', '<br>')
    return make_base_html(f"""
<div style="width:100%; height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:80px; position:relative;">
  <div style="width:60px; height:5px; background:{COLOR_ACCENT}; margin-bottom:50px;"></div>
  <h1 style="font-size:68px; font-weight:900; line-height:1.5; text-align:center; letter-spacing:2px;">{title_escaped}</h1>
  <p style="font-size:28px; color:{COLOR_SUB}; margin-top:40px; text-align:center; line-height:1.6;">{subtitle_escaped}</p>
  <div style="position:absolute; bottom:50px; display:flex; align-items:center; gap:12px;">
    <div style="width:40px; height:2px; background:{COLOR_ACCENT};"></div>
    <p style="color:{COLOR_ACCENT}; font-size:22px;">{ACCOUNT_NAME}</p>
    <div style="width:40px; height:2px; background:{COLOR_ACCENT};"></div>
  </div>
</div>""")


def make_list_html(slide_num: int, heading: str, items: list) -> str:
    """リスト形式スライドのHTMLを作る"""
    items_html = ''
    for item in items:
        item_escaped = item.replace('\n', '<br>')
        items_html += f"""
    <div style="display:flex; align-items:flex-start; margin-bottom:36px;">
      <span style="color:{COLOR_ACCENT}; font-size:28px; min-width:40px; margin-top:4px;">▶</span>
      <p style="font-size:34px; line-height:1.6; color:{COLOR_TEXT};">{item_escaped}</p>
    </div>"""

    return make_base_html(f"""
<div style="width:100%; height:100%; padding:70px 80px; position:relative; display:flex; flex-direction:column; justify-content:center;">
  <p style="color:{COLOR_ACCENT}; font-size:22px; margin-bottom:24px;">{slide_num} / 5</p>
  <h2 style="font-size:38px; font-weight:700; border-left:5px solid {COLOR_ACCENT}; padding-left:20px; margin-bottom:50px; line-height:1.5;">{heading}</h2>
  <div>{items_html}</div>
  <p style="position:absolute; bottom:40px; right:80px; color:{COLOR_SUB}; font-size:20px;">{ACCOUNT_NAME}</p>
</div>""")


def make_comparison_html(slide_num: int, heading: str, left: str, right: str) -> str:
    """比較形式スライドのHTMLを作る"""
    left_escaped  = left.replace('\n', '<br>')
    right_escaped = right.replace('\n', '<br>')
    return make_base_html(f"""
<div style="width:100%; height:100%; padding:70px 80px; display:flex; flex-direction:column; justify-content:center; position:relative;">
  <p style="color:{COLOR_ACCENT}; font-size:22px; margin-bottom:24px;">{slide_num} / 5</p>
  <h2 style="font-size:38px; font-weight:700; border-left:5px solid {COLOR_ACCENT}; padding-left:20px; margin-bottom:50px;">{heading}</h2>
  <div style="display:flex; gap:30px; align-items:stretch;">
    <div style="flex:1; background:#1e1e1e; border-radius:16px; padding:40px; border:2px solid #333;">
      <p style="color:#ff6b6b; font-size:22px; margin-bottom:16px; font-weight:700;">❌ 以前</p>
      <p style="font-size:30px; line-height:1.6;">{left_escaped}</p>
    </div>
    <div style="width:4px; background:{COLOR_ACCENT}; border-radius:4px; align-self:stretch;"></div>
    <div style="flex:1; background:#1e1e1e; border-radius:16px; padding:40px; border:2px solid {COLOR_ACCENT};">
      <p style="color:{COLOR_ACCENT}; font-size:22px; margin-bottom:16px; font-weight:700;">✅ 今</p>
      <p style="font-size:30px; line-height:1.6;">{right_escaped}</p>
    </div>
  </div>
  <p style="position:absolute; bottom:40px; right:80px; color:{COLOR_SUB}; font-size:20px;">{ACCOUNT_NAME}</p>
</div>""")


def make_cta_html(text: str, sub: str) -> str:
    """CTA（最終スライド）のHTMLを作る"""
    text_escaped = text.replace('\n', '<br>')
    sub_escaped  = sub.replace('\n', '<br>')
    return make_base_html(f"""
<div style="width:100%; height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:80px; text-align:center;">
  <p style="font-size:60px; margin-bottom:30px;">🔖</p>
  <h2 style="font-size:56px; font-weight:900; line-height:1.6; margin-bottom:40px;">{text_escaped}</h2>
  <div style="width:80px; height:3px; background:{COLOR_ACCENT}; margin-bottom:40px;"></div>
  <p style="font-size:28px; color:{COLOR_SUB}; line-height:1.8;">{sub_escaped}</p>
  <p style="font-size:24px; color:{COLOR_ACCENT}; margin-top:50px;">{ACCOUNT_NAME}</p>
</div>""")


def slide_to_html(slide: dict, slide_num: int) -> str:
    """スライドの種類に応じてHTMLを選ぶ"""
    slide_type = slide['type']
    if slide_type == 'cover':
        return make_cover_html(slide['title'], slide.get('subtitle', ''))
    elif slide_type == 'list':
        return make_list_html(slide_num, slide['heading'], slide['items'])
    elif slide_type == 'comparison':
        return make_comparison_html(slide_num, slide['heading'], slide['left'], slide['right'])
    elif slide_type == 'cta':
        return make_cta_html(slide['text'], slide.get('sub', ''))
    else:
        raise ValueError(f"未知のスライドタイプ: {slide_type}")


# =============================
# 画像生成メイン処理
# =============================

def generate_all_images():
    """全テーマのカルーセル画像を一括生成する"""
    # 出力ディレクトリを作る（なければ作成）
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # コンテンツ定義ファイルを読み込む
    with open(CONTENT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    themes = data['themes']
    print(f"=== カルーセル画像生成開始（{len(themes)}テーマ × 5枚 = {len(themes)*5}枚）===")

    # playwright でブラウザを起動する（画面なしのヘッドレスモード）
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page    = browser.new_page(viewport={'width': IMAGE_SIZE, 'height': IMAGE_SIZE})

        for theme in themes:
            theme_id = theme['id']
            slides   = theme['slides']
            print(f"テーマ{theme_id:02d} 生成中...")

            for slide_num, slide in enumerate(slides, start=1):
                # HTMLを生成する
                html_content = slide_to_html(slide, slide_num)

                # ブラウザにHTMLを読み込む
                page.set_content(html_content, wait_until='networkidle')

                # PNGとして保存する
                output_path = os.path.join(OUTPUT_DIR, f"theme{theme_id:02d}_slide{slide_num}.png")
                page.screenshot(path=output_path, type='png')
                print(f"  ✅ slide{slide_num} → {os.path.basename(output_path)}")

        browser.close()

    print(f"=== 完了: {OUTPUT_DIR} に {len(themes)*5}枚の画像を生成しました ===")


if __name__ == '__main__':
    generate_all_images()
```

- [ ] **Step 4: コミットする**

```bash
git add skin/skin_instagram_image_gen_v3.py
git commit -m "追加: カルーセル画像生成スクリプト v3（HTML→PNG方式）"
```

---

## Task 4: カルーセル画像を一括生成する

**Files:**
- 新規作成: `skin/skin_instagram_carousels/theme01_slide1.png` 〜 `theme20_slide5.png`（計100枚）

- [ ] **Step 1: 画像を生成する**

```bash
cd /home/kenta_kamijyo && python3 skin/skin_instagram_image_gen_v3.py
```

期待出力（最後の行）:
```
=== 完了: /home/kenta_kamijyo/skin/skin_instagram_carousels に 100枚の画像を生成しました ===
```

- [ ] **Step 2: 生成枚数を確認する**

```bash
ls skin/skin_instagram_carousels/ | wc -l
```

期待出力: `100`

- [ ] **Step 3: 画像サイズを確認する**

```bash
python3 -c "
from PIL import Image
import os
path = 'skin/skin_instagram_carousels/theme01_slide1.png'
img = Image.open(path)
print(f'サイズ: {img.size}')  # (1080, 1080) であること
"
```

期待出力: `サイズ: (1080, 1080)`

- [ ] **Step 4: theme01〜03の各スライドを目視確認する（任意）**

```bash
# WSL2でWindowsのエクスプローラーを開いて確認する
explorer.exe skin/skin_instagram_carousels
```

---

## Task 5: カルーセル画像をコミットする

**Files:**
- `skin/skin_instagram_carousels/`（100枚を追加）

- [ ] **Step 1: .gitignore に除外設定がないことを確認する**

```bash
grep -r "skin_instagram_carousels" .gitignore 2>/dev/null || echo "除外設定なし"
```

- [ ] **Step 2: 画像をステージングしてコミットする**

```bash
git add skin/skin_instagram_carousels/
git commit -m "追加: カルーセル投稿用画像100枚（20テーマ×5枚）"
```

- [ ] **Step 3: GitHubにプッシュする**

```bash
git push
```

- [ ] **Step 4: GitHub上でURLが正しく機能することを確認する**

```bash
curl -o /dev/null -s -w "%{http_code}" \
  "https://raw.githubusercontent.com/kmkn0523-cell/kenta-learning/main/skin/skin_instagram_carousels/theme01_slide1.png"
```

期待出力: `200`

---

## Task 6: skin_instagram_auto_post.py をカルーセル対応に改修する

**Files:**
- 変更: `skin/skin_instagram_auto_post.py`

- [ ] **Step 1: カルーセルAPIの関数を追加するテストを書く**

`tests/test_carousel.py` に以下を追記する。

```python
from unittest.mock import patch, MagicMock
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skin'))


def test_build_carousel_image_urls():
    """テーマIDからカルーセル画像URLが5件生成されることを確認する"""
    # skin_instagram_auto_post からインポートする
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "auto_post",
        os.path.join(os.path.dirname(__file__), '..', 'skin', 'skin_instagram_auto_post.py')
    )
    mod = importlib.util.load_from_spec(spec)
    spec.loader.exec_module(mod)

    urls = mod.build_carousel_image_urls(theme_id=1)
    assert len(urls) == 5
    assert urls[0].endswith('theme01_slide1.png')
    assert urls[4].endswith('theme01_slide5.png')
    assert all('raw.githubusercontent.com' in url for url in urls)
```

- [ ] **Step 2: テストを実行して失敗することを確認する**

```bash
cd /home/kenta_kamijyo && python3 -m pytest tests/test_carousel.py::test_build_carousel_image_urls -v
```

期待出力: `FAILED`（まだ関数がないため）

- [ ] **Step 3: skin_instagram_auto_post.py にカルーセル対応を追加する**

`skin/skin_instagram_auto_post.py` の以下の部分を変更する。

**① GITHUB_RAW_BASE の変更（23行目付近）:**

変更前:
```python
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/kmkn0523-cell/kenta-learning/main/skin/skin_images"
```

変更後:
```python
GITHUB_RAW_BASE          = "https://raw.githubusercontent.com/kmkn0523-cell/kenta-learning/main/skin/skin_images"
GITHUB_CAROUSEL_BASE     = "https://raw.githubusercontent.com/kmkn0523-cell/kenta-learning/main/skin/skin_instagram_carousels"
CAROUSEL_CONTENT_FILE    = os.path.join(os.path.dirname(__file__), "carousel_content.json")
SLIDES_PER_CAROUSEL      = 5   # 1投稿あたりのスライド枚数
```

**② POSTS_FILE の参照先を変更（26行目付近）:**

変更前:
```python
POSTS_FILE    = os.path.join(os.path.dirname(__file__), "skin_threads_posts.json")      # 投稿データ
```

変更後:
```python
POSTS_FILE    = os.path.join(os.path.dirname(__file__), "skin_threads_posts.json")      # 投稿データ（旧）
```

**③ 以下の関数を `create_media_container` 関数の前に追加する:**

```python
# =============================
# カルーセルコンテンツの読み込み
# =============================

def load_carousel_content():
    """carousel_content.json からカルーセルテーマ定義を読み込む"""
    try:
        with open(CAROUSEL_CONTENT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['themes']
    except FileNotFoundError:
        print("❌ carousel_content.json が見つかりません")
        return []
    except json.JSONDecodeError:
        print("❌ carousel_content.json の形式が正しくありません")
        return []


def build_carousel_image_urls(theme_id: int) -> list:
    """テーマIDからカルーセル画像のURL一覧を作る（5枚分）"""
    return [
        f"{GITHUB_CAROUSEL_BASE}/theme{theme_id:02d}_slide{i}.png"
        for i in range(1, SLIDES_PER_CAROUSEL + 1)
    ]


# =============================
# カルーセル投稿API処理
# =============================

def create_child_container(image_url: str) -> str:
    """
    カルーセルの子コンテナを作る（1枚ずつ登録する）
    カルーセルは：子コンテナ×N枚 → カルーセルコンテナ → 公開 の順で処理する
    """
    url    = f"https://graph.facebook.com/v19.0/{USER_ID}/media"
    params = {
        "image_url":        image_url,
        "is_carousel_item": "true",   # カルーセルの子要素として登録する指定
        "access_token":     ACCESS_TOKEN,
    }
    try:
        response = requests.post(url, params=params, timeout=30)
        data     = response.json()
        if "id" in data:
            return data["id"]
        print(f"❌ 子コンテナ作成失敗: {data}")
        return ""
    except Exception as e:
        print(f"❌ 子コンテナ作成エラー: {e}")
        return ""


def create_carousel_container(child_ids: list, caption: str) -> str:
    """
    カルーセルコンテナを作る（子コンテナIDをまとめて渡す）
    """
    url    = f"https://graph.facebook.com/v19.0/{USER_ID}/media"
    params = {
        "media_type":   "CAROUSEL",
        "children":     ",".join(child_ids),  # カンマ区切りの子コンテナID一覧
        "caption":      caption,
        "access_token": ACCESS_TOKEN,
    }
    try:
        response = requests.post(url, params=params, timeout=30)
        data     = response.json()
        if "id" in data:
            return data["id"]
        print(f"❌ カルーセルコンテナ作成失敗: {data}")
        return ""
    except Exception as e:
        print(f"❌ カルーセルコンテナ作成エラー: {e}")
        return ""
```

**④ main() 関数の投稿処理部分を差し替える（`# 投稿データを読み込む` から末尾まで）:**

変更前:
```python
    # 投稿データを読み込む
    threads = load_threads()
    if not threads:
        print("❌ 投稿データが読み込めませんでした。終了します。")
        sys.exit(1)

    # 前回の進捗を読み込む（全テーマをループ）
    progress      = load_progress()
    current_index = progress["next_index"] % len(threads)
    thread        = threads[current_index]
    theme_id      = thread["id"]
    theme_name    = thread["theme"]

    # キャプションを組み立てる（フックテキスト + CTA + ハッシュタグ）
    hook_text = thread["posts"][0]                # 1投稿目（フック）をキャプションに使う
    caption   = hook_text + CTA + HASHTAGS

    # 画像URLを組み立てる（Threads自動投稿と同じ.jpg形式）
    image_filename = f"theme{theme_id:02d}.jpg"
    image_url      = f"{GITHUB_RAW_BASE}/{image_filename}"

    print(f"📌 テーマ: {theme_name}（index={current_index}）")
    print(f"🖼️  画像URL: {image_url}")
    print(f"📝 キャプション（先頭100文字）: {caption[:100]}...")

    # Step1: メディアコンテナを作成
    print("📤 Step1: メディアコンテナ作成中...")
    container_result = create_media_container(image_url, caption)

    if "id" not in container_result:
        print(f"❌ メディアコンテナ作成失敗: {container_result}")
        sys.exit(1)

    creation_id = container_result["id"]
    print(f"✅ コンテナID取得: {creation_id}")

    # 画像処理の完了を確認してから公開（最大120秒）
    print("⏳ 画像処理完了を確認中...")
    if not wait_for_container_ready(creation_id):
        print("❌ コンテナが処理完了しなかったため投稿を中止します")
        sys.exit(1)

    # Step2: 投稿を公開
    print("📤 Step2: 投稿を公開中...")
    publish_result = publish_media(creation_id)

    if "id" not in publish_result:
        print(f"❌ 投稿公開失敗: {publish_result}")
        sys.exit(1)

    print(f"✅ 投稿成功！投稿ID: {publish_result['id']}")

    # 次回の進捗を保存
    next_index = current_index + 1
    save_progress(next_index)
    next_theme = threads[next_index % len(threads)]["theme"]
    print(f"📊 次回: {next_theme}（index={next_index % len(threads)}）")
    print("=== 完了 ===")
```

変更後:
```python
    # カルーセルコンテンツを読み込む
    themes = load_carousel_content()
    if not themes:
        print("❌ carousel_content.json が読み込めませんでした。終了します。")
        sys.exit(1)

    # 前回の進捗を読み込む（全テーマをループ）
    progress      = load_progress()
    current_index = progress["next_index"] % len(themes)
    theme         = themes[current_index]
    theme_id      = theme["id"]
    caption       = theme["caption"]

    print(f"📌 テーマ{theme_id:02d}（index={current_index}）")

    # カルーセル画像のURLを5枚分作る
    image_urls = build_carousel_image_urls(theme_id)
    print(f"🖼️  スライド画像: {len(image_urls)}枚")

    # Step1: 各スライドの子コンテナを作る
    print("📤 Step1: 子コンテナを作成中...")
    child_ids = []
    for i, url in enumerate(image_urls, start=1):
        print(f"  スライド{i}: {os.path.basename(url)}")
        child_id = create_child_container(url)
        if not child_id:
            print(f"❌ スライド{i}の子コンテナ作成に失敗しました")
            sys.exit(1)
        child_ids.append(child_id)
        time.sleep(2)  # API制限を避けるため少し待つ

    print(f"✅ 子コンテナ{len(child_ids)}件 作成完了")

    # Step2: カルーセルコンテナを作る
    print("📤 Step2: カルーセルコンテナを作成中...")
    carousel_id = create_carousel_container(child_ids, caption)
    if not carousel_id:
        print("❌ カルーセルコンテナ作成に失敗しました")
        sys.exit(1)
    print(f"✅ カルーセルコンテナID: {carousel_id}")

    # カルーセルの処理完了を待つ
    print("⏳ カルーセル処理完了を確認中...")
    if not wait_for_container_ready(carousel_id):
        print("❌ カルーセルが処理完了しなかったため投稿を中止します")
        sys.exit(1)

    # Step3: 投稿を公開する
    print("📤 Step3: 投稿を公開中...")
    publish_result = publish_media(carousel_id)
    if "id" not in publish_result:
        print(f"❌ 投稿公開失敗: {publish_result}")
        sys.exit(1)

    print(f"✅ カルーセル投稿成功！投稿ID: {publish_result['id']}")

    # 次回の進捗を保存する
    next_index = current_index + 1
    save_progress(next_index)
    print(f"📊 次回テーマ: {themes[next_index % len(themes)]['id']:02d}（index={next_index % len(themes)}）")
    print("=== 完了 ===")
```

- [ ] **Step 4: テストを実行して通ることを確認する**

```bash
cd /home/kenta_kamijyo && python3 -m pytest tests/test_carousel.py -v
```

期待出力: `3 passed`

- [ ] **Step 5: コミットする**

```bash
git add skin/skin_instagram_auto_post.py tests/test_carousel.py
git commit -m "変更: skin Instagram投稿をカルーセル形式に対応"
```

---

## Task 7: 進捗ファイルをリセットしてプッシュする

**Files:**
- 変更: `skin/skin_instagram_progress.json`

- [ ] **Step 1: 進捗をリセットする**

```bash
echo '{"next_index": 0}' > skin/skin_instagram_progress.json
```

- [ ] **Step 2: 確認する**

```bash
cat skin/skin_instagram_progress.json
```

期待出力: `{"next_index": 0}`

- [ ] **Step 3: コミット＆プッシュする**

```bash
git add skin/skin_instagram_progress.json
git commit -m "リセット: skin Instagram進捗をカルーセル運用向けに初期化"
git push
```

---

## Task 8: GitHub Actions で手動テストする

- [ ] **Step 1: GitHub Actions の手動トリガーを実行する**

GitHubリポジトリの `Actions` タブ → `skin Instagram自動投稿` → `Run workflow` をクリックする

- [ ] **Step 2: ログを確認する**

以下が出力されていれば成功。

```
📌 テーマ01（index=0）
🖼️  スライド画像: 5枚
📤 Step1: 子コンテナを作成中...
  スライド1: theme01_slide1.png
  ...
✅ 子コンテナ5件 作成完了
📤 Step2: カルーセルコンテナを作成中...
✅ カルーセルコンテナID: ...
📤 Step3: 投稿を公開中...
✅ カルーセル投稿成功！投稿ID: ...
```

- [ ] **Step 3: Instagramアプリで投稿を確認する**

投稿がカルーセル（スワイプできる）形式になっていることを目視確認する。

---

## コメント活動ガイド（手動・毎日15分）

自動化とは別に、以下を毎日手動で行う。

**①対象アカウントを探す（初回のみ）**

Instagramで `#大人ニキビ` `#肌荒れ改善` を検索し、フォロワー1,000〜30,000のアカウントを10個リスト化する。

**②毎日のコメント（1日5〜10件）**

- 3行以上で自分の体験談を入れる
- NG：「勉強になりました！」
- OK：「これ本当にそうですよね。自分も小麦を週1に減らしてから2ヶ月で頬の赤みが引きました」
