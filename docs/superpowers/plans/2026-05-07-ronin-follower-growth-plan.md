# @RoninWords フォロワー成長機構 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** @RoninWords Threads アカウントに、データ駆動型のフォロワー成長機構を実装する（Day1-20 学習フェーズ、Day21+ 最適化フェーズ）

**Architecture:** skin の実装をミラーリング。毎日 06:00 に Threads API からデータ取得 → 07:00 に分析・最適化インデックス生成 → Day21 以降は最適ハッシュタグセット＋高反応パターンで自動投稿。

**Tech Stack:** Python3（requests）、JSON（ローカル管理）、GitHub Actions（自動実行）、Threads API v1.0

---

## ファイル構成

### 修正対象
- `ronin/threads_posts.json` - 既存の投稿データに、ハッシュタグセット3種（A: 基本、B: アクション、C: 感情）を追加

### 新規作成
- `ronin/ronin_analytics.json` - 毎日のデータ蓄積（日付、投稿内容、エンゲージメント）
- `ronin/ronin_optimization_index.json` - パターンランキング・投稿キュー管理・分析フェーズ管理
- `ronin/ronin_data_collector.py` - Threads API データ取得スクリプト
- `ronin/ronin_analyzer.py` - パターン分析スクリプト
- `ronin/ronin_optimizer.py` - 最適化インデックス生成スクリプト
- `.github/workflows/ronin_analytics_daily.yml` - 自動実行ワークフロー

### 改造対象
- `ronin/ronin_threads_auto_post.py` - Day21 チェック追加 + 最適化投稿分岐実装

---

## フェーズ 1: JSON ファイル初期化

### Task 1: ronin/threads_posts.json にハッシュタグセットを追加

**Files:**
- Modify: `ronin/threads_posts.json`

**背景:** 現在の threads_posts.json（Day 1-60）には、ハッシュタグセットがない。skin と同じ3セット（A: 基本、B: アクション、C: 感情）を追加して、投稿ごとにハッシュタグを選択できるようにする。

- [ ] **Step 1: threads_posts.json を読んで構造を確認**

```bash
python3 -c "import json; f=open('ronin/threads_posts.json'); data=json.load(f); print(f'Total posts: {len(data.get(\"posts\", []))}, Keys: {list(data.get(\"posts\", [{}])[0].keys())}')"
```

Expected: `Total posts: 60, Keys: ['day', 'morning', 'evening']`

- [ ] **Step 2: ハッシュタグセットの定義を確認（skin から参考）**

```bash
python3 -c "import json; f=open('skin/skin_threads_posts.json'); data=json.load(f); sample=data[0]; print(f'Hashtag sets: {[k for k in sample.keys() if \"hashtags\" in k]}')"
```

Expected: ハッシュタグセットの種類を確認

- [ ] **Step 3: ronin/threads_posts.json の各投稿に、ハッシュタグセット3種を追加**

ハッシュタグセット（@RoninWords 専用）:

**Set A: 基本型（日本の知恵・マインドセット）**
```
#JapaneseWisdom #Bushido #Mindset #Stoicism #Philosophy #RoninWords #Ronin
```

**Set B: アクション型（習慣・実践・行動）**
```
#DailyHabit #Discipline #Mastery #Growth #Action #RoninWords #Consistency
```

**Set C: 感情型（共感・感情・刺激）**
```
#Mindfulness #SelfAwareness #Courage #Resilience #RoninWords #Inspiration
```

Python コード（各投稿に追加）:

```python
import json

with open('ronin/threads_posts.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# ハッシュタグセット定義
hashtags_set_a = ["#JapaneseWisdom", "#Bushido", "#Mindset", "#Stoicism", "#Philosophy", "#RoninWords", "#Ronin"]
hashtags_set_b = ["#DailyHabit", "#Discipline", "#Mastery", "#Growth", "#Action", "#RoninWords", "#Consistency"]
hashtags_set_c = ["#Mindfulness", "#SelfAwareness", "#Courage", "#Resilience", "#RoninWords", "#Inspiration"]

# 各投稿にハッシュタグセット追加
for post in data.get('posts', []):
    post['hashtags_set_A'] = hashtags_set_a
    post['hashtags_set_B'] = hashtags_set_b
    post['hashtags_set_C'] = hashtags_set_c

# 保存
with open('ronin/threads_posts.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Hashtags added to all posts")
```

