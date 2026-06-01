# skin リプ巡回ツール skin_reply_hunter.py 実装プラン

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** skinアカウントの能動リプ運用「探す → 書く → 記録」を1コマンドで回せる半自動CLIツールを作る（Threads APIは一切叩かない）。

**Architecture:** 純粋ロジック関数（`suggest_drafts` / `sort_round_list` / `record_reply` / 日次ログ追記ロジック）と、I/O・ブラウザ・対話（`main`周り）を分離する。テストは純粋ロジックだけに集中。テンプレートは `skin_comment_helper.py` から共通モジュールへ切り出し、両ツールで共有する。

**Tech Stack:** Python3標準ライブラリのみ（`os` / `json` / `random` / `webbrowser` / `subprocess` / `datetime`）。テストは `pytest`。新規ライブラリのインストールは不要。

---

## 設計の出典

このプランは `docs/superpowers/specs/2026-06-01-skin-reply-hunter-design.md`（設計合意済み）を実装に落とすもの。仕様の根拠が必要なときはそちらを参照する。

## 規約・前提（全タスク共通）

- **Threads APIを一切叩かない**。ネットワーク・トークンの心配はなく、守るのはファイル読み書きと入力ミスだけ。
- **新規ライブラリ禁止**。上記の標準ライブラリだけで作る。
- **「今日」は日本時間（JST = UTC+9）基準**で決める。
- 各行に初心者向けの日本語コメントを付ける（CLAUDE.md方針）。変数名・関数名は略さない英単語。
- **テストのimport方式**（このリポジトリには `conftest.py` / `pytest.ini` 等の設定ファイルが無いため、各テスト冒頭で明示する）:
  ```python
  import sys
  from pathlib import Path
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # skin/ をimportパスに追加
  import skin_reply_hunter as hunter
  ```
- **日次ログの空欄行は末尾スペース無し**で書く。既存 `skin_daily_log.md` の空欄枠（例 `- リプ件数:`）に揃え、CLAUDE.md「行末に空白を入れない」にも従う（設計specの例では末尾スペース有りに見えるが、既存ファイル側に合わせるのが正）。値が入る行だけ `- リプ件数: 5` のようにコロン＋半角スペース＋値とする。
- `pytest` の実行はリポジトリルート `/home/kenta_kamijyo/` から行う。

## ファイル構成

| ファイル | 区分 | 責務 |
|---|---|---|
| `skin/skin_comment_templates.py` | 新規 | コメント／リプのテンプレ集 `COMMENT_TEMPLATES`（6カテゴリ）を持つ共通モジュール |
| `skin/skin_comment_helper.py` | 変更 | テンプレ辞書の直書きをやめ、共通モジュールから `import` するだけにする（挙動は不変） |
| `skin/skin_reply_hunter.py` | 新規（本体） | 巡回・下書き提示・記録の半自動ツール本体 |
| `skin/tests/test_skin_reply_hunter.py` | 新規 | 純粋ロジック関数の `pytest` |
| `skin/skin_reply_history.json` | 自動生成 | アカウント別リプ履歴。**手で作らない**。`save_history` が実行時に初めて書き出す |
| `learning/learning_notes.md` | 変更 | 「作成したプログラム」一覧表に新規2ファイルを追記（Task 7） |

依存方向: `skin_comment_helper.py` と `skin_reply_hunter.py` の両方が `skin_comment_templates.py` を読む。テストは `skin_reply_hunter.py` の純粋関数だけを対象にする。

---

## Task 1: テンプレートを共通モジュールへ切り出す

`skin_comment_helper.py` 内の `COMMENT_TEMPLATES` を新ファイルへ移し、両ツールで共有する。挙動は変えない（純粋なリファクタリング）。

**Files:**
- Create: `skin/skin_comment_templates.py`
- Modify: `skin/skin_comment_helper.py:7-88`（先頭のテンプレ辞書を `import` 1行へ差し替え）

- [ ] **Step 1: 共通モジュールを作る**

`skin/skin_comment_templates.py` を新規作成し、`skin_comment_helper.py` にある辞書を**そのまま**移す（内容は1文字も変えない）。

