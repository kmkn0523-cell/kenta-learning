# ronin Threads「投稿の外側」自動強化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** @RoninWords Threadsの「投稿の外側」（1コメ目シード・CTA・reply_engine設定・週次レポート）をテーマ連動＋完全自動で強化し、reach改善の土台を作る。

**Architecture:** 既存の6カテゴリ分類ロジック（`KEYWORD_MAP`/`classify_category`）を`ronin_reply_hunter.py`/`ronin_reply_engine.py`から新モジュール`ronin_theme_classifier.py`に切り出して共通化し、`ronin_threads_action.py`（1コメ目シード・CTA）からも利用する。Substackの2つの自動投稿スクリプトに公開URL記録を追加し、CTAのテーマ連動を可能にする。最後に`skin_weekly_report.py`を移植した週次レポートを追加する。

**Tech Stack:** Python 3.12 / pytest / requests / GitHub Actions（cron）/ Gmail SMTP（既存Secret `GMAIL_APP_PASSWORD` 共用）

## Global Constraints

- 完全自動施策のみ（手動コピペが必須な`ronin_reply_hunter.py`の改善・`RONIN_REPLY_ENGINE_ENABLED`の有効化は対象外）
- 既存の動作を変えない後方互換を優先する（`pick_generic_seed`・`cta_line_for_cycle`の既存引数無し呼び出しは従来どおりの挙動を返す）
- 週次レポートの送信時刻はskinと同じ月曜 JST08:00（`cron: '0 23 * * 0'`）
- テストは各ファイルと同じ作法（`sys.path.insert(0, str(Path(__file__).resolve().parents[1]))`でronin/をimport可能にする）に従う
- コミットは各タスク完了ごとに実行する

---

### Task 1: `ronin_theme_classifier.py` の新規作成（テーマ分類の共通化）

**Files:**
- Create: `ronin/ronin_theme_classifier.py`
- Test: `ronin/tests/test_ronin_theme_classifier.py`

**Interfaces:**
- Produces: `KEYWORD_MAP`（6カテゴリの英語キーワード辞書、キー"1"〜"6"）/ `classify_category(text: str) -> str | None`（本文からカテゴリキーを返す。無該当は`None`）

- [ ] **Step 1: 新規テストファイルを書く**

```python
# ronin/tests/test_ronin_theme_classifier.py
# ronin_theme_classifier.py のテーマ分類ロジックをテストする
# 実行: pytest ronin/tests/test_ronin_theme_classifier.py -v
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ronin_theme_classifier import KEYWORD_MAP, classify_category


def test_6カテゴリすべてキーワードを持つ():
    assert set(KEYWORD_MAP.keys()) == {"1", "2", "3", "4", "5", "6"}
    for words in KEYWORD_MAP.values():
        assert len(words) >= 3


def test_規律文は1():
    assert classify_category("Discipline and a daily routine build consistency") == "1"


def test_逆境文は2():
    assert classify_category("I failed after a long struggle and setback") == "2"


def test_集中文は3():
    assert classify_category("I can't focus, too much distraction and noise") == "3"


def test_ストイック文は4():
    assert classify_category("Stay calm, this is a stoic mindset lesson") == "4"


def test_熟達文は5():
    assert classify_category("Mastery takes years of practice and craft") == "5"


def test_目的文は6():
    assert classify_category("Still searching for purpose and meaning") == "6"


def test_無該当はNone():
    assert classify_category("The weather is nice and the sky is blue today") is None


def test_同点は番号の若い方():
    # "discipline"（1）と"purpose"（6）が1個ずつ当たる → 若い方の"1"が残る
    assert classify_category("Discipline and purpose both matter") == "1"
```

- [ ] **Step 2: テストを実行して失敗を確認する**

Run: `cd /home/kenta_kamijyo && pytest ronin/tests/test_ronin_theme_classifier.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'ronin_theme_classifier'`）

- [ ] **Step 3: `ronin_theme_classifier.py` を新規作成する**

```python
# ronin_theme_classifier.py
# @RoninWords 投稿・返信テキストのテーマ分類（6カテゴリ）。
# ronin_reply_hunter.py（半自動リプ下書き）・ronin_reply_engine.py（自動リプ本体）・
# ronin_threads_action.py（自動投稿の1コメ目シード・CTA連動）の3箇所で同じ分類ロジックが
# 必要になったため、単一モジュールに切り出した。

# 投稿文に含まれる英語キーワード → どのカテゴリーか の対応表
# （ronin_comment_templates.py の6カテゴリ "1"〜"6" に合わせる）
KEYWORD_MAP = {
    "1": ["discipline", "habit", "routine", "consistency", "willpower", "consistent", "self-control", "show up"],  # 規律・習慣
    "2": ["fail", "failure", "struggle", "adversity", "setback", "quit", "hard time", "resilience", "bounce back"],  # 逆境・打たれ強さ
    "3": ["focus", "distraction", "distracted", "procrastinate", "attention", "deep work", "concentration", "noise"],  # 集中・誘惑
    "4": ["stoic", "stoicism", "mindset", "calm", "anxiety", "fear", "control", "acceptance", "let go"],  # ストイック・心の在り方
    "5": ["master", "mastery", "skill", "craft", "practice", "improve", "discipline of", "expertise", "reps"],  # 熟達・鍛錬
    "6": ["purpose", "meaning", "goal", "vision", "direction", "why", "ikigai", "mission", "calling"],  # 目的・意味
}


def classify_category(text):
    """本文から最も当てはまるカテゴリキー（"1"〜"6"）を返す。
    キーワードが一番多く当たったカテゴリを選ぶ。同点なら番号の若い方（辞書の順序どおり）。
    どのキーワードにも当たらなければ None。"""
    lowered = text.lower()
    best_key = None
    best_hits = 0
    for key, words in KEYWORD_MAP.items():
        hits = sum(1 for word in words if word.lower() in lowered)
        if hits > best_hits:
            best_key = key
            best_hits = hits
    return best_key
```

- [ ] **Step 4: テストを実行して成功を確認する**

Run: `cd /home/kenta_kamijyo && pytest ronin/tests/test_ronin_theme_classifier.py -v`
Expected: PASS（9件）

- [ ] **Step 5: コミット**

```bash
git add ronin/ronin_theme_classifier.py ronin/tests/test_ronin_theme_classifier.py
git commit -m "feat(ronin): テーマ分類ロジックをronin_theme_classifier.pyに切り出す"
```

---

### Task 2: `ronin_reply_hunter.py` を新モジュールに向けて参照変更