```bash
python3 << 'EOF'
import json

with open('ronin/threads_posts.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

hashtags_set_a = ["#JapaneseWisdom", "#Bushido", "#Mindset", "#Stoicism", "#Philosophy", "#RoninWords", "#Ronin"]
hashtags_set_b = ["#DailyHabit", "#Discipline", "#Mastery", "#Growth", "#Action", "#RoninWords", "#Consistency"]
hashtags_set_c = ["#Mindfulness", "#SelfAwareness", "#Courage", "#Resilience", "#RoninWords", "#Inspiration"]

for post in data.get('posts', []):
    post['hashtags_set_A'] = hashtags_set_a
    post['hashtags_set_B'] = hashtags_set_b
    post['hashtags_set_C'] = hashtags_set_c

with open('ronin/threads_posts.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Hashtags added to all posts")
EOF
```

Expected: `Hashtags added to all posts` と表示

- [ ] **Step 4: ハッシュタグが追加されたか確認**

```bash
python3 -c "import json; f=open('ronin/threads_posts.json'); data=json.load(f); post=data['posts'][0]; print(f'Sample post day {post[\"day\]} has hashtags:', all(f'hashtags_set_{c}' in post for c in ['A', 'B', 'C']))"
```

Expected: `Sample post day 1 has hashtags: True`

- [ ] **Step 5: Commit**

```bash
git add ronin/threads_posts.json
git commit -m "feat: add hashtag sets to ronin/threads_posts.json"
```

---

### Task 2: ronin_analytics.json の初期構造を作成

**Files:**
- Create: `ronin/ronin_analytics.json`

**背景:** 毎日の Threads API データを蓄積するために、ronin_analytics.json を初期化。skin と同じ構造で、posts_history（日付別の投稿・エンゲージメント記録）と pattern_performance（パターン別の分析結果）を管理。

- [ ] **Step 1: skin/skin_analytics.json の構造を確認**

```bash
python3 -c "import json; f=open('skin/skin_analytics.json'); data=json.load(f); print(json.dumps({k: type(v).__name__ for k, v in data.items()}, indent=2))"
```

Expected: トップレベルのキーと型を表示

- [ ] **Step 2: ronin_analytics.json を作成（同じ構造）**

```bash
python3 << 'EOF'
import json
from datetime import datetime

ronin_analytics = {
    "last_updated": datetime.now().isoformat(),
    "posts_history": [],
    "pattern_performance": []
}

with open('ronin/ronin_analytics.json', 'w', encoding='utf-8') as f:
    json.dump(ronin_analytics, f, indent=2, ensure_ascii=False)

print("ronin_analytics.json created")
EOF
```

Expected: `ronin_analytics.json created` と表示

- [ ] **Step 3: ファイルが作成されたか確認**

```bash
ls -la ronin/ronin_analytics.json && python3 -c "import json; f=open('ronin/ronin_analytics.json'); data=json.load(f); print(f'Keys: {list(data.keys())}')"
```

Expected: ファイルが存在、キーが表示される

- [ ] **Step 4: Commit**

```bash
git add ronin/ronin_analytics.json
git commit -m "feat: create ronin_analytics.json"
```

---

### Task 3: ronin_optimization_index.json の初期構造を作成

**Files:**
- Create: `ronin/ronin_optimization_index.json`

**背景:** Day21 チェック・パターンランキング・投稿キュー管理を一箇所で行う JSON ファイル。skin と同じ構造で、analysis_phase（learning/optimizing）と days_accumulated を管理。

- [ ] **Step 1: skin/skin_optimization_index.json の構造を確認**

```bash
python3 -c "import json; f=open('skin/skin_optimization_index.json'); data=json.load(f); print(json.dumps(data, indent=2, ensure_ascii=False)[:500])"
```