```python
# skin_comment_templates.py
# skin アカウントのコメント／リプ用テンプレート集（カテゴリー別）。
# skin_comment_helper.py と skin_reply_hunter.py の両方から import して共有する。
# テンプレを直したいときは必ずこのファイルを編集する（1箇所直せば両ツールに反映される）。

COMMENT_TEMPLATES = {
    "1": {
        "name": "腸活・食事系の投稿へ",
        "comments": [
            "腸と肌のつながり、本当にそうですよね。食事を変えてから肌が落ち着いてきました。",
            "納豆と味噌汁を朝の定番にしたら便通が変わって、それから肌も変わりました。",
            "グルテンを減らして2週間で肌の変化を感じました。まず食事から変えるのが正解でした。",
            "腸活を始めてから高い化粧品への依存が減りました。内側を整えると外側が要らなくなってきます。",
            "発酵食品を毎日取り入れるようになってから、ニキビが出にくくなってきた気がします。",
            "甘い飲み物を緑茶に替えただけで、2週間後に肌のテカりが落ち着きました。まず飲み物が一番ハードル低い。",
            "腸が整うと肌が変わるって信じてなかったんですが、実際に変わりました。半信半疑でもやってみる価値あります。",
        ],
    },
    "2": {
        "name": "睡眠・生活習慣系の投稿へ",
        "comments": [
            "23時就寝を続けたら、朝の肌の状態が全然違ってきました。睡眠って本当に大事。",
            "夜更かしをやめるのが一番ハードル高かったですが、効果は一番実感しやすかったです。",
            "スマホを23時に置くようにしただけで、1週間後に肌の回復が早くなった気がします。",
            "睡眠の質が変わると肌が変わりますよね。成長ホルモンのゴールデンタイム、意識するようになりました。",
            "睡眠を改善したら化粧品代が浮きました笑 内側が整うと外側が要らなくなってきます。",
            "コルチゾールが肌荒れに直結してるって知ってから、ストレス対策を意識するようになりました。",
            "朝日を5分浴びるだけで体内時計が整って、夜の眠気の質が変わってきました。",
        ],
    },
    "3": {
        "name": "スキンケア・化粧品系の投稿へ",
        "comments": [
            "引き算のスキンケア、大事ですよね。高い化粧品より洗顔の回数を減らす方が効きました。",
            "洗いすぎをやめたら逆にテカりが落ち着いた経験があります。やりすぎが原因だったんですね。",
            "シンプルケアに変えてから肌が安定してきました。重ね塗りは逆効果でした。",
            "化粧水1本だけにしたら肌のバリアが整ってきた感じがします。",
            "スキンケアをシンプルにするのって最初は不安でしたが、変えて正解でした。",
            "洗顔料を低刺激なものに変えただけで、つっぱりがなくなりました。道具より使い方ですね。",
            "スキンケアに月1万かけるより、食事と睡眠に使う方が変わった実感があります。",
        ],
    },
    "4": {
        "name": "ニキビ悩み・共感系の投稿へ",
        "comments": [
            "同じ経験があります。外側だけ頑張っていた頃は全然変わりませんでした。",
            "この情報、もっと早く知りたかったです。",
            "繰り返すニキビって本当につらいですよね。原因を変えないと解決しないと気づいたのが転機でした。",
            "肌荒れって見た目だけじゃなくてメンタルにも来ますよね。同じ思いをしてきました。",
            "「体質だから仕方ない」と思い込んでた頃、生活習慣を変えたら変わりました。諦めなくてよかった。",
            "高い化粧品を試し続けた時期があったので、すごく共感します。",
            "内側から変えるって最初は半信半疑でしたが、試してよかったです。",
        ],
    },
    "5": {
        "name": "サプリ・栄養系の投稿へ",
        "comments": [
            "亜鉛を3ヶ月続けたら皮脂の量が変わってきました。続けることが大事ですね。",
            "サプリより先に食事を整えるのが正解でした。基礎ができてからサプリが活きる感じ。",
            "亜鉛とビタミンAを意識するようになってから肌の回復が早くなった気がします。",
            "高いサプリより食事改革の方が効いた体験があります。まず食事ですよね。",
            "緑茶に替えるだけで結構変わるんですよね。飲み物から始めるのが一番ハードルが低い。",
            "亜鉛サプリ、月500円くらいで始められるのがいいですよね。3ヶ月試す価値あります。",
            "コーヒーを緑茶に変えてから肌の調子が安定してきました。カフェインって意外と影響しますね。",
        ],
    },
    "6": {
        "name": "ファスティング・断食系の投稿へ",
        "comments": [
            "夜8時以降食べないを続けたら、2週間で頬の赤みが落ち着いてきました。",
            "16時間ファスティング、最初の3日は辛かったですが4日目から急に楽になりました。",
            "腸を休ませるって感覚、実際にやってみると体感できますよね。",
            "ファスティング後の朝の頭のクリアさ、最初は驚きました。肌にも同じことが起きてる気がします。",
            "夜食をやめるだけでも違いますよね。消化に使う energy が肌の修復に回せる感じ。",
        ],
    },
}
```

- [ ] **Step 2: 共通モジュールが読めることを確認（最初の動作チェック）**

Run: `cd /home/kenta_kamijyo && PYTHONPATH=skin python3 -c "from skin_comment_templates import COMMENT_TEMPLATES; print(len(COMMENT_TEMPLATES))"`
Expected: `6`

- [ ] **Step 3: skin_comment_helper.py を辞書直書きから import に差し替える**

`skin/skin_comment_helper.py` の 7〜88行目（コメントブロック `# ---...` / `# コメントテンプレート集（カテゴリー別）` / `# ---...` と `COMMENT_TEMPLATES = {` から対応する閉じ `}`（`def show_menu` 直前）まで）を削除。差し替え後ファイル先頭:

```python
# skin_comment_helper.py
# 他アカウントへのコメント候補を生成するツール
# 使い方: python3 skin/skin_comment_helper.py

import random  # ランダムにコメントを並べ替えるための道具

# コメントテンプレートは共通モジュールから読み込む（skin_reply_hunter.py と共有）
from skin_comment_templates import COMMENT_TEMPLATES
```

以降の `def show_menu()` / `show_comments` / `main` / ガードは一切変更しない。

- [ ] **Step 4: 切り出し後も挙動不変を確認**

Run: `cd /home/kenta_kamijyo && PYTHONPATH=skin python3 -c "from skin_comment_templates import COMMENT_TEMPLATES as A; import skin_comment_helper as H; assert H.COMMENT_TEMPLATES is A; print(len(A))"`
Expected: `6`

