# skin Threads ツリー投稿 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** skinアカウントのThreads自動投稿を単体投稿からツリー構造（3本連鎖）に変更する

**Architecture:** 新しい投稿データファイル `skin/skin_threads_posts.json` を作成し（14セット×3本）、`skin/skin_threads_action.py` を改修してリプライ連鎖投稿に対応させる。既存の `skin_x_posts.json` や GitHub Actions ワークフローは変更しない。

**Tech Stack:** Python 3, Threads Graph API（`reply_to_id` パラメータ）, JSON, GitHub Actions

---

## ファイル構成

| 操作 | ファイル | 役割 |
|---|---|---|
| 新規作成 | `skin/skin_threads_posts.json` | 14セット×3本のツリー投稿データ |
| 変更 | `skin/skin_threads_action.py` | ツリー投稿対応の自動投稿スクリプト |
| 変更なし | `skin/skin_x_posts.json` | 既存投稿データ（触れない） |
| 変更なし | `skin/skin_threads_progress.json` | 進捗管理（daily_index をそのまま使う） |
| 変更なし | `.github/workflows/*.yml` | GitHub Actionsワークフロー |

---

## Task 1: skin_threads_posts.json を作成する

**Files:**
- Create: `skin/skin_threads_posts.json`

- [ ] **Step 1: ファイルを作成する**

`skin/skin_threads_posts.json` を以下の内容で作成する。
（各本は500文字以内、ハッシュタグは本3に付けずスクリプト側で付与する）