- [ ] **Step 2: ronin_optimization_index.json を作成（同じ構造）**

```bash
python3 << 'EOF'
import json

ronin_optimization_index = {
    "last_analyzed": "2026/05/07",
    "analysis_phase": "learning",
    "days_accumulated": 0,
    "status": "Initialization (Day 0/20 in learning phase)",
    "pattern_ranking": [],
    "time_optimization": {},
    "hashtag_optimization": {},
    "next_post_queue": []
}

with open('ronin/ronin_optimization_index.json', 'w', encoding='utf-8') as f:
    json.dump(ronin_optimization_index, f, indent=2, ensure_ascii=False)

print("ronin_optimization_index.json created")
EOF
```

Expected: `ronin_optimization_index.json created` と表示

- [ ] **Step 3: ファイルが作成されたか確認**

```bash
python3 -c "import json; f=open('ronin/ronin_optimization_index.json'); data=json.load(f); print(f'Phase: {data[\"analysis_phase\"]}, Status: {data[\"status\"]}')"
```

Expected: `Phase: learning, Status: Initialization (Day 0/20 in learning phase)`

- [ ] **Step 4: Commit**

```bash
git add ronin/ronin_optimization_index.json
git commit -m "feat: create ronin_optimization_index.json"
```

---

## フェーズ 2: データ収集・分析・最適化スクリプト

### Task 4: ronin_data_collector.py を作成

**Files:**
- Create: `ronin/ronin_data_collector.py`

**背景:** skin_data_collector.py をベースに、@RoninWords アカウント用に作成。毎日 Threads API から投稿データを取得して、ronin_analytics.json に蓄積。

- [ ] **Step 1: skin/skin_data_collector.py を確認**

```bash
head -50 skin/skin_data_collector.py
```

- [ ] **Step 2: ronin_data_collector.py を作成（skin をコピーして、account ID のみ変更）**

```bash
cp skin/skin_data_collector.py ronin/ronin_data_collector.py
```

- [ ] **Step 3: ronin_data_collector.py を編集**

파일 내용을 다음과 같이 변경:
- `THREADS_BUSINESS_ACCOUNT_ID_SKIN` → `THREADS_BUSINESS_ACCOUNT_ID_RONIN`
- `skin/skin_threads_posts.json` → `ronin/threads_posts.json`
- `skin/skin_analytics.json` → `ronin/ronin_analytics.json`
- `skin/skin_threads_progress.json` → `ronin/ronin_threads_progress.json`
- コメント内の "skin" → "ronin"

```python
# ronin/ronin_data_collector.py の関数修正例（save_analytics 関数）

def save_analytics(new_record):
    """Append a new post record to ronin_analytics.json"""
    try:
        with open('ronin/ronin_analytics.json', 'r', encoding='utf-8') as f:
            analytics = json.load(f)
    except FileNotFoundError:
        analytics = {"last_updated": datetime.now().isoformat(), "posts_history": [], "pattern_performance": []}
    
    analytics["posts_history"].append(new_record)
    analytics["last_updated"] = datetime.now().isoformat()
    
    with open('ronin/ronin_analytics.json', 'w', encoding='utf-8') as f:
        json.dump(analytics, f, indent=2, ensure_ascii=False)
```

- [ ] **Step 4: 環境変数確認（.env にアカウント ID があるか）**

```bash
grep "RONIN" .env
```

Expected: `THREADS_BUSINESS_ACCOUNT_ID_RONIN=...` が表示される（なければ skin のアカウント ID をコピー）

- [ ] **Step 5: ドライランテスト**

```bash
python3 ronin/ronin_data_collector.py --dry-run
```

Expected: エラーなし、`Dry run completed` と表示

- [ ] **Step 6: Commit**

```bash
git add ronin/ronin_data_collector.py
git commit -m "feat: create ronin_data_collector.py"
```

---

### Task 5: ronin_analyzer.py を作成

**Files:**
- Create: `ronin/ronin_analyzer.py`