- [ ] **Step 5: コミット**

```bash
cd /home/kenta_kamijyo && git add skin/skin_comment_templates.py skin/skin_comment_helper.py && git commit -m "refactor: COMMENT_TEMPLATES を共通モジュールへ切り出し"
```

---

## Task 2: 本体ファイル作成 ＋ suggest_drafts（下書き生成）

投稿文のキーワードからカテゴリを判定し、そのカテゴリのテンプレから下書き3案を返す純粋関数を作る。テストしやすいよう `(drafts, category_key)` のタプルを返す（`random.sample` の結果そのものは固定できないため、テストは `category_key` と「候補が正しいカテゴリ集合の部分集合か」で検証する）。

**Files:**
- Create: `skin/skin_reply_hunter.py`
- Test: `skin/tests/test_skin_reply_hunter.py`

- [ ] **Step 1: 失敗するテストを書く**

`skin/tests/test_skin_reply_hunter.py` を新規作成:

```python
# test_skin_reply_hunter.py
# skin_reply_hunter.py の純粋ロジック関数をテストする（ファイル操作・対話は対象外）。

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # skin/ をimportパスに追加

import skin_reply_hunter as hunter

def test_suggest_drafts_gut_health_returns_category_1():
    # 「腸活・発酵」が入っていればカテゴリ1（腸活・食事）になる
    drafts, category = hunter.suggest_drafts("最近腸活を始めて発酵食品を食べています")
    assert category == "1"
    assert len(drafts) == 3
    assert set(drafts).issubset(set(hunter.COMMENT_TEMPLATES["1"]["comments"]))

def test_suggest_drafts_acne_returns_category_4():
    # 「ニキビ・肌荒れ」が入っていればカテゴリ4（ニキビ共感）になる
    drafts, category = hunter.suggest_drafts("繰り返すニキビと肌荒れに悩んでいます")
    assert category == "4"
    assert set(drafts).issubset(set(hunter.COMMENT_TEMPLATES["4"]["comments"]))

def test_suggest_drafts_no_match_returns_generic():
    # どのキーワードにも当たらなければ汎用テンプレになる
    drafts, category = hunter.suggest_drafts("今日はいい天気ですね、散歩しました")
    assert category == "generic"
    assert set(drafts).issubset(set(hunter.GENERIC_DRAFTS))

def test_suggest_drafts_multiple_match_picks_most_hits():
    # 複数カテゴリに当たったら、当たり数が多いカテゴリを選ぶ（腸活=3語 > ニキビ=1語）
    drafts, category = hunter.suggest_drafts("腸活で発酵食品をとったら肌荒れが減った")
    assert category == "1"

def test_suggest_drafts_tie_picks_lowest_category_number():
    # 当たり数が同じ（睡眠1語・乾燥1語）なら、カテゴリ番号の若い方を選ぶ
    drafts, category = hunter.suggest_drafts("睡眠と乾燥が気になる")
    assert category == "2"
```

- [ ] **Step 2: テストを実行して失敗を確認**

Run: `cd /home/kenta_kamijyo && pytest skin/tests/test_skin_reply_hunter.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'skin_reply_hunter'`）

- [ ] **Step 3: 本体の先頭部分＋ suggest_drafts を書く**

`skin/skin_reply_hunter.py` を新規作成:

```python
# skin_reply_hunter.py
# skin アカウントの「能動リプ巡回」を1コマンドで回す半自動ツール。
# 探す（巡回リスト＋ブラウザ起動）→ 書く（下書き3案）→ 記録（履歴JSON＋日次ログ）をまとめる。
# Threads API は一切叩かない（投稿は Kenta が手動でアプリにコピペする）。
# 使い方: python3 skin/skin_reply_hunter.py

import os          # ファイルのパスを組み立てる道具
import json        # JSON ファイルを読み書きする道具
import random      # 下書き候補をランダムに選ぶ道具
import webbrowser  # ブラウザでURLを開く道具（標準ライブラリ）
import subprocess  # WSL2でWindows側のブラウザを呼ぶ予備手段（標準ライブラリ）
from datetime import datetime, timezone, timedelta  # 日付・時刻を扱う道具

# コメントテンプレートは共通モジュールから読み込む（skin_comment_helper.py と共有）
from skin_comment_templates import COMMENT_TEMPLATES

# 日本時間（JST = UTC+9）。「今日」を日本基準で決めるために使う
JST = timezone(timedelta(hours=9))

# このファイルがある skin/ フォルダを基準に、関係ファイルの場所を決める
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGETS_PATH = os.path.join(BASE_DIR, "skin_account_targets.json")
HISTORY_PATH = os.path.join(BASE_DIR, "skin_reply_history.json")
DAILY_LOG_PATH = os.path.join(BASE_DIR, "skin_daily_log.md")

# 投稿文に含まれるキーワード → カテゴリ番号（COMMENT_TEMPLATES のキー "1"〜"6" に対応）
CATEGORY_KEYWORDS = {
    "1": ["腸", "便秘", "発酵", "食物繊維", "腸活"],
    "2": ["寝", "睡眠", "夜更かし", "寝不足"],
    "3": ["化粧水", "保湿", "乾燥", "スキンケア"],
    "4": ["ニキビ", "肌荒れ", "吹き出物", "赤み"],
    "5": ["サプリ", "ビタミン", "亜鉛", "鉄", "栄養"],
    "6": ["ファスティング", "断食", "16時間"],
}

# どのカテゴリにも当てはまらないとき用の「共感＋ひとこと質問」汎用テンプレ
GENERIC_DRAFTS = [
    "すごく共感します。私も似た経験があるので、つい読み込んでしまいました。",
    "この視点、勉強になります。ちなみに続けるコツってありますか？",
    "わかります…！内側から整えるって地味だけど効きますよね。",
    "参考になります。自分も少しずつ試してみようと思いました。",
    "丁寧な発信ですね。続きもぜひ読みたいです。",
]

def suggest_drafts(post_text):
    """投稿文のキーワードからカテゴリを判定し、下書き3案を返す純粋関数。

    戻り値: (drafts, category_key)
      - drafts: 下書き文字列のリスト（最大3件）
      - category_key: "1"〜"6"（該当カテゴリ）か "generic"（該当なし）
    判定が同点のときはカテゴリ番号の若い方を選ぶ（結果が毎回同じになるよう順序を固定）。
    """
    # カテゴリごとに「投稿文に含まれたキーワードの数」を数える
    scores = {}
    for key, keywords in CATEGORY_KEYWORDS.items():
        scores[key] = sum(1 for word in keywords if word in post_text)

    # 一番当たり数が多いカテゴリを選ぶ。同点はカテゴリ番号の若い方（"1"→"6"の順で先に見る）
    best_key = None
    best_score = 0
    for key in sorted(CATEGORY_KEYWORDS.keys()):
        if scores[key] > best_score:
            best_score = scores[key]
            best_key = key

    # どのキーワードにも当たらなければ汎用テンプレを返す
    if best_key is None:
        return random.sample(GENERIC_DRAFTS, min(3, len(GENERIC_DRAFTS))), "generic"

    # 当たったカテゴリのテンプレから3案をランダムに選ぶ
    comments = COMMENT_TEMPLATES[best_key]["comments"]
    return random.sample(comments, min(3, len(comments))), best_key
```

- [ ] **Step 4: テストを実行して成功を確認**

Run: `cd /home/kenta_kamijyo && pytest skin/tests/test_skin_reply_hunter.py -v`
Expected: PASS（5件）

- [ ] **Step 5: コミット**

```bash
cd /home/kenta_kamijyo && git add skin/skin_reply_hunter.py skin/tests/test_skin_reply_hunter.py && git commit -m "feat: skin_reply_hunter に suggest_drafts（下書き生成）を追加"
```

---

## Task 3: sort_round_list（巡回順の並べ替え）

履歴の `last_replied_at`（最終リプ日）を見て、しばらくリプっていない人を上に並べる純粋関数。未リプは `""` 扱いで最優先。同点は元の並び順を保つ（安定ソート）。

**Files:**
- Modify: `skin/skin_reply_hunter.py`（`suggest_drafts` の下に追記）
- Test: `skin/tests/test_skin_reply_hunter.py`（末尾に追記）

- [ ] **Step 1: 失敗するテストを追記する**

`skin/tests/test_skin_reply_hunter.py` の末尾に追記:

```python
def test_sort_round_list_unreplied_comes_first():
    # 未リプ（履歴に無い）アカウントが最優先で先頭に来る
    targets = [
        {"handle": "@a", "url": "x", "theme": "t", "notes": ""},
        {"handle": "@b", "url": "x", "theme": "t", "notes": ""},
    ]
    history = {"@a": {"last_replied_at": "2026-05-30", "total_replies": 1}}
    ordered = hunter.sort_round_list(targets, history)
    assert ordered[0]["handle"] == "@b"  # 未リプの @b が先頭

def test_sort_round_list_oldest_first():
    # リプ日が古い順に並ぶ
    targets = [
        {"handle": "@a", "url": "x", "theme": "t", "notes": ""},
        {"handle": "@b", "url": "x", "theme": "t", "notes": ""},
    ]
    history = {
        "@a": {"last_replied_at": "2026-05-30", "total_replies": 1},
        "@b": {"last_replied_at": "2026-05-20", "total_replies": 1},
    }
    ordered = hunter.sort_round_list(targets, history)
    assert ordered[0]["handle"] == "@b"  # 古い @b が先頭

def test_sort_round_list_stable_keeps_original_order_on_tie():
    # 全員未リプ（同点）なら元の並び順を保つ（安定ソート）
    targets = [
        {"handle": "@a", "url": "x", "theme": "t", "notes": ""},
        {"handle": "@b", "url": "x", "theme": "t", "notes": ""},
        {"handle": "@c", "url": "x", "theme": "t", "notes": ""},
    ]
    ordered = hunter.sort_round_list(targets, {})
    assert [t["handle"] for t in ordered] == ["@a", "@b", "@c"]
```

- [ ] **Step 2: テストを実行して失敗を確認**

Run: `cd /home/kenta_kamijyo && pytest skin/tests/test_skin_reply_hunter.py -k sort_round_list -v`
Expected: FAIL（`AttributeError: module ... has no attribute 'sort_round_list'`）

- [ ] **Step 3: sort_round_list を実装する**

`skin/skin_reply_hunter.py` の `suggest_drafts` の下に追記:

```python
def sort_round_list(targets, history):
    """巡回順に並べたターゲットのリストを返す純粋関数（元のリストは壊さない）。

    並び順: 前回リプ日（last_replied_at）が古い順。未リプは "" 扱いで最優先。
    日付は ISO "YYYY-MM-DD" なので文字列の昇順がそのまま「古い順」になる。
    同点は Python の sorted が安定ソートなので元の並び順を保つ。
    """
    def sort_key(target):
        # 履歴にそのアカウントが無ければ未リプ → "" を返して最優先にする
        entry = history.get(target["handle"], {})
        return entry.get("last_replied_at") or ""

    return sorted(targets, key=sort_key)
```

- [ ] **Step 4: テストを実行して成功を確認**

Run: `cd /home/kenta_kamijyo && pytest skin/tests/test_skin_reply_hunter.py -k sort_round_list -v`
Expected: PASS（3件）

- [ ] **Step 5: コミット**

```bash
cd /home/kenta_kamijyo && git add skin/skin_reply_hunter.py skin/tests/test_skin_reply_hunter.py && git commit -m "feat: skin_reply_hunter に sort_round_list（巡回順）を追加"
```

---

## Task 4: record_reply（リプ履歴の更新）

指定アカウントへのリプを履歴に1件記録する純粋関数。`last_replied_at` を今日に更新し、`total_replies` を1増やす。初めてのアカウントなら1から始まる。

**Files:**
- Modify: `skin/skin_reply_hunter.py`（`sort_round_list` の下に追記）
- Test: `skin/tests/test_skin_reply_hunter.py`（末尾に追記）

- [ ] **Step 1: 失敗するテストを追記する**

`skin/tests/test_skin_reply_hunter.py` の末尾に追記:

```python
def test_record_reply_new_handle_starts_at_one():
    # 初めてのアカウントは total_replies が 1 から始まる
    history = {}
    updated = hunter.record_reply(history, "@new", "2026-06-01")
    assert updated["@new"]["last_replied_at"] == "2026-06-01"
    assert updated["@new"]["total_replies"] == 1

def test_record_reply_existing_handle_increments():
    # 既存アカウントは total_replies が1増え、日付が更新される
    history = {"@a": {"last_replied_at": "2026-05-20", "total_replies": 2}}
    updated = hunter.record_reply(history, "@a", "2026-06-01")
    assert updated["@a"]["last_replied_at"] == "2026-06-01"
    assert updated["@a"]["total_replies"] == 3
```

- [ ] **Step 2: テストを実行して失敗を確認**

Run: `cd /home/kenta_kamijyo && pytest skin/tests/test_skin_reply_hunter.py -k record_reply -v`
Expected: FAIL（`AttributeError: ... 'record_reply'`）

- [ ] **Step 3: record_reply を実装する**

`skin/skin_reply_hunter.py` の `sort_round_list` の下に追記:

```python
def record_reply(history, handle, today):
    """指定アカウントへのリプを履歴に1件記録し、更新後の履歴を返す。

    - last_replied_at を today（"YYYY-MM-DD"）に更新する
    - total_replies を1増やす（初めてのアカウントなら 1 から始まる）
    history を直接書き換える（呼び出し側で save_history する前提）。
    """
    # そのアカウントの記録を取り出す。無ければ初期値（未リプ・0件）を使う
    entry = history.get(handle, {"last_replied_at": None, "total_replies": 0})
    entry["last_replied_at"] = today
    entry["total_replies"] = entry.get("total_replies", 0) + 1
    history[handle] = entry
    return history
```

- [ ] **Step 4: テストを実行して成功を確認**

Run: `cd /home/kenta_kamijyo && pytest skin/tests/test_skin_reply_hunter.py -k record_reply -v`
Expected: PASS（2件）

- [ ] **Step 5: コミット**

```bash
cd /home/kenta_kamijyo && git add skin/skin_reply_hunter.py skin/tests/test_skin_reply_hunter.py && git commit -m "feat: skin_reply_hunter に record_reply（履歴更新）を追加"
```

---

## Task 5: 日次ログ追記ロジック（jp_weekday ＋ update_daily_log_text）

`skin_daily_log.md` への追記ロジックを「文字列を受け取り文字列を返す純粋関数」として切り出す（ファイル読み書きは Task 6）。今日の見出しが無ければ新ブロックを追記、あれば「リプ件数」行だけ更新。空欄行は末尾スペース無し。

**Files:**
- Modify: `skin/skin_reply_hunter.py`（`record_reply` の下に追記）
- Test: `skin/tests/test_skin_reply_hunter.py`（末尾に追記）

- [ ] **Step 1: 失敗するテストを追記する**

`skin/tests/test_skin_reply_hunter.py` の末尾に追記:

```python
def test_jp_weekday_2026_06_01_is_monday():
    # 2026-06-01 は月曜日
    assert hunter.jp_weekday("2026-06-01") == "月"

def test_update_daily_log_appends_block_when_heading_missing():
    # 今日の見出しが無ければ、末尾に新しいブロックを追記する
    existing = "# skin 日次ログ\n\n## 2026-05-31（日）\n- リプ件数: 2\n"
    result = hunter.update_daily_log_text(existing, 5, "2026-06-01")
    assert "## 2026-06-01（月）" in result
    assert "- リプ件数: 5" in result
    assert "- 手動投稿数:" in result  # 空欄枠（末尾スペース無し）
    assert "## 2026-05-31（日）" in result  # 既存ブロックは残る

def test_update_daily_log_updates_only_count_when_heading_exists():
    # 今日の見出しが既にあれば、その下のリプ件数行だけ書き換える
    existing = "# skin 日次ログ\n\n## 2026-06-01（月）\n- リプ件数: 0\n- 手動投稿数:\n- 気づき:\n"
    result = hunter.update_daily_log_text(existing, 7, "2026-06-01")
    assert "- リプ件数: 7" in result
    assert "- リプ件数: 0" not in result
    assert result.count("## 2026-06-01（月）") == 1  # 見出しは増えない
```