```json
{
  "threads": [
    {
      "id": 1,
      "theme": "問いかけ型",
      "posts": [
        "肌荒れが治らない人、これ全員やってます。\n\n□ 甘い飲み物を毎日飲んでる\n□ 就寝が深夜0時以降\n□ パン・麺が毎日の主食\n□ ストレスで食いしばり癖がある\n□ 便秘または下痢がち\n\n何個当てはまりましたか？\n\n3個以上なら、スキンケアより先に変えるべきことがあります。",
        "3個以上当てはまった人へ。\n\nそれらは全部「腸の炎症」を引き起こす習慣です。\n\n腸が荒れる\n→ 有害物質が血液に漏れ出す\n→ 全身で炎症が起きる\n→ 肌に出る\n\nスキンケアで表面を整えても、腸から炎症が出続ける限り治りません。\n\nまず変えるべき3つ：\n① 甘い飲み物をお茶に替える\n② 就寝を23時前にする\n③ パンを週3回以下にする\n\nこれだけで2週間後に変化を感じる人が多いです。",
        "この投稿、保存しておくと◎\n\n毎日1つ、肌荒れを改善するヒントを投稿しています。\nフォローするとタイムラインに届きます。"
      ]
    },
    {
      "id": 2,
      "theme": "腸と肌のつながり",
      "posts": [
        "「腸と肌はつながっている」\n\nこれ、科学的に証明されています。\n\n腸内環境が乱れると肌が荒れる。\n肌が荒れているなら、腸を見直すべき。\n\nスキンケアだけで治らない理由は、ここにあります。",
        "腸と肌がつながる仕組み。\n\n①腸内の悪玉菌が増える\n②腸壁に炎症が起きる（リーキーガット）\n③有害物質が血液に漏れ出す\n④肌に炎症として現れる→ニキビ・赤み・乾燥\n\nこの流れを断ち切るには腸内環境を整えること。\n\n腸に良い食べ物：\n・発酵食品（納豆・味噌・ヨーグルト）\n・食物繊維（野菜・きのこ・豆）\n・水（甘い飲み物の代わりに）\n\n逆に腸を荒らすもの：\n・砂糖・白米・小麦の大量摂取\n・アルコール\n・睡眠不足",
        "この投稿、保存しておくと◎\n\n毎日1つ、肌荒れを改善するヒントを投稿しています。\nフォローするとタイムラインに届きます。"
      ]
    },
    {
      "id": 3,
      "theme": "砂糖とニキビ",
      "posts": [
        "ニキビの本当の原因、砂糖だった。\n\n「甘いものが好き」と「肌が治らない」はほぼセットです。\n\nでも、なぜ砂糖がニキビを作るのか。\nその仕組みを知ると、やめたくなります。",
        "砂糖とニキビの仕組み。\n\n①糖質を摂りすぎる\n②血糖値が急上昇する\n③体がインスリンを大量に分泌する\n④インスリンが皮脂の分泌を増やす\n⑤毛穴が詰まり、ニキビになる\n\nさらに砂糖は腸内の悪玉菌のエサにもなる。\n腸が荒れる→炎症が肌に出る、のダブルパンチ。\n\nまず試すこと：\n・ジュース→お茶に替える\n・おやつ→ナッツや果物に替える\n・甘いヨーグルト→無糖に替える\n\n2週間試すだけで違いが出ます。",
        "この投稿、保存しておくと◎\n\n毎日1つ、肌荒れを改善するヒントを投稿しています。\nフォローするとタイムラインに届きます。"
      ]
    },
    {
      "id": 4,
      "theme": "洗顔のやりすぎ",
      "posts": [
        "「念入りに洗顔してるのに肌が荒れる」\n\nそれ、洗いすぎです。\n\n1日3回以上洗顔している人、逆効果になっている可能性があります。",
        "洗いすぎると肌が荒れる仕組み。\n\n①洗いすぎで必要な皮脂まで落とす\n②肌が「皮脂が足りない」と感じる\n③皮脂を過剰に分泌する（代償性皮脂分泌）\n④毛穴が詰まり、ニキビが悪化する\n\n正しい洗顔：\n・1日2回（朝・夜）まで\n・朝は水かぬるま湯だけでもOK\n・ゴシゴシこすらない、泡でやさしく包む\n・洗い流しはぬるま湯で\n\n高い洗顔料より、回数と方法が大事です。",
        "この投稿、保存しておくと◎\n\n毎日1つ、肌荒れを改善するヒントを投稿しています。\nフォローするとタイムラインに届きます。"
      ]
    },
    {
      "id": 5,
      "theme": "睡眠と肌",
      "posts": [
        "夜11時前に寝るだけで、肌が変わります。\n\n「睡眠と肌の関係」を知っている人は多い。\nでも実際に何が起きているのかを知ると、早く寝たくなります。",
        "睡眠中に起きていること。\n\n眠ると「成長ホルモン」が分泌される。\nこのホルモンが肌を修復・再生する。\n\n特に深い睡眠（ノンレム睡眠）が始まる\n就寝後30〜60分が最もホルモンが出る。\n\nつまり、遅く寝るほど修復時間が短くなる。\n\n睡眠の質を上げる3つのこと：\n① 就寝30分前にスマホをやめる\n② 夜8時以降はカフェインを避ける\n③ 寝る前に白湯を飲む（内臓を温める）\n\nお金ゼロで肌が変わる最強の対策です。",
        "この投稿、保存しておくと◎\n\n毎日1つ、肌荒れを改善するヒントを投稿しています。\nフォローするとタイムラインに届きます。"
      ]
    },
    {
      "id": 6,
      "theme": "小麦とグルテン",
      "posts": [
        "毎日パンを食べてる人に、知ってほしいことがあります。\n\n「グルテン」が肌荒れの原因になっている可能性があります。\n\n全員じゃないけど、当てはまる人は確実にいます。",
        "グルテンと肌の話。\n\n小麦に含まれるグルテンが腸壁を刺激し、\n腸に「穴」が開きやすくなる（リーキーガット）。\n\n有害物質が血液に漏れ出す→全身で炎症→肌荒れ\n\nこの3つが重なるなら、試す価値あり：\n□ パン・麺・お菓子を毎日食べてる\n□ 腸の調子が悪い（便秘・下痢・ガス）\n□ 肌荒れが慢性的に続いてる\n\n試し方：2週間だけ小麦を減らしてみる。\n白米・そば・芋類に置き換えるだけでいい。\n\n変化を感じたら、それが原因です。",
        "この投稿、保存しておくと◎\n\n毎日1つ、肌荒れを改善するヒントを投稿しています。\nフォローするとタイムラインに届きます。"
      ]
    },
    {
      "id": 7,
      "theme": "ストレスと皮脂",
      "posts": [
        "「ストレスで肌が荒れる」は気のせいじゃない。\n\n体は正直で、ストレスを受けると即座に肌に反応します。\n\nその仕組みを知ると、ストレス管理が最高のスキンケアだとわかります。",
        "ストレスが肌を荒らす仕組み。\n\nストレスを受ける\n→「コルチゾール（ストレスホルモン）」が増える\n→ 皮脂の分泌が急増する\n→ 腸のバリアが弱くなる\n→ 炎症が起きやすくなる\n→ 睡眠の質が下がる\n\nこの全部、ニキビの直接原因です。\n\nストレスを減らす3つの方法：\n① 1日10分、何もしない時間を作る\n② 深呼吸（4秒吸って8秒吐く）を1日3回\n③ 好きなことを週1回以上やる\n\n「ストレスを減らす」は、れっきとしたスキンケアです。",
        "この投稿、保存しておくと◎\n\n毎日1つ、肌荒れを改善するヒントを投稿しています。\nフォローするとタイムラインに届きます。"
      ]
    },
    {
      "id": 8,
      "theme": "失敗談型",
      "posts": [
        "8年間、全部間違えてた。\n\n肌荒れを治したくてやってたこと、全部逆効果だったと気づいた話です。\n\n同じことしてた人、いますか？",
        "8年間やってた間違いリスト。\n\n・1日3回の洗顔（必要な皮脂まで落としてた）\n・高い美容液を重ね塗り（原因が違うから意味がない）\n・ニキビに化粧品を塗り込む（炎症が悪化する）\n・甘いヨーグルトを毎日（砂糖で腸を荒らしてた）\n・サラダチキンだけ食べる（腸活に必要な発酵食品がない）\n\n変えたこと：\n・洗顔は夜1回だけ\n・化粧品をシンプルに減らした\n・発酵食品（納豆・味噌）を毎日食べる\n・甘い飲み物をやめた\n\n変えてから2ヶ月で、8年間の悩みが解消しました。",
        "この投稿、保存しておくと◎\n\n毎日1つ、肌荒れを改善するヒントを投稿しています。\nフォローするとタイムラインに届きます。"
      ]
    },
    {
      "id": 9,
      "theme": "やめた習慣",
      "posts": [
        "やめたら肌が変わった、7つの習慣。\n\n「足す」より「引く」の方が、肌は早く変わります。\n\n全部タダでできることです。",
        "肌が変わった7つのやめること。\n\n1. 1日3回以上の洗顔\n   → 必要な皮脂まで落として悪化させてた\n\n2. 高い美容液の重ね塗り\n   → 原因が違うから表面を整えても無意味\n\n3. 深夜0時以降に寝る\n   → 成長ホルモンが出ない＝修復されない\n\n4. 甘いジュースを毎日飲む\n   → 血糖値スパイク＋腸の悪玉菌が増える\n\n5. パンを毎朝食べる\n   → グルテンで腸壁を傷つけてた\n\n6. ニキビを触る・潰す\n   → 菌を広げて新しいニキビを作る\n\n7. ストレスを食事で発散する\n   → 腸と血糖値のダブルダメージ",
        "この投稿、保存しておくと◎\n\n毎日1つ、肌荒れを改善するヒントを投稿しています。\nフォローするとタイムラインに届きます。"
      ]
    },
    {
      "id": 10,
      "theme": "腸活食習慣",
      "posts": [
        "腸が整っている人がやっている食習慣、5つ。\n\n全部今日から始められます。\n高いサプリより、まずこれを試してください。",
        "腸活のための5つの食習慣。\n\n1. 納豆を週4回食べる\n   → 善玉菌のエサになる食物繊維が豊富\n\n2. 味噌汁を毎朝飲む\n   → 発酵食品＋温かい液体で腸を起こす\n\n3. 甘い飲み物をお茶に替える\n   → 砂糖は悪玉菌のエサ・腸壁を荒らす\n\n4. 野菜・きのこを毎食1品\n   → 食物繊維が善玉菌を育てる\n\n5. 夜8時以降は食べない\n   → 腸を休ませると修復が進む\n\nどれか1つから始めて、続けること。\n腸は変えるのに時間がかかるが、変わったら肌も変わります。",
        "この投稿、保存しておくと◎\n\n毎日1つ、肌荒れを改善するヒントを投稿しています。\nフォローするとタイムラインに届きます。"
      ]
    },
    {
      "id": 11,
      "theme": "お金をかけない美肌",
      "posts": [
        "3万円の化粧水より先にやること、8つ。\n\n全部無料か500円以下でできます。\n\n「高いものを使っているのに治らない」という人、これが先です。",
        "お金をかけずに肌が変わる8つのこと。\n\n1. 朝日を5分浴びる（体内時計を整える）\n2. 水を1日1.5〜2L飲む（血液をきれいにする）\n3. 緑茶を常備する（抗炎症・抗酸化作用）\n4. 小麦を週3回以下にする（腸壁を守る）\n5. 夜8時以降食べない（腸を休ませる）\n6. 化粧品を1本に絞る（重ね塗りは逆効果）\n7. 就寝前スマホを30分やめる（睡眠の質を上げる）\n8. ニキビを絶対触らない（菌を広げない）\n\n全部やれば最強。でも1つからでいい。\n\nどれが一番難しそうですか？",
        "この投稿、保存しておくと◎\n\n毎日1つ、肌荒れを改善するヒントを投稿しています。\nフォローするとタイムラインに届きます。"
      ]
    },
    {
      "id": 12,
      "theme": "タイプ別診断",
      "posts": [
        "大人ニキビ、同じ対策をしても効く人と効かない人がいる理由。\n\nタイプが違うから。\n\nあなたはどのタイプか、確認してみてください。",
        "大人ニキビ4タイプ診断。\n\nA：皮脂過多型\n→ Tゾーンがテカる・甘いものが好き\n→ 対策：糖質を減らす・洗顔1日2回まで\n\nB：腸荒れ型\n→ パン主食・便通が不安定\n→ 対策：発酵食品を増やす・小麦を減らす\n\nC：ホルモン乱れ型\n→ 夜更かし・生理前に悪化する\n→ 対策：23時前就寝・ストレス管理\n\nD：ストレス型\n→ 頬の赤み・食いしばり癖がある\n→ 対策：深呼吸・休息時間を作る\n\n複数当てはまる場合は、最も当てはまるタイプから始めると効果が出やすい。\n\nあなたはA〜Dどれですか？",
        "この投稿、保存しておくと◎\n\n毎日1つ、肌荒れを改善するヒントを投稿しています。\nフォローするとタイムラインに届きます。"
      ]
    },
    {
      "id": 13,
      "theme": "水分と肌",
      "posts": [
        "水を1日2L飲むだけで肌が変わる。\n\n「そんな簡単な話?」と思うかもしれませんが、\n水不足の人の肌荒れは、水を飲むだけで改善することがあります。",
        "水と肌の関係。\n\n水分が不足すると：\n・血液がドロドロになる\n・老廃物が排出されにくくなる\n・肌のターンオーバーが遅くなる\n・皮脂が過剰になる（乾燥を補おうとする）\n\nこれ全部、ニキビ・乾燥・くすみの原因です。\n\n正しい水の飲み方：\n① 起き抜けにコップ1杯（腸を起こす）\n② 食前にコップ1杯（食べすぎ防止にもなる）\n③ 甘い飲み物をすべてお茶か水に替える\n\n「水を飲む」だけで、3つの肌問題が同時に改善します。",
        "この投稿、保存しておくと◎\n\n毎日1つ、肌荒れを改善するヒントを投稿しています。\nフォローするとタイムラインに届きます。"
      ]
    },
    {
      "id": 14,
      "theme": "亜鉛と皮脂",
      "posts": [
        "皮脂が多い人が不足しているミネラルがあります。\n\n「亜鉛」です。\n\nスキンケアより先に、これを見直した方が早く変わります。",
        "亜鉛と皮脂の話。\n\n亜鉛は「皮脂分泌をコントロールするミネラル」です。\n\n亜鉛が不足すると：\n・皮脂が過剰になる\n・炎症が治まりにくくなる\n・ニキビが繰り返す\n\n亜鉛が多い食べ物：\n・牡蠣（圧倒的に多い）\n・牛肉・豚肉\n・納豆・豆腐\n・カシューナッツ\n\n食事で摂れない場合は亜鉛サプリ（1日15mg程度）で補える。\nコンビニで1000円以下で買える。\n\n3万円の化粧品より、亜鉛1000円の方が効く人がいます。",
        "この投稿、保存しておくと◎\n\n毎日1つ、肌荒れを改善するヒントを投稿しています。\nフォローするとタイムラインに届きます。"
      ]
    }
  ]
}
```