**背景:** skin_analyzer.py をベースに、@RoninWords 用に作成。毎日の分析データから pattern_performance を計算し、Day21 チェック。

- [ ] **Step 1: skin/skin_analyzer.py をコピー**

```bash
cp skin/skin_analyzer.py ronin/ronin_analyzer.py
```

- [ ] **Step 2: ronin_analyzer.py をファイル名の参照を編集**

- `skin_analytics.json` → `ronin_analytics.json`
- `skin_optimization_index.json` → `ronin_optimization_index.json`
- コメント内の "skin" → "ronin"

- [ ] **Step 3: テスト**

```bash
python3 ronin/ronin_analyzer.py
```

Expected: `Still in learning phase` または `Analysis completed` と表示

- [ ] **Step 4: Commit**

```bash
git add ronin/ronin_analyzer.py
git commit -m "feat: create ronin_analyzer.py"
```

---

### Task 6: ronin_optimizer.py を作成

**Files:**
- Create: `ronin/ronin_optimizer.py`

**背景:** skin_optimizer.py をベースに、@RoninWords 用に作成。pattern_ranking と next_post_queue を生成。

- [ ] **Step 1: skin/skin_optimizer.py をコピー**

```bash
cp skin/skin_optimizer.py ronin/ronin_optimizer.py
```

- [ ] **Step 2: ronin_optimizer.py をファイル名の参照を編集**

- `skin_analytics.json` → `ronin_analytics.json`
- `skin_optimization_index.json` → `ronin_optimization_index.json`
- `skin_threads_posts.json` → `ronin/threads_posts.json`
- コメント内の "skin" → "ronin"

- [ ] **Step 3: テスト**

```bash
python3 ronin/ronin_optimizer.py
```

Expected: `Optimization index updated` と表示

- [ ] **Step 4: Commit**

```bash
git add ronin/ronin_optimizer.py
git commit -m "feat: create ronin_optimizer.py"
```

---

## フェーズ 3: GitHub Actions ワークフロー

### Task 7: ronin_analytics_daily.yml ワークフローを作成

**Files:**
- Create: `.github/workflows/ronin_analytics_daily.yml`

**背景:** skin_analytics_daily.yml をベースに、@RoninWords 用に作成。毎日 06:00 と 07:00 に自動実行。

- [ ] **Step 1: skin_analytics_daily.yml を確認**

```bash
cat .github/workflows/skin_analytics_daily.yml | head -40
```

- [ ] **Step 2: ronin_analytics_daily.yml を作成（skin をコピーして、account ID を変更）**

```yaml
name: Ronin Threads Analytics Daily

on:
  schedule:
    - cron: '0 6 * * *'  # 06:00 UTC (15:00 JST)
    - cron: '0 7 * * *'  # 07:00 UTC (16:00 JST)
  workflow_dispatch:

jobs:
  analytics:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: pip install requests
      
      - name: Collect data from Threads API
        env:
          THREADS_ACCESS_TOKEN: ${{ secrets.THREADS_ACCESS_TOKEN }}
          THREADS_BUSINESS_ACCOUNT_ID_RONIN: ${{ secrets.THREADS_BUSINESS_ACCOUNT_ID_RONIN }}
        run: python3 ronin/ronin_data_collector.py
      
      - name: Analyze patterns
        run: |
          python3 ronin/ronin_analyzer.py
          python3 ronin/ronin_optimizer.py
      
      - name: Commit and push changes
        run: |
          git config user.email "github-action@example.com"
          git config user.name "GitHub Action"
          git add ronin/ronin_analytics.json ronin/ronin_optimization_index.json
          git commit -m "自動更新: ronin analytics $(date '+%Y/%m/%d %H:%M' -u)" || true
          git push
```

ファイルを `.github/workflows/ronin_analytics_daily.yml` に保存

- [ ] **Step 3: ワークフローファイルが正しく配置されたか確認**

```bash
ls -la .github/workflows/ronin_analytics_daily.yml
```