**Files:**
- Modify: `ronin/ronin_reply_hunter.py:14-44`

**Interfaces:**
- Consumes: `ronin_theme_classifier.KEYWORD_MAP`（Task 1で作成済み）
- Produces: 変更なし（`KEYWORD_MAP`は引き続き`ronin_reply_hunter`の名前空間からimport可能・既存呼び出し元に影響なし）

- [ ] **Step 1: 既存テストを実行し、現状すべて通ることを確認する**

Run: `cd /home/kenta_kamijyo && pytest ronin/tests/test_ronin_reply_hunter.py -v`
Expected: PASS（変更前の現状確認）

- [ ] **Step 2: `KEYWORD_MAP`の定義をimportに置き換える**

`ronin/ronin_reply_hunter.py:14-44` を以下に置き換える（テンプレ集のimportに続けて、`KEYWORD_MAP`も新モジュールからimportする。定義そのものは削除）:

```python
# テンプレ集・テーマ分類は共通モジュールから読み込む。
# 直接実行（python3 ronin/ronin_reply_hunter.py）でも、pytest 経由でも動くように2通り試す
try:
    from ronin_comment_templates import COMMENT_TEMPLATES, GENERIC_TEMPLATES  # ronin/ が import パスにある時
    from ronin_theme_classifier import KEYWORD_MAP  # ronin/ が import パスにある時
except ImportError:
    from ronin.ronin_comment_templates import COMMENT_TEMPLATES, GENERIC_TEMPLATES  # リポジトリ直下から動かす時
    from ronin.ronin_theme_classifier import KEYWORD_MAP  # リポジトリ直下から動かす時

# -----------------------------------------------
# ファイルの場所（このスクリプトと同じ ronin/ フォルダにある前提）
# -----------------------------------------------
BASE_DIR = Path(__file__).resolve().parent  # このファイルがある ronin/ フォルダ
TARGETS_PATH = BASE_DIR / "ronin_account_targets.json"  # 巡回先アカウントの一覧（読むだけ）
HISTORY_PATH = BASE_DIR / "ronin_reply_history.json"  # アカウント別リプ履歴（読み書き・無ければ初回）
DAILY_LOG_PATH = BASE_DIR / "ronin_daily_log.md"  # 日次ログ（その日のリプ件数を追記）

# 曜日を日本語1文字で出すための表（月曜=0 … 日曜=6 に対応）
WEEKDAY_JP = ["月", "火", "水", "木", "金", "土", "日"]

# どのカテゴリーにも当てはまらなかった時に表示する名前（汎用テンプレ用）
GENERIC_CATEGORY_NAME = "汎用（どのカテゴリにも当てはまらない時）"
```

- [ ] **Step 3: 既存テストを再実行して回帰が無いことを確認する**

Run: `cd /home/kenta_kamijyo && pytest ronin/tests/test_ronin_reply_hunter.py -v`
Expected: PASS（Step 1と同じ件数・全通過。動作は変わっていないことの確認）

- [ ] **Step 4: コミット**

```bash
git add ronin/ronin_reply_hunter.py
git commit -m "refactor(ronin): reply_hunterのKEYWORD_MAPをronin_theme_classifierから読み込む"
```

---

### Task 3: `ronin_reply_engine.py` を新モジュールに向けて参照変更

**Files:**
- Modify: `ronin/ronin_reply_engine.py:16-23`, `ronin/ronin_reply_engine.py:39-50`

**Interfaces:**
- Consumes: `ronin_theme_classifier.classify_category`（Task 1で作成済み）
- Produces: 変更なし（`classify_category`は引き続き`ronin_reply_engine`の名前空間からimport可能）

- [ ] **Step 1: 既存テストを実行し、現状すべて通ることを確認する**

Run: `cd /home/kenta_kamijyo && pytest ronin/tests/test_ronin_reply_engine.py -v`
Expected: PASS（変更前の現状確認）

- [ ] **Step 2: importとローカル定義を置き換える**

`ronin/ronin_reply_engine.py:16-23` を以下に置き換える:

```python
# テンプレ集とテーマ分類は既存モジュールから再利用する。
# 直接実行でも pytest 経由でも動くよう2通り import を試す（既存スクリプトと同じ作法）。
try:
    from ronin_comment_templates import COMMENT_TEMPLATES, GENERIC_TEMPLATES
    from ronin_theme_classifier import classify_category
except ImportError:
    from ronin.ronin_comment_templates import COMMENT_TEMPLATES, GENERIC_TEMPLATES
    from ronin.ronin_theme_classifier import classify_category
```

`ronin/ronin_reply_engine.py:39-50` にあるローカルの`classify_category`定義（下記ブロック）は削除する:

```python
def classify_category(post_text):
    """投稿本文から最も当てはまるテンプレのカテゴリキー（"1"〜"6"）を返す。
    どのキーワードにも当たらなければ None（汎用テンプレを使う合図）。"""
    text = post_text.lower()
    best_key = None
    best_hits = 0
    for key, words in KEYWORD_MAP.items():
        hits = sum(1 for word in words if word.lower() in text)
        if hits > best_hits:
            best_key = key
            best_hits = hits
    return best_key
```

- [ ] **Step 3: 既存テストを再実行して回帰が無いことを確認する**

Run: `cd /home/kenta_kamijyo && pytest ronin/tests/test_ronin_reply_engine.py -v`
Expected: PASS（Step 1と同じ件数・全通過）

- [ ] **Step 4: コミット**

```bash
git add ronin/ronin_reply_engine.py
git commit -m "refactor(ronin): reply_engineのclassify_categoryをronin_theme_classifierから読み込む"
```

---

### Task 4: `ronin_comment_seeder.py` に1コメ目シードのテーマ連動を追加

**Files:**
- Modify: `ronin/ronin_comment_seeder.py`（末尾に追記）
- Test: `ronin/tests/test_ronin_comment_seeder.py`（末尾に追記）

**Interfaces:**
- Consumes: なし（`theme_key`は呼び出し元(`ronin_threads_action.py`のTask 7)が`ronin_theme_classifier.classify_category`で判定した値を渡す）
- Produces: `THEME_SEED_QUESTIONS: dict[str, list[str]]`（キー"1"〜"6"） / `pick_seed_question(count: int, theme_key: str | None) -> str`

- [ ] **Step 1: 失敗するテストを追記する**

`ronin/tests/test_ronin_comment_seeder.py` の末尾に追記:

```python
from ronin_comment_seeder import pick_seed_question, THEME_SEED_QUESTIONS


def test_テーマ連動シードはカテゴリ内でカウントを回す():
    first = pick_seed_question(0, "1")
    assert first == THEME_SEED_QUESTIONS["1"][0]
    # 末尾を超えたら先頭へ
    assert pick_seed_question(len(THEME_SEED_QUESTIONS["1"]), "1") == THEME_SEED_QUESTIONS["1"][0]


def test_テーマ未指定なら汎用にフォールバック():
    assert pick_seed_question(0, None) == pick_generic_seed(0)


def test_未知のテーマキーは汎用にフォールバック():
    assert pick_seed_question(0, "99") == pick_generic_seed(0)


def test_全カテゴリに複数の問いかけがある():
    assert set(THEME_SEED_QUESTIONS.keys()) == {"1", "2", "3", "4", "5", "6"}
    for pool in THEME_SEED_QUESTIONS.values():
        assert len(pool) >= 3
```

- [ ] **Step 2: テストを実行して失敗を確認する**

Run: `cd /home/kenta_kamijyo && pytest ronin/tests/test_ronin_comment_seeder.py -v`
Expected: FAIL（`ImportError: cannot import name 'pick_seed_question'`）

- [ ] **Step 3: `ronin_comment_seeder.py` に実装を追記する**

`ronin/ronin_comment_seeder.py` の末尾に追記:

```python
# 6カテゴリ別の問いかけ。ronin_theme_classifier.classify_category が返すキー"1"〜"6"に対応。
# カテゴリが判定できた投稿には、汎用問いかけより刺さりやすいテーマ別の問いかけを出す。
THEME_SEED_QUESTIONS = {
    "1": [  # Discipline / habits（規律・習慣）
        "What's one habit you've kept even when you didn't feel like it?",
        "Discipline or motivation — which one actually gets you through today?",
        "What does your morning routine look like right now?",
        "Save this if your discipline needs a reminder today.",
        "What's the smallest habit that's made the biggest difference for you?",
    ],
    "2": [  # Resilience / adversity（逆境・打たれ強さ）
        "What's the hardest setback you've come back from?",
        "When did failing actually teach you something useful?",
        "What keeps you going when things get hard?",
        "Save this for the next time you want to quit.",
        "Tell me about a time you bounced back from something that broke you.",
    ],
    "3": [  # Focus / distraction（集中・誘惑）
        "What's stealing your focus most days?",
        "How do you protect your deep work time?",
        "Phone in another room — yes or no?",
        "Save this if your attention span needs a reset.",
        "What's your biggest distraction right now, honestly?",
    ],
    "4": [  # Stoic / mindset（ストイック・心の在り方）
        "What's something you can't control that you're still trying to control?",
        "How do you stay calm when everything feels chaotic?",
        "What would the stoic version of you do right now?",
        "Save this the next time anxiety takes the wheel.",
        "What's one thing you've learned to accept instead of fight?",
    ],
    "5": [  # Mastery / craft（熟達・鍛錬）
        "What craft are you slowly mastering, one rep at a time?",
        "How many years have you put into the thing you're best at?",
        "What does practice look like for you this week?",
        "Save this if you're in the boring middle of mastering something.",
        "What skill are you most proud of building from scratch?",
    ],
    "6": [  # Purpose / meaning（目的・意味）
        "What gives your days meaning right now?",
        "How do you know when you're living with purpose?",
        "What's your 'why' when things get hard?",
        "Save this if you're still searching for your ikigai.",
        "What would you do even if no one paid you for it?",
    ],
}


def pick_seed_question(count, theme_key):
    """カウント(0始まり)でテーマ別の問いかけを順番に選ぶ。
    theme_key が THEME_SEED_QUESTIONS に無ければ汎用問いかけ（pick_generic_seed）にフォールバックする。"""
    pool = THEME_SEED_QUESTIONS.get(theme_key)
    if not pool:
        return pick_generic_seed(count)
    return pool[count % len(pool)]
```

- [ ] **Step 4: テストを実行して成功を確認する**

Run: `cd /home/kenta_kamijyo && pytest ronin/tests/test_ronin_comment_seeder.py -v`
Expected: PASS（既存4件＋新規4件＝8件）

- [ ] **Step 5: コミット**

```bash
git add ronin/ronin_comment_seeder.py ronin/tests/test_ronin_comment_seeder.py
git commit -m "feat(ronin): 1コメ目シードのテーマ連動（THEME_SEED_QUESTIONS）を追加"
```

---

### Task 5: `substack_auto_post.py` に公開URLの自動記録を追加

**Files:**
- Modify: `ronin/substack_auto_post.py:305-367`（`create_and_publish_post`）, `ronin/substack_auto_post.py:422-439`（`main`内の履歴追記）
- Test: `ronin/tests/test_substack_auto_post.py`（末尾に追記）

**Interfaces:**
- Produces: `build_article_url(slug: str | None) -> str | None` / `create_and_publish_post(...) -> tuple[str, str | None]`（戻り値が`post_id`単体から`(post_id, slug)`に変更）
- `progress["history"]`の各エントリに`"url"`キーが追加される（値は`build_article_url(slug)`の結果。`None`の場合もある）

- [ ] **Step 1: 失敗するテストを追記する**

`ronin/tests/test_substack_auto_post.py` の末尾に追記:

```python
from substack_auto_post import build_article_url, PUBLICATION_URL


def test_build_article_url_slugありならURLを組み立てる():
    assert build_article_url("ichi-go-ichi-e") == f"{PUBLICATION_URL}/p/ichi-go-ichi-e"


def test_build_article_url_slugなしはNone():
    assert build_article_url(None) is None
    assert build_article_url("") is None
```

- [ ] **Step 2: テストを実行して失敗を確認する**

Run: `cd /home/kenta_kamijyo && pytest ronin/tests/test_substack_auto_post.py -v`
Expected: FAIL（`ImportError: cannot import name 'build_article_url'`）

- [ ] **Step 3: `build_article_url`を追加し、`create_and_publish_post`とその呼び出し元を変更する**

`ronin/substack_auto_post.py:305-367` の`create_and_publish_post`関数の直前に追加:

```python
def build_article_url(slug):
    """Substack記事のslugから公開URLを組み立てる。slugが無ければNoneを返す
    （CTAのテーマ連動で、この記事にリンクできるかどうかの判定に使う）。"""
    if not slug:
        return None
    return f"{PUBLICATION_URL}/p/{slug}"
```

`create_and_publish_post`関数内、ドラフト作成部分（既存の`post = draft_resp.json(); post_id = post["id"]`の直後）に`slug`取得を追加し、関数の戻り値を`(post_id, slug)`に変更する:

```python
    post    = draft_resp.json()
    post_id = post["id"]
    slug    = post.get("slug")
    print(f"  ドラフトID: {post_id}", flush=True)
```

関数の末尾（`return post_id`）を以下に変更:

```python
    return post_id, slug
```

`main()`内の呼び出し部分（`post_id = create_and_publish_post(proverb, image_path, session=session)`）を以下に変更:

```python
    post_id, slug = create_and_publish_post(proverb, image_path, session=session)
```

`main()`内の履歴追記部分（`progress["history"].append(...)`）を以下に変更:

```python
    progress["history"].append({
        "date":    now,
        "day":     day,
        "post_id": post_id,
        "title":   title,
        "url":     build_article_url(slug),
    })
```

- [ ] **Step 4: テストを実行して成功を確認する**

Run: `cd /home/kenta_kamijyo && pytest ronin/tests/test_substack_auto_post.py -v`
Expected: PASS（既存4件＋新規2件＝6件）

- [ ] **Step 5: コミット**

```bash
git add ronin/substack_auto_post.py ronin/tests/test_substack_auto_post.py
git commit -m "feat(ronin): substack_auto_postで公開記事URLをprogressに記録する"
```

---

### Task 6: `substack_deep_dive_auto_post.py` に公開URLの自動記録を追加

**Files:**
- Modify: `ronin/substack_deep_dive_auto_post.py:217-272`（`create_and_publish_post`）, `ronin/substack_deep_dive_auto_post.py:343-354`（`main`内の履歴追記）
- Create: `ronin/tests/test_substack_deep_dive_auto_post.py`

**Interfaces:**
- Produces: `build_article_url(slug: str | None) -> str | None` / `create_and_publish_post(...) -> tuple[str, str | None]`（Task 5と同じ形。ファイルが別なので関数は別定義）
- `progress["history"]`の各エントリに`"url"`キーが追加される

- [ ] **Step 1: 新規テストファイルを書く**

```python
# ronin/tests/test_substack_deep_dive_auto_post.py
# substack_deep_dive_auto_post.py の公開URL組み立てロジックをテストする
# 実行: pytest ronin/tests/test_substack_deep_dive_auto_post.py -v
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from substack_deep_dive_auto_post import build_article_url, PUBLICATION_URL


def test_build_article_url_slugありならURLを組み立てる():
    assert build_article_url("the-hawk-hides-its-talons") == f"{PUBLICATION_URL}/p/the-hawk-hides-its-talons"


def test_build_article_url_slugなしはNone():
    assert build_article_url(None) is None
    assert build_article_url("") is None
```

- [ ] **Step 2: テストを実行して失敗を確認する**

Run: `cd /home/kenta_kamijyo && pytest ronin/tests/test_substack_deep_dive_auto_post.py -v`
Expected: FAIL（`ModuleNotFoundError`または`ImportError`）

- [ ] **Step 3: `build_article_url`を追加し、`create_and_publish_post`とその呼び出し元を変更する**

`ronin/substack_deep_dive_auto_post.py:217-272` の`create_and_publish_post`関数の直前に追加:

```python
def build_article_url(slug):
    """Substack記事のslugから公開URLを組み立てる。slugが無ければNoneを返す
    （CTAのテーマ連動で、この記事にリンクできるかどうかの判定に使う）。"""
    if not slug:
        return None
    return f"{PUBLICATION_URL}/p/{slug}"
```

`create_and_publish_post`関数内、ドラフト作成部分（既存の`post_id = draft_resp.json()["id"]`）を以下に変更:

```python
    draft_json = draft_resp.json()
    post_id    = draft_json["id"]
    slug       = draft_json.get("slug")
    print(f"  ドラフトID: {post_id}", flush=True)
```

関数の末尾（`return post_id`）を以下に変更:

```python
    return post_id, slug
```

`main()`内の呼び出し部分（`post_id = create_and_publish_post(session, article, card_day)`）を以下に変更:

```python
    post_id, slug = create_and_publish_post(session, article, card_day)
```

`main()`内の履歴追記部分（`progress["history"].append(...)`）を以下に変更:

```python
    progress["history"].append({
        "date":     now,
        "card_day": card_day,
        "japanese": japanese,
        "post_id":  post_id,
        "title":    article["title"],
        "url":      build_article_url(slug),
    })
```

- [ ] **Step 4: テストを実行して成功を確認する**

Run: `cd /home/kenta_kamijyo && pytest ronin/tests/test_substack_deep_dive_auto_post.py -v`
Expected: PASS（2件）

- [ ] **Step 5: コミット**

```bash
git add ronin/substack_deep_dive_auto_post.py ronin/tests/test_substack_deep_dive_auto_post.py
git commit -m "feat(ronin): substack_deep_dive_auto_postで公開記事URLをprogressに記録する"
```

---

### Task 7: `ronin_threads_action.py` に1コメ目シード・CTAのテーマ連動を組み込む

**Files:**
- Modify: `ronin/ronin_threads_action.py:12-15`（import）, `ronin/ronin_threads_action.py:149-157`（`cta_line_for_cycle`）, `ronin/ronin_threads_action.py:290-368`（`post_once`）
- Test: `ronin/tests/test_ronin_threads_action.py`（先頭のimportと末尾に追記）

**Interfaces:**
- Consumes: `ronin_theme_classifier.classify_category`（Task 1） / `ronin_comment_seeder.pick_seed_question`（Task 4） / Task 5・6で`substack_progress.json`/`deep_dive_progress.json`の履歴エントリに追加された`"url"`キー
- Produces: `load_substack_articles_with_url() -> list[dict]`（各要素`{"title": str, "url": str}`） / `pick_theme_substack_line(theme_key: str | None, articles: list[dict]) -> str` / `cta_line_for_cycle(history_count: int, theme_key: str | None = None, substack_articles: list[dict] | None = None) -> str`（引数追加・既存の呼び出し方は互換）

- [ ] **Step 1: 失敗するテストを追記する**

`ronin/tests/test_ronin_threads_action.py` の先頭のimportブロックに`json`を追加:

```python
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ronin_threads_action as action
```

ファイル末尾に追記:

```python
# ------- CTAのSubstackテーマ連動 -------

def test_CTAサイクル_テーマ一致する記事があればそのURLを使う():
    articles = [{"title": "The Discipline of Showing Up Every Day",
                 "url": "https://roninwords.substack.com/p/discipline-1"}]
    line = action.cta_line_for_cycle(7, theme_key="1", substack_articles=articles)
    assert "https://roninwords.substack.com/p/discipline-1" in line


def test_CTAサイクル_テーマ一致なしはプロフィールURLにフォールバック():
    articles = [{"title": "The Hawk Hides Its Talons",
                 "url": "https://roninwords.substack.com/p/hawk"}]
    line = action.cta_line_for_cycle(7, theme_key="1", substack_articles=articles)
    assert line == action.SUBSTACK_LINE


def test_CTAサイクル_theme_keyがNoneならプロフィールURL():
    line = action.cta_line_for_cycle(7, theme_key=None, substack_articles=[{"title": "x", "url": "y"}])
    assert line == action.SUBSTACK_LINE


def test_load_substack_articles_with_url_ファイル無しは空リスト(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert action.load_substack_articles_with_url() == []


def test_load_substack_articles_with_url_urlとtitleがある記事だけ拾う(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "substack").mkdir()
    (tmp_path / "substack" / "substack_progress.json").write_text(
        json.dumps({"history": [
            {"title": "A — B", "url": "https://x/p/a"},
            {"title": "C — D"},  # urlなし→対象外
        ]}), encoding="utf-8",
    )
    (tmp_path / "substack" / "deep_dive_progress.json").write_text(
        json.dumps({"history": [{"title": "E", "url": "https://x/p/e"}]}), encoding="utf-8",
    )
    articles = action.load_substack_articles_with_url()
    assert {"title": "A — B", "url": "https://x/p/a"} in articles
    assert {"title": "E", "url": "https://x/p/e"} in articles
    assert len(articles) == 2


# ------- 1コメ目シードのテーマ連動（post_once統合） -------

def test_dry_run_教え投稿は本文をテーマ分類してseedを組み立てる(capsys, tmp_path, monkeypatch):
    prog = tmp_path / "prog.json"
    prog.write_text('{"index": 0, "engagement_index": 0, "history": []}', encoding="utf-8")
    monkeypatch.setattr(action, "PROGRESS_FILE", str(prog))
    monkeypatch.setattr(
        action, "flatten_posts",
        lambda: [{"day": 1, "type": "morning", "content": "Discipline and a daily routine build consistency."}],
    )

    def fail_post(*a, **k):
        raise AssertionError("dry-runでAPIを呼んではいけない")

    monkeypatch.setattr(action, "post_to_threads", fail_post)
    action.post_once(dry_run=True)

    out = capsys.readouterr().out
    # テーマ1（規律）に分類され、THEME_SEED_QUESTIONS["1"]の先頭が使われる
    assert action.ronin_comment_seeder.THEME_SEED_QUESTIONS["1"][0][:30] in out
```

- [ ] **Step 2: テストを実行して失敗を確認する**

Run: `cd /home/kenta_kamijyo && pytest ronin/tests/test_ronin_threads_action.py -v`
Expected: FAIL（`cta_line_for_cycle() got an unexpected keyword argument 'theme_key'` / `AttributeError: module 'ronin_threads_action' has no attribute 'load_substack_articles_with_url'`）

- [ ] **Step 3: importを追加する**

`ronin/ronin_threads_action.py:12-15` を以下に置き換える:

```python
# ronin専用モジュール（同じ ronin/ フォルダ内・cd ronin で実行されるためベアimport）
import ronin_hashtags          # ハッシュタグ・ローテーション
import ronin_engagement        # engagement在庫（コメント誘発投稿）
import ronin_comment_seeder    # 1コメ目テキスト生成
import ronin_theme_classifier  # 投稿本文のテーマ分類（1コメ目・CTA連動に使う）
```

- [ ] **Step 4: `cta_line_for_cycle`をテーマ連動に拡張する**

`ronin/ronin_threads_action.py:149-157` を以下に置き換える:

```python
def load_substack_articles_with_url():
    """Substackの進捗履歴（カード・deep-dive両方）から、公開URLを持つ記事の一覧を返す。
    各要素は {"title": str, "url": str}。ファイルが無い/壊れていても空リストを返す（投稿は止めない）。"""
    articles = []
    for filename in ("substack/substack_progress.json", "substack/deep_dive_progress.json"):
        try:
            with open(filename, encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            continue
        for entry in data.get("history", []):
            title = entry.get("title")
            url = entry.get("url")
            if title and url:
                articles.append({"title": title, "url": url})
    return articles


def pick_theme_substack_line(theme_key, articles):
    """テーマに合うSubstack記事のURLでCTA行を作る。無ければ既存のプロフィールURLにフォールバック。"""
    for article in articles:
        if ronin_theme_classifier.classify_category(article["title"]) == theme_key:
            return f"📖 Full deep dive on this teaching → {article['url']}"
    return SUBSTACK_LINE


def cta_line_for_cycle(history_count, theme_key=None, substack_articles=None):
    """14投稿サイクルで、1コメ目に載せるCTAリンク行を返す（通常回は空文字）。
    余り0=Gumroad / 余り7=Substack（従来の本文CTAと同じ周期）。
    余り7のときは theme_key に合う公開済みSubstack記事があればそのURLを使い、
    無ければプロフィールURL（SUBSTACK_LINE）にフォールバックする。"""
    cycle = history_count % 14
    if cycle == 0:
        return GUMROAD_LINE
    if cycle == 7:
        if theme_key is None:
            return SUBSTACK_LINE
        articles = substack_articles if substack_articles is not None else load_substack_articles_with_url()
        return pick_theme_substack_line(theme_key, articles)
    return ""
```

- [ ] **Step 5: `post_once`でテーマ分類を組み込む**

`ronin/ronin_threads_action.py:290-368` の`post_once`関数内、種別決定〜CTA決定の部分（下記の既存3行）:

```python
    kind = decide_post_kind(history_count)
    hashtags = ronin_hashtags.pick_hashtag_set(history_count)
    cta_line = cta_line_for_cycle(history_count)

    image_url = None  # engagementは画像なし、teachingは後で設定

    if kind == "engagement":
        eng_posts = ronin_engagement.load_engagement_posts()
        if eng_posts:
            eng_index = progress.get("engagement_index", 0)
            eng = ronin_engagement.pick_engagement_post(eng_posts, eng_index)
            content = eng["text"]
            seed_base = eng["seed_comment"]
            label = f"engagement {eng['id']}"
        else:
            # 在庫が無ければ教えの投稿にフォールバック
            print("⚠️ engagement在庫が空。教えの投稿にフォールバックします。")
            kind = "teaching"

    if kind == "teaching":
        index = progress.get("index", 0) % len(teaching_posts)
        post = teaching_posts[index]
        content = post["content"]
        seed_base = ronin_comment_seeder.pick_generic_seed(history_count)
        image_url = get_image_url(post["day"])
        label = f"Day{post['day']:02d} {post['type']}"
```