- [ ] **Step 2: JSONが正しく読めるか確認する**

ターミナルで実行：
```bash
cd /home/kenta_kamijyo/skin
python3 -c "
import json
with open('skin_threads_posts.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
threads = data['threads']
print(f'セット数: {len(threads)}')
for t in threads:
    posts = t['posts']
    lens = [len(p) for p in posts]
    over = [i+1 for i, l in enumerate(lens) if l > 500]
    status = '⚠️ 500文字超' if over else '✅'
    print(f'{status} [{t[\"id\"]}] {t[\"theme\"]} | 本1:{lens[0]}字 本2:{lens[1]}字 本3:{lens[2]}字')
"
```

期待する出力（14セット全部✅、文字数が全て500以下）：
```
セット数: 14
✅ [1] 問いかけ型 | 本1:... 本2:... 本3:...
✅ [2] 腸と肌のつながり | ...
（14行続く）
```

⚠️ が出た場合：該当セットの投稿文を短くする

- [ ] **Step 3: コミットする**

```bash
cd /home/kenta_kamijyo
git add skin/skin_threads_posts.json
git commit -m "投稿データ追加: skin Threads ツリー投稿（14セット×3本）"
```

---

## Task 2: skin_threads_action.py をツリー投稿対応に改修する

**Files:**
- Modify: `skin/skin_threads_action.py`