Expected: ファイルが存在

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/ronin_analytics_daily.yml
git commit -m "ci: add ronin_analytics_daily workflow"
```

---

## フェーズ 4: 投稿スクリプト改造

### Task 8: ronin_threads_auto_post.py を改造（Day21 までは均等投稿）

**Files:**
- Modify: `ronin/ronin_threads_auto_post.py`

**背景:** skin_threads_auto_post.py の改造版をベースに、Day21 チェック機能を追加。

- [ ] **Step 1: skin/skin_threads_auto_post.py を確認（should_use_optimization 関数）**

```bash
grep -A 10 "def should_use_optimization" skin/skin_threads_auto_post.py
```

- [ ] **Step 2: ronin_threads_auto_post.py に should_use_optimization() を追加**

```python
def should_use_optimization():
    """Day21 以降かチェック（ロニン用）"""
    try:
        with open('ronin/ronin_optimization_index.json', 'r', encoding='utf-8') as f:
            opt_index = json.load(f)
        
        # analysis_phase が "optimizing" なら True
        return opt_index.get('analysis_phase') == 'optimizing'
    except:
        return False
```

- [ ] **Step 3: main 関数を修正**

既存の main() を post_sequential() に改名し、新しい main() に Day21 チェックを追加：

```python
def main():
    """メイン処理"""
    # Day21 後に最適化を使用するか判定
    if should_use_optimization():
        # Task 9 で実装（Day21以降の最適化投稿）
        post_optimized()
    else:
        # Day21 までは従来の均等投稿
        post_sequential()
```

- [ ] **Step 4: Commit**

```bash
git add ronin/ronin_threads_auto_post.py
git commit -m "refactor: prepare ronin_threads_auto_post.py for optimization (add Day21 check)"
```

---

### Task 9: ronin_threads_auto_post.py を改造（Day21 以降は最適化投稿）

**Files:**
- Modify: `ronin/ronin_threads_auto_post.py`

**背景:** Day21 以降、optimization_index の next_post_queue から投稿を取得して、最適ハッシュタグセットで投稿。

- [ ] **Step 1: skin/skin_threads_auto_post.py の post_optimized() 関数を確認**

```bash
grep -A 50 "def post_optimized" skin/skin_threads_auto_post.py | head -60
```

- [ ] **Step 2: ronin_threads_auto_post.py に post_optimized() を実装**

```python
def post_optimized():
    """最適化インデックスを参照して投稿（Day21以降用）"""
    # 最適化インデックスを読む
    with open('ronin/ronin_optimization_index.json', 'r', encoding='utf-8') as f:
        opt_index = json.load(f)
    
    # posts データを読む
    post_data = load_posts('ronin/threads_posts.json')
    
    # next_post_queue から次の投稿を取得
    queue = opt_index.get('next_post_queue', [])
    if not queue:
        print("Queue is empty. No posts to publish.")
        return
    
    # キューの最初の投稿を取得
    next_post_info = queue[0]
    day = next_post_info['day']
    
    # posts データを辞書化して高速検索
    posts_dict = {p['day']: p for p in post_data}
    post = posts_dict.get(day)
    if not post:
        print(f"❌ Day {day} の投稿データが見つかりません")
        return
    
    # 朝夜の判定
    post_type = 'morning' if check_is_morning() else 'evening'
    post_text = post[post_type]
    
    # 最適ハッシュタグセットを取得
    hashtag_set = opt_index.get('hashtag_optimization', {}).get(f'day_{day}', 'hashtags_set_A')
    hashtags = post.get(hashtag_set, post.get('hashtags_set_A', []))
    
    # 投稿テキスト + ハッシュタグを結合
    full_text = post_text + '\n\n' + ' '.join(hashtags)
    
    # Threads API で投稿
    try:
        post_id = post_to_threads(full_text)
        print(f"Posted Day {day} ({post_type}) with hashtags {hashtag_set}")
        
        # キューから削除
        opt_index['next_post_queue'].pop(0)
        with open('ronin/ronin_optimization_index.json', 'w', encoding='utf-8') as f:
            json.dump(opt_index, f, indent=2, ensure_ascii=False)
    
    except Exception as e:
        print(f"Error posting: {e}")