を、以下に置き換える（`theme_key`の判定を追加し、`pick_generic_seed`を`pick_seed_question`に変更、`cta_line`の計算を`content`確定後に移動）:

```python
    kind = decide_post_kind(history_count)
    hashtags = ronin_hashtags.pick_hashtag_set(history_count)

    image_url = None  # engagementは画像なし、teachingは後で設定
    theme_key = None  # 投稿本文のテーマ分類（1コメ目・CTA連動に使う）

    if kind == "engagement":
        eng_posts = ronin_engagement.load_engagement_posts()
        if eng_posts:
            eng_index = progress.get("engagement_index", 0)
            eng = ronin_engagement.pick_engagement_post(eng_posts, eng_index)
            content = eng["text"]
            theme_key = ronin_theme_classifier.classify_category(content)
            seed_base = eng["seed_comment"]
            label = f"engagement {eng['id']}"
        else:
            # 在庫が無ければ教えの投稿にフォールバック
            print("⚠️ engagement在庫が空。教えの投稿にフォールバックします。")
            kind = "teaching"

    if kind == "teaching":
        index = progress.get("index", 0) % len(teaching_posts)
        post = teaching_posts[index]
        content = post["content"]
        theme_key = ronin_theme_classifier.classify_category(content)
        seed_base = ronin_comment_seeder.pick_seed_question(history_count, theme_key)
        image_url = get_image_url(post["day"])
        label = f"Day{post['day']:02d} {post['type']}"

    cta_line = cta_line_for_cycle(history_count, theme_key=theme_key)
```

- [ ] **Step 6: テストを実行して成功を確認する**

Run: `cd /home/kenta_kamijyo && pytest ronin/tests/test_ronin_threads_action.py -v`
Expected: PASS（既存7件＋新規6件＝13件）

- [ ] **Step 7: ronin/tests配下すべてを実行して回帰が無いことを確認する**

Run: `cd /home/kenta_kamijyo && pytest ronin/tests/ -v`
Expected: PASS（全件）

- [ ] **Step 8: コミット**

```bash
git add ronin/ronin_threads_action.py ronin/tests/test_ronin_threads_action.py
git commit -m "feat(ronin): 1コメ目シードとCTAをテーマ連動にする（threads_action）"
```

---

### Task 8: `ronin_reply_engine.py`のOPENERS拡充と設定値の見直し（本稼働はしない）

**Files:**
- Modify: `ronin/ronin_reply_engine.py:55`（`OPENERS`）
- Modify: `ronin/ronin_reply_engine_config.json`（`daily_cap`/`per_run`）

**Interfaces:**
- Consumes: なし
- Produces: `OPENERS`（5件→8件、既存の`compose_reply`はこのリストから動的に組み合わせを作るため変更不要）

- [ ] **Step 1: 既存テストを実行し、現状すべて通ることを確認する**

Run: `cd /home/kenta_kamijyo && pytest ronin/tests/test_ronin_reply_engine.py -v`
Expected: PASS（変更前の現状確認。`compose_reply`のテストは`OPENERS`から動的に組み合わせを計算するため、件数が増えても壊れない）

- [ ] **Step 2: `OPENERS`を5件→8件に拡充する**

`ronin/ronin_reply_engine.py:55` を以下に置き換える:

```python
OPENERS = ["", "So true. ", "Well said. ", "Needed this. ", "This hits. ",
           "Real talk. ", "Exactly this. ", "Feeling this. "]
```

- [ ] **Step 3: 設定値を見直す**

`ronin/ronin_reply_engine_config.json` の`daily_cap`と`per_run`を以下に変更する（skinの見直し比率に合わせる。本稼働はしないが、将来Meta App Reviewが通った際にすぐ安全側の値で動かせるようにする）:

```json
{
  "my_username": "roninwords",
  "keywords": ["discipline", "stoicism", "stoic", "self improvement", "consistency", "procrastination", "deep work", "mindset", "ikigai", "purpose", "mastery", "hard work", "self discipline", "focus", "resilience", "growth mindset", "build habits", "stay consistent", "self mastery", "mental toughness"],
  "daily_cap": 10,
  "per_run": 2,
  "max_per_author_per_day": 1,
  "min_post_length": 20,
  "max_urls": 1,
  "recent_window": 60,
  "min_sleep_seconds": 20,
  "max_sleep_seconds": 90
}
```

- [ ] **Step 4: テストを再実行して回帰が無いことを確認する**

Run: `cd /home/kenta_kamijyo && pytest ronin/tests/test_ronin_reply_engine.py -v`
Expected: PASS（Step 1と同じ件数・全通過）

- [ ] **Step 5: コミット**

```bash
git add ronin/ronin_reply_engine.py ronin/ronin_reply_engine_config.json
git commit -m "chore(ronin): reply_engineのOPENERS拡充とdaily_cap/per_run見直し（本稼働はしない）"
```

---

### Task 9: 週次自動レポート（`ronin_weekly_report.py` + GitHub Actions）

**Files:**
- Create: `ronin/ronin_weekly_report.py`
- Create: `ronin/tests/test_ronin_weekly_report.py`
- Create: `.github/workflows/ronin_weekly_report.yml`

**Interfaces:**
- Consumes: `ronin/ronin_analytics.json`の`posts_history`（既存フィールド: `day`/`type`/`post_id`/`posted_at`/`likes`/`comments`/`shares`/`views`/`engagement_rate`） / `ronin/ronin_optimization_index.json`の`pattern_ranking`（既存フィールド: `day`/`score`/`priority`）
- Produces: `recent_posts` / `summarize` / `top_posts` / `suggest_next_actions` / `build_report` / `send_report_email` / `main`（`skin_weekly_report.py`と同じ関数構成。`ab_summary`は無い代わりに`pattern_ranking`をそのまま表示に使う）

- [ ] **Step 1: 新規テストファイルを書く**