- [ ] **Step 2: テストを実行して失敗を確認**

Run: `cd /home/kenta_kamijyo && pytest skin/tests/test_skin_reply_hunter.py -k "weekday or daily_log" -v`
Expected: FAIL（`AttributeError: ... 'jp_weekday'`）

- [ ] **Step 3: jp_weekday と update_daily_log_text を実装する**

`skin/skin_reply_hunter.py` の `record_reply` の下に追記:

```python
# 曜日番号（月=0 … 日=6）→ 日本語の曜日1文字
WEEKDAY_JP = ["月", "火", "水", "木", "金", "土", "日"]

def jp_weekday(today):
    """"YYYY-MM-DD" を受け取り、日本語の曜日1文字（月〜日）を返す。"""
    date = datetime.strptime(today, "%Y-%m-%d")
    return WEEKDAY_JP[date.weekday()]

def update_daily_log_text(existing_text, count, today):
    """日次ログの中身（文字列）に、その日のリプ件数を反映して返す純粋関数。

    - 今日の見出し「## YYYY-MM-DD（曜）」が無ければ、末尾に新しいブロックを追記する
    - あれば、その見出しの下にある最初の「- リプ件数:」行だけ書き換える
      （手動投稿数・気づき・他の日の枠・週次サマリーは触らない）
    空欄行は末尾スペースを付けない（既存ファイルの書式に合わせる）。
    """
    weekday = jp_weekday(today)
    heading = "## {}（{}）".format(today, weekday)
    lines = existing_text.split("\n")

    # 今日の見出しが何行目にあるか探す（無ければ None のまま）
    heading_index = None
    for i, line in enumerate(lines):
        if line.strip() == heading:
            heading_index = i
            break

    # 見出しが無ければ、末尾に新しいブロックを追記する
    if heading_index is None:
        block = "\n## {}（{}）\n- リプ件数: {}\n- 手動投稿数:\n- 気づき:\n".format(today, weekday, count)
        return existing_text.rstrip("\n") + "\n" + block

    # 見出しがあれば、その下の最初の「- リプ件数:」行だけ書き換える
    for i in range(heading_index + 1, len(lines)):
        if lines[i].startswith("## "):  # 次の日の見出しに来たら打ち切り
            break
        if lines[i].startswith("- リプ件数:"):
            lines[i] = "- リプ件数: {}".format(count)
            break
    return "\n".join(lines)
```

- [ ] **Step 4: テストを実行して成功を確認**

Run: `cd /home/kenta_kamijyo && pytest skin/tests/test_skin_reply_hunter.py -k "weekday or daily_log" -v`
Expected: PASS（3件）

- [ ] **Step 5: コミット**

```bash
cd /home/kenta_kamijyo && git add skin/skin_reply_hunter.py skin/tests/test_skin_reply_hunter.py && git commit -m "feat: skin_reply_hunter に日次ログ追記ロジックを追加"
```

---

## Task 6: I/O・ブラウザ・対話の組み立て（load/save/open/append/main）

純粋ロジックを束ねて実際に動くツールにする層。ファイル読み書き・ブラウザ起動・対話ループ。ここは単体テスト対象外で、最後にスモークテスト（`q` で即終了）で副作用ゼロを確認する。

**Files:**
- Modify: `skin/skin_reply_hunter.py`（`update_daily_log_text` の下に追記）

- [ ] **Step 1: ファイル入出力とブラウザ起動を追記する**

`skin/skin_reply_hunter.py` に追記:

```python
def load_targets():
    """skin_account_targets.json を読み、targets リストを返す。"""
    with open(TARGETS_PATH, "r", encoding="utf-8") as targets_file:
        data = json.load(targets_file)
    return data["targets"]

def load_history():
    """skin_reply_history.json を読み、history 辞書を返す。無ければ空辞書（初回）。"""
    if not os.path.exists(HISTORY_PATH):
        return {}
    with open(HISTORY_PATH, "r", encoding="utf-8") as history_file:
        data = json.load(history_file)
    return data.get("history", {})

def save_history(history):
    """history を skin_reply_history.json に書き込む（更新日は今日のJST）。"""
    today = datetime.now(JST).strftime("%Y-%m-%d")
    data = {"version": "1.0", "updated_at": today, "history": history}
    with open(HISTORY_PATH, "w", encoding="utf-8") as history_file:
        json.dump(data, history_file, ensure_ascii=False, indent=2)

def open_account(url):
    """ブラウザでURLを開く。WSL2を考えて3段フォールバックする。"""
    # ① Python標準のブラウザ起動を試す
    try:
        if webbrowser.open(url):
            return
    except Exception:
        pass
    # ② ダメなら Windows側のブラウザを cmd.exe 経由で開く
    try:
        subprocess.run(["cmd.exe", "/c", "start", "", url], check=True)
        return
    except Exception:
        pass
    # ③ それも無理なら URL を表示（Kentaが手動で開く）
    print("ブラウザを自動で開けませんでした。下のURLを手動で開いてください:")
    print(url)

def append_daily_log(count, today):
    """skin_daily_log.md にその日のリプ件数を追記する。失敗しても落とさない。"""
    try:
        if os.path.exists(DAILY_LOG_PATH):
            with open(DAILY_LOG_PATH, "r", encoding="utf-8") as log_file:
                existing_text = log_file.read()
        else:
            existing_text = "# skin 日次ログ\n"
        new_text = update_daily_log_text(existing_text, count, today)
        with open(DAILY_LOG_PATH, "w", encoding="utf-8") as log_file:
            log_file.write(new_text)
        print("日次ログに本日のリプ件数（{}件）を記録しました。".format(count))
    except Exception as error:
        # ログ追記に失敗しても件数は履歴に残っているので、警告だけ出して続行
        print("【警告】日次ログの更新に失敗しました（件数は履歴に残っています）: {}".format(error))
```