- [ ] **Step 1: ファイルを以下の内容に書き換える**

`skin/skin_threads_action.py` を以下の内容に完全に書き換える：

```python
# skin_threads_action.py
# GitHub Actions専用の自動投稿スクリプト（対話なし・全自動）
# ツリー構造（3本連鎖）でThreadsに投稿する

import json                    # JSONファイルを扱う道具
import os                      # 環境変数を読み込む道具
import time                    # 待機処理に使う道具
import requests                # インターネットにリクエストを送る道具
from datetime import datetime  # 今の日時を取得する道具

# 環境変数からAPIキーを読み込む（GitHub Actionsのsecretsから渡される）
THREADS_ACCESS_TOKEN = os.environ["THREADS_ACCESS_TOKEN"]
THREADS_USER_ID      = os.environ["THREADS_USER_ID"]

# 投稿データと進捗ファイルのパス
POSTS_FILE    = "skin_threads_posts.json"       # ツリー用の新しい投稿データ
PROGRESS_FILE = "skin_threads_progress.json"   # 次に投稿する番号を覚えておくファイル

# 3本目の投稿につけるハッシュタグ
HASHTAGS = "\n\n#肌荒れ #大人ニキビ #ニキビ改善 #腸活 #美肌習慣"


def post_to_threads(text, reply_to_id=None):
    """
    Threads APIを使って投稿する（2段階APIコール）
    reply_to_id を渡すとリプライ投稿になる（ツリーの2本目・3本目に使う）
    """

    # ステップ1: 投稿コンテナ（投稿の下書き）を作成する
    container_url = f"https://graph.threads.net/{THREADS_USER_ID}/threads"
    container_params = {
        "media_type": "TEXT",                 # テキスト投稿
        "text": text,                         # 投稿する文章
        "access_token": THREADS_ACCESS_TOKEN  # 認証キー
    }

    # リプライ投稿の場合は「どの投稿への返信か」を追加する
    if reply_to_id:
        container_params["reply_to_id"] = reply_to_id

    response = requests.post(container_url, params=container_params)
    data = response.json()

    if "id" not in data:
        raise Exception(f"コンテナ作成失敗: {data}")

    creation_id = data["id"]  # 下書きのID

    # Threads APIはコンテナ作成後すぐに公開するとエラーになるため30秒待つ
    print("  コンテナ作成完了。30秒待機中...")
    time.sleep(30)

    # ステップ2: 下書きを実際に公開する
    publish_url = f"https://graph.threads.net/{THREADS_USER_ID}/threads_publish"
    publish_params = {
        "creation_id": creation_id,
        "access_token": THREADS_ACCESS_TOKEN
    }
    publish_response = requests.post(publish_url, params=publish_params)
    publish_data = publish_response.json()

    if "id" not in publish_data:
        raise Exception(f"公開失敗: {publish_data}")

    return publish_data["id"]  # 投稿IDを返す（次のリプライ先として使う）


def load_posts():
    """ツリー投稿データをJSONから読み込む"""
    with open(POSTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_progress():
    """進捗ファイルを読み込む（なければ初期値で始める）"""
    if not os.path.exists(PROGRESS_FILE):
        return {"daily_index": 0, "history": []}
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_progress(progress):
    """進捗をファイルに保存する"""
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def main():
    """メイン処理（全自動・対話なし）"""
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    print(f"=== skin自動投稿開始: {now} ===")

    # 投稿データと進捗を読み込む
    posts    = load_posts()
    progress = load_progress()

    # ローテーションで今回のセットを選ぶ（14セットを繰り返す）
    threads_list = posts["threads"]
    index        = progress.get("daily_index", 0) % len(threads_list)
    thread_set   = threads_list[index]

    print(f"投稿セット: {index + 1}/{len(threads_list)} ({thread_set['theme']})")

    # 3本の投稿テキストを準備する（3本目にハッシュタグを追加する）
    text_1 = thread_set["posts"][0]
    text_2 = thread_set["posts"][1]
    text_3 = thread_set["posts"][2] + HASHTAGS

    # 本1を投稿する（新規投稿）
    print("\n本1を投稿中（フック）...")
    post_id_1 = post_to_threads(text_1)
    print(f"  ✅ 本1投稿成功！（ID: {post_id_1}）")

    # 本2を本1にリプライする
    print("\n本2を投稿中（本題）...")
    post_id_2 = post_to_threads(text_2, reply_to_id=post_id_1)
    print(f"  ✅ 本2投稿成功！（ID: {post_id_2}）")

    # 本3を本2にリプライする
    print("\n本3を投稿中（CTA）...")
    post_id_3 = post_to_threads(text_3, reply_to_id=post_id_2)
    print(f"  ✅ 本3投稿成功！（ID: {post_id_3}）")

    # 次の投稿番号に進める（14セットを超えたら0に戻る）
    progress["daily_index"] = (index + 1) % len(threads_list)
    next_thread = threads_list[progress["daily_index"]]
    print(f"\n次回: {next_thread['theme']}")

    # 履歴に記録する
    if "history" not in progress:
        progress["history"] = []
    progress["history"].append({
        "date": now,
        "theme": thread_set["theme"],
        "post_id_1": post_id_1,
        "post_id_2": post_id_2,
        "post_id_3": post_id_3
    })

    save_progress(progress)  # 進捗を保存する
    print("=== 完了 ===")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 構文エラーがないか確認する**

```bash
cd /home/kenta_kamijyo/skin
python3 -c "import py_compile; py_compile.compile('skin_threads_action.py', doraise=True); print('✅ 構文OK')"
```

期待する出力：
```
✅ 構文OK
```

エラーが出た場合：エラーメッセージの行番号を確認して該当箇所を修正する

- [ ] **Step 3: コミットする**

```bash
cd /home/kenta_kamijyo
git add skin/skin_threads_action.py
git commit -m "スクリプト改修: skin Threads ツリー投稿対応（3本連鎖）"
```

---

## Task 3: GitHubにプッシュして自動投稿を確認する

**Files:**
- 変更なし（プッシュのみ）

- [ ] **Step 1: GitHubにプッシュする**

```bash
cd /home/kenta_kamijyo
git push
```

- [ ] **Step 2: 次のGitHub Actions実行を待つ**

GitHubのActionsタブで確認する：
- リポジトリページ → Actionsタブ → 「skin Threads自動投稿」ワークフロー
- 次の発火タイミング（毎時07分）に実行されることを確認する

- [ ] **Step 3: 実行結果を確認する**

GitHub Actionsのログで以下を確認：
```
=== skin自動投稿開始: 2026/XX/XX XX:07 ===
投稿セット: 1/14 (問いかけ型)

本1を投稿中（フック）...
  コンテナ作成完了。30秒待機中...
  ✅ 本1投稿成功！（ID: XXXXXXXXXXXXXXX）

本2を投稿中（本題）...
  コンテナ作成完了。30秒待機中...
  ✅ 本2投稿成功！（ID: XXXXXXXXXXXXXXX）

本3を投稿中（CTA）...
  コンテナ作成完了。30秒待機中...
  ✅ 本3投稿成功！（ID: XXXXXXXXXXXXXXX）

次回: 腸と肌のつながり
=== 完了 ===
```

- [ ] **Step 4: Threadsアプリで実際の投稿を確認する**

skinアカウントのThreadsページを開いて：
- 本1（フック）が新規投稿として表示されている
- 本1の下に本2（本題）がリプライとして表示されている
- 本2の下に本3（CTA＋ハッシュタグ）がリプライとして表示されている

---

## 完了条件チェックリスト

- [ ] `skin/skin_threads_posts.json` に14セット×3本のデータが正しく入っている
- [ ] `skin/skin_threads_action.py` がツリー投稿に対応している（構文エラーなし）
- [ ] GitHub Actionsで3本連鎖投稿が成功している
- [ ] Threadsアプリでツリー構造が確認できている