```python
# ronin/tests/test_ronin_weekly_report.py
# ronin_weekly_report.py の純粋ロジックをテストする（ネットワーク・実ファイル書き出しは対象外）
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ronin_weekly_report import (
    recent_posts,
    summarize,
    top_posts,
    suggest_next_actions,
    build_report,
)

JST = timezone(timedelta(hours=9))
TODAY = datetime(2026, 7, 1, 12, 0, tzinfo=JST)


def _post(days_ago, views=10, likes=0, engagement=10.0, type_="morning"):
    """TODAYから days_ago 日前の投稿データを作る（テスト用）"""
    posted = (TODAY - timedelta(days=days_ago)).astimezone(timezone.utc)
    return {
        "posted_at": posted.strftime("%Y-%m-%dT%H:%M:%S+0000"),
        "views": views,
        "likes": likes,
        "engagement_rate": engagement,
        "type": type_,
    }


def test_recent_posts_keeps_within_window():
    history = [_post(1), _post(6), _post(8)]
    result = recent_posts(history, TODAY, days=7)
    assert len(result) == 2


def test_recent_posts_skips_broken_date():
    history = [_post(1), {"posted_at": "こわれた日付", "views": 10}]
    result = recent_posts(history, TODAY)
    assert len(result) == 1


def test_summarize_computes_averages():
    posts = [_post(1, views=10, likes=1), _post(2, views=20, likes=0)]
    s = summarize(posts)
    assert s["count"] == 2
    assert s["avg_views"] == 15.0
    assert s["avg_likes"] == 0.5
    assert s["total_views"] == 30


def test_summarize_empty_is_zero():
    s = summarize([])
    assert s == {"count": 0, "avg_views": 0.0, "avg_likes": 0.0, "avg_engagement": 0.0, "total_views": 0}


def test_top_posts_sorts_by_views():
    posts = [_post(1, views=5), _post(2, views=20), _post(3, views=10)]
    tops = top_posts(posts, n=2)
    assert [p["views"] for p in tops] == [20, 10]


def test_suggest_actions_flags_zero_likes_and_low_views():
    s = summarize([_post(1, views=10, likes=0, engagement=2.0)])
    actions = suggest_next_actions(s)
    joined = " ".join(actions)
    assert "1コメ目" in joined
    assert "reply_hunter" in joined


def test_suggest_actions_no_data():
    actions = suggest_next_actions(summarize([]))
    assert "データ" in actions[0]


def test_build_report_has_sections():
    history = [_post(1, views=10, likes=0)]
    report = build_report(history, TODAY, pattern_ranking=[{"day": 140, "score": 14.3, "priority": 1}])
    assert "週次レポート" in report
    assert "直近7日のサマリー" in report
    assert "高反応パターン" in report
    assert "次の打ち手" in report


def test_build_report_pattern_ranking省略可():
    history = [_post(1, views=10, likes=0)]
    report = build_report(history, TODAY)
    assert "週次レポート" in report
    assert "高反応パターン" not in report
```

- [ ] **Step 2: テストを実行して失敗を確認する**

Run: `cd /home/kenta_kamijyo && pytest ronin/tests/test_ronin_weekly_report.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'ronin_weekly_report'`）

- [ ] **Step 3: `ronin_weekly_report.py`を新規作成する**