- [ ] **Step 2: 巡回リスト表示と1件処理を追記する**

`skin/skin_reply_hunter.py` に追記:

```python
def show_round_list(targets, history):
    """巡回リストを画面に表示し、表示順のリストを返す。"""
    ordered = sort_round_list(targets, history)
    print("\n=== 今日の巡回リスト（上から順におすすめ）===")
    for number, target in enumerate(ordered, start=1):
        entry = history.get(target["handle"], {})
        last = entry.get("last_replied_at") or "未"
        total = entry.get("total_replies", 0)
        print("{}. {}（{}）前回:{} 累計:{}".format(
            number, target["handle"], target["theme"], last, total))
        if target.get("notes"):
            print("   メモ: {}".format(target["notes"]))
    return ordered

def handle_one_post(history, today, default_handle=None):
    """投稿文を貼り付け → 下書き3案提示 → 1案選択 → 記録、までを1件分行う。

    戻り値: リプを記録したら handle（文字列）、しなければ None。
    """
    post_text = input("\nリプしたい投稿の本文を貼り付けてEnterEnter（空Enterで戻る）:\n").strip()
    if not post_text:
        return None

    # 投稿文から下書き3案を出す
    drafts, category = suggest_drafts(post_text)
    if category == "generic":
        print("\n（どの話題か自動判定できませんでした。汎用の共感リプを出します）")
    else:
        print("\n【{}】の下書き候補:".format(COMMENT_TEMPLATES[category]["name"] if category != "generic" else "汎用"))
    for number, draft in enumerate(drafts, start=1):
        print("  {}. {}".format(number, draft))

    # どれを使うか選ぶ（空Enterでこの投稿はスキップ）
    choice = input("使う番号を入力（空Enterでスキップ）: ").strip()
    if not choice.isdigit() or not (1 <= int(choice) <= len(drafts)):
        print("スキップしました。")
        return None

    print("\n----- コピー用（これをThreadsアプリに貼って投稿）-----")
    print(drafts[int(choice) - 1])
    print("--------------------------------------------------------")

    # どのアカウントへのリプかを確認（巡回中のアカウントを既定値にできる）
    prompt = "リプ先のhandle"
    if default_handle:
        prompt += "（空Enterで {}）".format(default_handle)
    handle = input(prompt + ": ").strip() or (default_handle or "")
    if not handle:
        print("handleが空のため、記録しませんでした。")
        return None

    record_reply(history, handle, today)
    print("記録しました: {}".format(handle))
    return handle
```

- [ ] **Step 3: main（対話ループ）とエントリポイントを追記する**

`skin/skin_reply_hunter.py` に追記:

```python
def main():
    """対話ループ全体。巡回 → 下書き → 記録を回し、終了時に保存する。"""
    today = datetime.now(JST).strftime("%Y-%m-%d")

    # ターゲット読み込み（無い/壊れていたら巡回できないので終了）
    try:
        targets = load_targets()
    except FileNotFoundError:
        print("【エラー】skin_account_targets.json が見つかりません。終了します。")
        return
    except (json.JSONDecodeError, KeyError):
        print("【エラー】skin_account_targets.json が壊れています。終了します。")
        return

    # 履歴読み込み（壊れていたら自動上書きで累計を消さないよう終了）
    try:
        history = load_history()
    except json.JSONDecodeError:
        print("【エラー】skin_reply_history.json が壊れています。"
              "累計を失わないため上書きせず終了します。中身を確認してください。")
        return

    reply_count = 0
    print("\nskin リプ巡回ツール（Threads APIは使いません。投稿は手動コピペ）")

    try:
        while True:
            ordered = show_round_list(targets, history)
            print("\n操作: 番号=そのアカウントを開く / s=投稿を貼って下書き / q=終了")
            command = input("入力: ").strip().lower()

            if command == "q":
                break
            if command == "s":
                if handle_one_post(history, today):
                    reply_count += 1
                continue
            if command.isdigit() and 1 <= int(command) <= len(ordered):
                target = ordered[int(command) - 1]
                open_account(target["url"])
                if handle_one_post(history, today, default_handle=target["handle"]):
                    reply_count += 1
                continue
            print("無効な入力です。もう一度入力してください。")
    except (EOFError, KeyboardInterrupt):
        print("\n中断しました。")

    # リプを1件でも記録したときだけ保存する（何もしなければファイルを触らない）
    if reply_count > 0:
        save_history(history)
        append_daily_log(reply_count, today)
        print("\n本日のリプ: {}件。お疲れさまでした。".format(reply_count))
    else:
        print("\nリプの記録はありませんでした。ファイルは変更していません。")

# このファイルを直接実行したときだけ main() を動かす
if __name__ == "__main__":
    main()
```