def check_is_morning():
    """現在時刻が朝か夜かを判定"""
    from datetime import datetime
    hour = datetime.now().hour
    return 6 <= hour < 18
```

- [ ] **Step 3: post_to_threads() が既に存在するか確認**

```bash
grep -n "def post_to_threads" ronin/ronin_threads_auto_post.py
```

既存なら OK。

- [ ] **Step 4: テスト**

```bash
python3 ronin/ronin_threads_auto_post.py
```

Expected: `Using sequential mode (Day 1-20)` と表示（Day21前なので）

- [ ] **Step 5: Commit**

```bash
git add ronin/ronin_threads_auto_post.py
git commit -m "feat: add optimization mode to ronin_threads_auto_post.py (Day 21+)"
```

---

## フェーズ 5: テスト＆検証

### Task 10: ローカルテスト（統合テスト）

**Files:**
- N/A（全スクリプト）

**背景:** GitHub Actions にプッシュする前に、ローカルで全スクリプトが動くか確認。

- [ ] **Step 1: ronin_data_collector.py をドライランテスト**

```bash
python3 ronin/ronin_data_collector.py --dry-run
```

Expected: `Dry run completed` と表示

- [ ] **Step 2: ronin_analytics.json を確認**

```bash
python3 -c "import json; f=open('ronin/ronin_analytics.json'); data=json.load(f); print(f'Posts recorded: {len(data.get(\"posts_history\", []))} entries')"
```

Expected: テストデータが記録されている

- [ ] **Step 3: ronin_analyzer.py をテスト**

```bash
python3 ronin/ronin_analyzer.py
```

Expected: `Still in learning phase` と表示

- [ ] **Step 4: ronin_optimizer.py をテスト**

```bash
python3 ronin/ronin_optimizer.py
```

Expected: `Optimization index updated` と表示

- [ ] **Step 5: ronin_optimization_index.json を確認**

```bash
python3 -c "import json; f=open('ronin/ronin_optimization_index.json'); data=json.load(f); print(f'Phase: {data.get(\"analysis_phase\")}'); print(f'Days accumulated: {data.get(\"days_accumulated\")}')"
```

Expected: `Phase: learning`, `Days accumulated: 0`

- [ ] **Step 6: ronin_threads_auto_post.py をテスト**

```bash
python3 ronin/ronin_threads_auto_post.py 2>&1 | head -20
```

Expected: エラーなし、`Using sequential mode (Day 1-20)` と表示

---

### Task 11: GitHub Actions ワークフローの動作確認

**Files:**
- N/A（ワークフロー）

**背景:** GitHub に push 後、Actions が正しく実行されるか確認。

- [ ] **Step 1: すべての変更をコミット＆プッシュ**

```bash
git status
git push origin main
```

Expected: GitHub へのプッシュ完了

- [ ] **Step 2: GitHub Actions タブを確認**

`https://github.com/[user]/[repo]/actions`

Expected: `Ronin Threads Analytics Daily` ワークフロー が表示される

- [ ] **Step 3: ワークフロー実行状態を確認**

GitHub UI から最新の run をクリック。

Expected: 
- ✅ 緑のチェック（成功）
- または ⚠️ 警告（ただし実行はされた）

- [ ] **Step 4: ログを確認**

各ステップのログで以下を確認：
- "Collect data from Threads API" → API エラーは OK（トークン .env 未設定）
- "Analyze patterns" → `Still in learning phase` or 分析完了
- "Commit and push changes" → コミット成功 or nothing to commit

---

## まとめ

このプランで以下が実現される：

✅ **フェーズ1**: JSON ファイル初期化（ハッシュタグセット追加）  
✅ **フェーズ2**: Threads API からの自動データ計測（毎日 06:00）  
✅ **フェーズ3**: データ分析＆最適化インデックス生成（毎日 07:00、Day21 から）  
✅ **フェーズ4**: 投稿スクリプト改造（Day21 以降は最適化投稿）  
✅ **フェーズ5**: テスト＆検証  

---

**実装開始**: Task 1 から順番に進めてください