```python
#!/usr/bin/env python3
# ronin_weekly_report.py
# @RoninWords Threads の「今週どうだった？」を自動でまとめる週次レポート。
# 既存の分析データ（ronin_analytics.json）と最適化ランキング（ronin_optimization_index.json）を
# 束ねて、直近7日の数字・伸びた投稿・次の打ち手を人間が読める形で出す。
# 使い方: python3 ronin/ronin_weekly_report.py
#   → 画面に表示しつつ ronin/ronin_weekly_report.md に書き出す。

import json     # JSONを読む道具
import os       # ファイルの場所を組み立てる道具
import re       # 日時の "+0000" を直す道具
import smtplib  # メールを送る道具（週次レポートをGmailで通知）
from datetime import datetime, timezone, timedelta  # 日時を扱う道具
from email.mime.text import MIMEText  # メール本文を作る道具

MAIL_ADDR = "kmkn0523@gmail.com"  # 送信元・送信先（どちらも自分のGmail）

# ファイルの場所（このスクリプトと同じ ronin/ にある前提）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ANALYTICS_PATH = os.path.join(BASE_DIR, "ronin_analytics.json")
OPTIMIZATION_PATH = os.path.join(BASE_DIR, "ronin_optimization_index.json")
REPORT_PATH = os.path.join(BASE_DIR, "ronin_weekly_report.md")
JST = timezone(timedelta(hours=9))  # 日本時間


def _parse_dt(text):
    """Threads APIの日時 "+0000"（コロン無し）を Python が読める形に直して datetime にする。"""
    text = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", text)  # 末尾 +0000 → +00:00
    return datetime.fromisoformat(text)


def recent_posts(history, today, days=7):
    """投稿履歴から、today を基準に直近 days 日ぶんの投稿だけを取り出す。"""
    cutoff = today - timedelta(days=days)  # この日時より新しい投稿だけ残す
    result = []
    for post in history:
        posted_at = post.get("posted_at")
        if not posted_at:  # 投稿日時が無いデータは飛ばす
            continue
        try:
            posted_dt = _parse_dt(posted_at)
        except ValueError:  # 日付が壊れていたら飛ばす（全体は止めない）
            continue
        if posted_dt >= cutoff:
            result.append(post)
    return result


def summarize(posts):
    """投稿リストから平均viewsなどの要約を作る。空なら全部0で返す。"""
    count = len(posts)
    if count == 0:
        return {"count": 0, "avg_views": 0.0, "avg_likes": 0.0, "avg_engagement": 0.0, "total_views": 0}
    total_views = sum(post.get("views", 0) for post in posts)
    total_likes = sum(post.get("likes", 0) for post in posts)
    total_engagement = sum(post.get("engagement_rate", 0) for post in posts)
    return {
        "count": count,
        "avg_views": total_views / count,
        "avg_likes": total_likes / count,
        "avg_engagement": total_engagement / count,
        "total_views": total_views,
    }


def top_posts(posts, n=5, key="views"):
    """指定キー（既定はviews）の大きい順に上位n件を返す。"""
    return sorted(posts, key=lambda post: post.get(key, 0), reverse=True)[:n]


def suggest_next_actions(summary):
    """要約の数字を見て、次にやるべきことをルールベースで提案する。"""
    if summary["count"] == 0:
        return ["直近7日の投稿データがありません。ronin_analytics_daily.ymlが動いているか確認してください。"]
    actions = []
    if summary["avg_likes"] < 1:
        actions.append("いいねが極小です。1コメ目のテーマ連動シード（ronin_comment_seeder）とengagement投稿の比率を見直してください。")
    if summary["avg_views"] < 30:
        actions.append("閲覧が伸びていません。reply_hunter.pyでの手動リプ巡回（reachの最強手段）を今週やってみてください。")
    if summary["avg_engagement"] < 5:
        actions.append("エンゲージ率が低めです。ハッシュタグセットのローテと配信時刻（ET基準）が効いているか確認してください。")
    if not actions:
        actions.append("主要指標は安定しています。CTAのSubstackテーマ連動が実際にクリックされているか確認してください。")
    return actions


def build_report(history, today, pattern_ranking=None):
    """週次レポートの本文（文字列）を組み立てる。"""
    recent = recent_posts(history, today)
    summary = summarize(recent)
    lines = []
    lines.append(f"# ronin Threads 週次レポート（{today.strftime('%Y-%m-%d')}）")
    lines.append("")
    lines.append("## 直近7日のサマリー")
    lines.append(f"- 投稿数: {summary['count']}件")
    lines.append(f"- 平均閲覧（views）: {summary['avg_views']:.1f}")
    lines.append(f"- 平均いいね: {summary['avg_likes']:.2f}")
    lines.append(f"- 平均エンゲージ率: {summary['avg_engagement']:.2f}%")
    lines.append(f"- 合計閲覧: {summary['total_views']}")
    lines.append("")
    lines.append("## 伸びた投稿 Top5（views順）")
    if recent:
        for post in top_posts(recent):
            lines.append(
                f"- views {post.get('views', 0)} / いいね {post.get('likes', 0)}"
                f" / {post.get('type', '不明')}"
            )
    else:
        lines.append("- （対象投稿なし）")
    lines.append("")
    if pattern_ranking:
        lines.append("## 高反応パターン Top5（優先度順）")
        for entry in pattern_ranking[:5]:
            lines.append(f"- Day{entry.get('day')} / score {entry.get('score')} / 優先度{entry.get('priority')}")
        lines.append("")
    lines.append("## 次の打ち手")
    for action in suggest_next_actions(summary):
        lines.append(f"- {action}")
    return "\n".join(lines)


def send_report_email(report_text, today):
    """週次レポートをGmailで自分宛に送る。パスワード未設定なら静かにスキップ。"""
    password = os.environ.get("GMAIL_APP_PASSWORD", "")
    if not password:  # ローカル実行時はパスワードが無いので送らない（既存スクリプトと同じ作法）
        print("GMAIL_APP_PASSWORD が未設定のため、メール送信はスキップします。")
        return
    msg = MIMEText(report_text, "plain", "utf-8")  # レポート本文をそのままメールにする
    msg["From"] = MAIL_ADDR
    msg["To"] = MAIL_ADDR
    msg["Subject"] = f"【ronin週次レポート】{today.strftime('%Y-%m-%d')}"
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:  # Gmailの安全な送信口
        server.login(MAIL_ADDR, password)
        server.send_message(msg)
    print("週次レポートをメール送信しました。")


def main():
    """実データを読んでレポートを画面とファイルに出す。"""
    with open(ANALYTICS_PATH, encoding="utf-8") as f:
        history = json.load(f).get("posts_history", [])
    pattern_ranking = []
    try:  # 最適化インデックスは大きいが pattern_ranking キーだけ使う（読むだけ・書き換えない）
        with open(OPTIMIZATION_PATH, encoding="utf-8") as f:
            pattern_ranking = json.load(f).get("pattern_ranking", [])
    except (FileNotFoundError, json.JSONDecodeError):
        pattern_ranking = []
    today = datetime.now(JST)
    report = build_report(history, today, pattern_ranking)
    print(report)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report + "\n")
    print(f"\n→ 書き出し: {REPORT_PATH}")
    send_report_email(report, today)  # GMAIL_APP_PASSWORD があればメール通知


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: テストを実行して成功を確認する**

Run: `cd /home/kenta_kamijyo && pytest ronin/tests/test_ronin_weekly_report.py -v`
Expected: PASS（9件）

- [ ] **Step 5: GitHub Actionsワークフローを新規作成する**

```yaml
# ronin_weekly_report.yml
# ronin Threads の週次レポートを毎週月曜JST朝に自動生成し、Gmailで通知する。
# 直近7日の数字・伸びた投稿・高反応パターン・次の打ち手をまとめる（ronin_weekly_report.py）。

name: ronin 週次レポート

on:
  schedule:
    - cron: '0 23 * * 0'  # JST 月曜 08:00（UTC 日曜23:00）
  workflow_dispatch:  # 手動実行（テスト用）

concurrency:
  group: ronin-weekly-report  # 二重起動・push競合を防ぐ専用グループ
  cancel-in-progress: false

jobs:
  weekly-report:
    runs-on: ubuntu-latest
    permissions:
      contents: write  # レポートmdのpushに必要
    steps:
      - name: リポジトリをチェックアウト
        uses: actions/checkout@v4

      - name: Python 3.12 をセットアップ
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: 週次レポートを生成してメール送信
        env:
          GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
        run: cd ronin && python ronin_weekly_report.py

      - name: レポートをGitにコミット＆プッシュ
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add ronin/ronin_weekly_report.md
          if ! git diff --staged --quiet; then
            git commit -m "自動同期: ronin週次レポート更新"
            for i in 1 2 3; do
              git pull --rebase origin main && git push && break
              echo "push失敗 リトライ $i/3..."
              sleep 5
            done
          fi
```

このファイルを `.github/workflows/ronin_weekly_report.yml` に保存する。

- [ ] **Step 6: ronin/tests配下すべてを実行して最終回帰確認する**

Run: `cd /home/kenta_kamijyo && pytest ronin/tests/ -v`
Expected: PASS（全件）

- [ ] **Step 7: コミット**

```bash
git add ronin/ronin_weekly_report.py ronin/tests/test_ronin_weekly_report.py .github/workflows/ronin_weekly_report.yml
git commit -m "feat(ronin): 週次自動レポート（Gmail通知）を追加"
```

---

## 全タスク完了後の最終確認

- [ ] **Step 1: リポジトリ全体のpytestを実行する**

Run: `cd /home/kenta_kamijyo && pytest tests/ skin/tests/ ronin/tests/ -v`
Expected: PASS（全件・既存分含めて回帰なし）

- [ ] **Step 2: 新規ワークフローの構文をローカルで確認する（GitHub Actionsは実行しない）**

Run: `cd /home/kenta_kamijyo && python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ronin_weekly_report.yml'))" 2>/dev/null || python3 -c "import json,sys; sys.exit(0)"`

（`yaml`パッケージが無ければ目視でインデントを確認する。実際のcron発火は次の月曜まで待つ・`workflow_dispatch`で手動テスト可能）