- [ ] **Step 4: スモークテスト（即終了で副作用ゼロを確認）**

Run: `cd /home/kenta_kamijyo && printf 'q\n' | python3 skin/skin_reply_hunter.py`
Expected: 10アカウントの巡回リストが表示され、最後に「リプの記録はありませんでした。ファイルは変更していません。」が出る。

- [ ] **Step 5: 履歴ファイルが作られていないことを確認**

Run: `cd /home/kenta_kamijyo && git status --short`
Expected: `skin/skin_reply_history.json` が出てこない（`q` 即終了では作られない）。

- [ ] **Step 6: コミット**

```bash
cd /home/kenta_kamijyo && git add skin/skin_reply_hunter.py && git commit -m "feat: skin_reply_hunter に対話ループ（巡回・記録・ログ追記）を追加"
```

---

## Task 7: 全体テスト・学習ノート追記・最終コミット

全テストの通過確認、回帰が無いことの確認、学習ノートへの追記。

**Files:**
- Modify: `learning/learning_notes.md`（「作成したプログラム」一覧表に2行追記）

- [ ] **Step 1: 本ツールのテストが全部通ることを確認**

Run: `cd /home/kenta_kamijyo && pytest skin/tests/test_skin_reply_hunter.py -v`
Expected: PASS（12件）

- [ ] **Step 2: リポジトリ全体で回帰が無いことを確認**

Run: `cd /home/kenta_kamijyo && pytest tests/ skin/tests/`
Expected: 既存テストも含めて全てPASS（失敗・エラーが増えていない）

- [ ] **Step 3: 学習ノートに2ファイルを追記する**

`learning/learning_notes.md` の「作成したプログラム」一覧表（ヘッダ `| 日付 | ファイル名 | 内容 | 学んだ要素 |`）の末尾に追記:

```
| 6/1 | skin_comment_templates.py | コメント／リプのテンプレ集を共通モジュールに切り出し | import共通化・DRY・責務分離 |
| 6/1 | skin_reply_hunter.py | skin能動リプ巡回ツール（探す→書く→記録を1コマンド・API不使用） | キーワード判定・安定ソート・対話ループ・Markdown追記・pytest |
```

- [ ] **Step 4: 最終コミット**

```bash
cd /home/kenta_kamijyo && git add learning/learning_notes.md && git commit -m "docs: 学習ノートに skin_reply_hunter と skin_comment_templates を追記"
```

---

## Self-Review

**1. Spec coverage（設計specの各節 → 対応タスク）:**

- §3 スコープ（10アカウント巡回・下書き3案・件数記録）→ Task 6（巡回/対話）・Task 2（下書き）・Task 4/5（記録）
- §4・§2 Threads API不使用 → 全タスクの共通規約に明記、Task 6でもAPI呼び出しなし
- §6 コンポーネント表（各関数）→ `suggest_drafts`=Task2 / `sort_round_list`=Task3 / `record_reply`=Task4 / ログ追記=Task5 / `load/save/open/append/main`=Task6
- §6 テンプレ共通化 → Task 1
- §7 データファイル（`skin_reply_history.json` 構造・ISO日付）→ Task 4/6（`record_reply`・`save_history`）
- §8 下書き生成（キーワード→カテゴリ・同点は若い番号・無該当は汎用）→ Task 2
- §9 巡回順・ブラウザ3段フォールバック・日次ログ追記 → Task 3（順）・Task 6（ブラウザ）・Task 5/6（ログ）
- §10 エラーハンドリング（targets壊れ→終了 / history無し→空 / history壊れ→終了 / ブラウザ→URL表示 / ログ失敗→続行 / 無効入力→再入力）→ Task 6 `main`・`open_account`・`append_daily_log`
- §11 テスト（suggest_drafts/sort_round_list/record_reply/ログ追記）→ Task 2/3/4/5
- §12 ファイル一覧 → ファイル構成の表と一致

**2. Placeholder scan:** TBD・TODO・「あとで実装」などのプレースホルダは無し。各コードステップに実コードを記載済み。

**3. Type consistency:**

- `suggest_drafts(post_text)` → `(drafts, category_key)` を返す（Task2で定義、テストもタプルで受ける）
- `sort_round_list(targets, history)`（Task3）/ `record_reply(history, handle, today)`（Task4）/ `update_daily_log_text(existing_text, count, today)`・`jp_weekday(today)`（Task5）— 後続タスクの呼び出し（Task6の `show_round_list`・`handle_one_post`・`main`・`append_daily_log`）と引数名・戻り値が一致
- パス定数 `TARGETS_PATH` / `HISTORY_PATH` / `DAILY_LOG_PATH` は Task2 で定義し Task6 で使用
- `COMMENT_TEMPLATES` は Task1 で共通モジュール化し、Task2 で `import`、Task2/6 で参照
