# skin フォロワー増加システム 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Threads 自動投稿を活用しながら、反応データに基づいて投稿パターン・ハッシュタグ・時間帯を自動最適化し、フォロワー増加を実現する

**Architecture:** 4つの独立した Python スクリプト（データ計測→分析→最適化→投稿実行）を GitHub Actions で日次実行。Day1〜20 は学習期間として均等投稿、Day21 以降は蓄積されたデータから自動最適化。

**Tech Stack:** Python 3, Threads API, GitHub Actions, JSON (データ保存)

---

## フェーズ 1: 基礎設定（JSON ファイル初期化）

### Task 1: skin_threads_posts.json にハッシュタグセットを追加

**Files:**
- Modify: `skin/skin_threads_posts.json`

**背景:** 現在の skin_threads_posts.json には Day01〜07 の投稿文のみ。ここにハッシュタグセット A/B/C を追加して、後の分析で「どのセットが反応いいか」を判定できるようにする。

- [ ] **Step 1: 現在の skin_threads_posts.json を読む**

```bash
cat skin/skin_threads_posts.json
```

- [ ] **Step 2: ハッシュタグセットを含む新しい構造に修正**

```json
{
  "posts": [
    {
      "day": 1,
      "morning": "朝の投稿文（既存）",
      "evening": "夜の投稿文（既存）",
      "hashtags_set_A": ["#肌荒れ", "#スキンケア", "#美肌", "#肌悩み"],
      "hashtags_set_B": ["#敏感肌", "#肌改善", "#スキンケアルーティン"],
      "hashtags_set_C": ["#毛穴", "#ニキビ", "#美容"]
    },
    {
      "day": 2,
      "morning": "朝の投稿文（既存）",
      "evening": "夜の投稿文（既存）",
      "hashtags_set_A": ["#肌荒れ", "#スキンケア", "#美肌", "#肌悩み"],
      "hashtags_set_B": ["#敏感肌", "#肌改善", "#スキンケアルーティン"],
      "hashtags_set_C": ["#毛穴", "#ニキビ", "#美容"]
    },
    ...Day 3〜7 も同じ構造で追加...
  ]
}
```

**補足：** ハッシュタグセット A は基本的な肌荒れ関連、B は改善・ケア重視、C は具体的な悩み（毛穴・ニキビ）重視。

- [ ] **Step 3: ファイルが正しい JSON 形式か検証**

```bash
python3 -c "import json; json.load(open('skin/skin_threads_posts.json'))" && echo "OK"
```

Expected: `OK` と表示

- [ ] **Step 4: Commit**

```bash
git add skin/skin_threads_posts.json
git commit -m "feat: add hashtag sets A/B/C to skin posts"
```

---

### Task 2: skin_analytics.json（反応データベース）の初期構造を作成

**Files:**
- Create: `skin/skin_analytics.json`

**背景:** Threads API からの反応データ（いいね、コメント等）を毎日蓄積するファイル。初期状態では空のリストから始まる。

- [ ] **Step 1: skin_analytics.json を新規作成**

```json
{
  "last_updated": "2026-05-07T06:00:00+09:00",
  "posts_history": [],
  "pattern_performance": {
    "day_1": {
      "morning": {
        "total_posts": 0,
        "avg_likes": 0,
        "avg_comments": 0,
        "avg_engagement_score": 0,
        "best_hour": null,
        "best_hashtag_set": null
      },
      "evening": {
        "total_posts": 0,
        "avg_likes": 0,
        "avg_comments": 0,
        "avg_engagement_score": 0,
        "best_hour": null,
        "best_hashtag_set": null
      }
    },
    "day_2": { ... },
    "day_3": { ... },
    "day_4": { ... },
    "day_5": { ... },
    "day_6": { ... },
    "day_7": { ... }
  }
}
```

- [ ] **Step 2: ファイルが正しい JSON か検証**

```bash
python3 -c "import json; json.load(open('skin/skin_analytics.json'))" && echo "OK"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add skin/skin_analytics.json
git commit -m "feat: initialize skin_analytics.json"
```

---

### Task 3: skin_optimization_index.json（最適化インデックス）の初期構造を作成

**Files:**
- Create: `skin/skin_optimization_index.json`

**背景:** Day21 以降に、分析結果に基づいて生成されるファイル。最初は「学習中」という状態で、empty queue を持つ。

- [ ] **Step 1: skin_optimization_index.json を新規作成**

```json
{
  "last_analyzed": "2026-05-07T07:00:00+09:00",
  "analysis_phase": "learning",
  "days_accumulated": 0,
  "status": "データ蓄積中。Day21 以降に分析を開始します。",
  "pattern_ranking": [],
  "time_optimization": {},
  "hashtag_optimization": {},
  "next_post_queue": []
}
```

- [ ] **Step 2: JSON 検証**

```bash
python3 -c "import json; json.load(open('skin/skin_optimization_index.json'))" && echo "OK"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add skin/skin_optimization_index.json
git commit -m "feat: initialize skin_optimization_index.json"
```

---

## フェーズ 2: データ計測スクリプト

### Task 4: skin_data_collector.py を作成（Threads API からデータ取得）

**Files:**
- Create: `skin/skin_data_collector.py`

**背景:** 毎日 06:00 に実行。Threads API から過去の投稿データを取得し、skin_analytics.json に追記する。

- [ ] **Step 1: 基本の骨組みを書く**

```python
import json
import os
from datetime import datetime
import requests

# 環境変数からトークン・アカウント ID を取得
THREADS_ACCESS_TOKEN = os.getenv('THREADS_ACCESS_TOKEN')
THREADS_BUSINESS_ACCOUNT_ID = os.getenv('THREADS_BUSINESS_ACCOUNT_ID_SKIN')

def fetch_threads_data():
    """Threads API から過去の投稿データを取得"""
    # Threads API エンドポイント
    url = f"https://graph.threads.net/v1.0/{THREADS_BUSINESS_ACCOUNT_ID}/threads"
    
    params = {
        'fields': 'id,text,timestamp,insights.metric(likes,comments,shares)',
        'access_token': THREADS_ACCESS_TOKEN
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return []
    
    return response.json().get('data', [])

def calculate_engagement_score(likes, comments, shares):
    """エンゲージメント スコアを計算"""
    # スコア = いいね × 1.0 + コメント × 2.5 + シェア × 5.0
    score = (likes * 1.0) + (comments * 2.5) + (shares * 5.0)
    return round(score, 1)

def save_analytics(posts_data):
    """skin_analytics.json に新しいデータを追記"""
    # 既存データを読む
    with open('skin/skin_analytics.json', 'r', encoding='utf-8') as f:
        analytics = json.load(f)
    
    # last_updated を更新
    analytics['last_updated'] = datetime.now().isoformat()
    
    # 新しい投稿データを posts_history に追記
    for post in posts_data:
        post_record = {
            'post_id': post['id'],
            'posted_at': post['timestamp'],
            'likes': post['insights']['data'][0]['values'][0]['value'],  # API 構造に応じて調整
            'comments': post['insights']['data'][1]['values'][0]['value'],
            'shares': post['insights']['data'][2]['values'][0]['value'],
            'engagement_score': calculate_engagement_score(
                post['insights']['data'][0]['values'][0]['value'],
                post['insights']['data'][1]['values'][0]['value'],
                post['insights']['data'][2]['values'][0]['value']
            )
        }
        analytics['posts_history'].append(post_record)
    
    # ファイルに保存
    with open('skin/skin_analytics.json', 'w', encoding='utf-8') as f:
        json.dump(analytics, f, indent=2, ensure_ascii=False)
    
    print(f"Updated {len(posts_data)} posts to skin_analytics.json")

if __name__ == '__main__':
    posts = fetch_threads_data()
    save_analytics(posts)
```

- [ ] **Step 2: エラーハンドリングを追加**

API トークンが無いときの対応：

```python
def fetch_threads_data():
    """Threads API から過去の投稿データを取得"""
    if not THREADS_ACCESS_TOKEN or not THREADS_BUSINESS_ACCOUNT_ID:
        print("Error: THREADS_ACCESS_TOKEN or THREADS_BUSINESS_ACCOUNT_ID not set in .env")
        return []
    
    url = f"https://graph.threads.net/v1.0/{THREADS_BUSINESS_ACCOUNT_ID}/threads"
    params = {
        'fields': 'id,text,timestamp,insights.metric(likes,comments,shares)',
        'access_token': THREADS_ACCESS_TOKEN
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 401:
            print("Error: Unauthorized. Check your THREADS_ACCESS_TOKEN")
            return []
        
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            return []
        
        return response.json().get('data', [])
    
    except requests.exceptions.Timeout:
        print("Error: API request timed out")
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []
```

- [ ] **Step 3: skin/skin_threads_posts.json から「どの Day/type が投稿されたか」を判定して、analytics に day/type フィールドを追加**

投稿文から Day と morning/evening を特定する：

```python
def identify_day_and_type(post_text):
    """投稿文から Day01〜07 と morning/evening を判定"""
    # skin_threads_posts.json を読んで、投稿文マッチングして day/type を特定
    with open('skin/skin_threads_posts.json', 'r', encoding='utf-8') as f:
        posts_db = json.load(f)['posts']
    
    for post_db in posts_db:
        if post_text.strip() == post_db['morning'].strip():
            return post_db['day'], 'morning'
        if post_text.strip() == post_db['evening'].strip():
            return post_db['day'], 'evening'
    
    return None, None
```

analytics に追記する際に day/type を記録：

```python
post_record = {
    'day': day,
    'type': post_type,  # morning or evening
    'post_id': post['id'],
    'posted_at': post['timestamp'],
    'likes': ...,
    'comments': ...,
    'engagement_score': ...
}
```

- [ ] **Step 4: 動作確認（ローカルテスト用に dry-run オプション作成）**

```python
# main セクション後に以下を追加
def dry_run():
    """テスト用：API を呼ばずに動作確認"""
    # テスト用のダミーデータ
    test_posts = [
        {
            'id': 'test_post_1',
            'text': '朝の投稿文（Day01）',
            'timestamp': '2026-05-07T07:30:00+09:00',
            'insights': {
                'data': [
                    {'values': [{'value': 45}]},  # likes
                    {'values': [{'value': 12}]},  # comments
                    {'values': [{'value': 3}]}    # shares
                ]
            }
        }
    ]
    save_analytics(test_posts)
    print("Dry run completed")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--dry-run':
        dry_run()
    else:
        posts = fetch_threads_data()
        if posts:
            save_analytics(posts)
```

- [ ] **Step 5: ファイルが実行可能か確認**

```bash
python3 skin/skin_data_collector.py --dry-run
```

Expected: `Dry run completed` と表示、skin_analytics.json が更新される

- [ ] **Step 6: Commit**

```bash
git add skin/skin_data_collector.py
git commit -m "feat: implement skin_data_collector.py (Threads API data collection)"
```

---

### Task 5: skin_analyzer.py を作成（データ分析＆スコア計算）

**Files:**
- Create: `skin/skin_analyzer.py`

**背景:** Day21 以降に実行。skin_analytics.json の posts_history を分析して、Day01〜07 ごとの平均スコアを pattern_performance に記録。

- [ ] **Step 1: 基本の骨組みを書く**

```python
import json
from datetime import datetime
from collections import defaultdict

def load_analytics():
    """skin_analytics.json を読む"""
    with open('skin/skin_analytics.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_pattern_performance(posts_history):
    """Day01〜07 ごとの平均スコアを計算"""
    # day ごとに分類
    performance = defaultdict(lambda: {
        'morning': {'scores': [], 'hours': []},
        'evening': {'scores': [], 'hours': []}
    })
    
    for post in posts_history:
        day = post.get('day')
        post_type = post.get('type')  # morning or evening
        
        if not day or not post_type:
            continue
        
        score = post.get('engagement_score', 0)
        
        # 投稿時刻から時間を抽出
        posted_at = post.get('posted_at', '')
        try:
            hour = int(posted_at.split('T')[1].split(':')[0])
        except:
            hour = None
        
        # データを収集
        performance[f'day_{day}'][post_type]['scores'].append(score)
        if hour:
            performance[f'day_{day}'][post_type]['hours'].append(hour)
    
    # 平均を計算
    result = {}
    for day_key, day_data in performance.items():
        result[day_key] = {}
        for post_type, data in day_data.items():
            scores = data['scores']
            hours = data['hours']
            
            if scores:
                avg_score = sum(scores) / len(scores)
                best_hour = max(set(hours), key=hours.count) if hours else None
            else:
                avg_score = 0
                best_hour = None
            
            result[day_key][post_type] = {
                'total_posts': len(scores),
                'avg_engagement_score': round(avg_score, 1),
                'best_hour': best_hour,
                'best_hashtag_set': 'A'  # 初期値は A（後で分析で更新）
            }
    
    return result

def update_analytics(performance):
    """pattern_performance を skin_analytics.json に保存"""
    analytics = load_analytics()
    
    # pattern_performance を更新
    for day_key, day_data in performance.items():
        if day_key not in analytics['pattern_performance']:
            analytics['pattern_performance'][day_key] = {}
        analytics['pattern_performance'][day_key].update(day_data)
    
    # last_updated を記録
    analytics['last_updated'] = datetime.now().isoformat()
    
    # ファイルに保存
    with open('skin/skin_analytics.json', 'w', encoding='utf-8') as f:
        json.dump(analytics, f, indent=2, ensure_ascii=False)
    
    print(f"Updated pattern_performance for {len(performance)} days")

if __name__ == '__main__':
    analytics = load_analytics()
    performance = calculate_pattern_performance(analytics['posts_history'])
    update_analytics(performance)
    print("Analysis completed")
```

- [ ] **Step 2: Day21 チェック機能を追加**

Day21 まではスキップ：

```python
def should_analyze():
    """Day21 を過ぎているか確認"""
    analytics = load_analytics()
    
    # posts_history の日付から最初の投稿日を取得
    if not analytics['posts_history']:
        return False
    
    first_post_date = analytics['posts_history'][0]['posted_at'][:10]
    start_date = datetime.fromisoformat(first_post_date)
    days_passed = (datetime.now() - start_date).days
    
    if days_passed < 20:
        print(f"Analysis skipped. {20 - days_passed} days until Day21")
        return False
    
    return True

if __name__ == '__main__':
    if should_analyze():
        analytics = load_analytics()
        performance = calculate_pattern_performance(analytics['posts_history'])
        update_analytics(performance)
        print("Analysis completed")
    else:
        print("Still in learning phase")
```

- [ ] **Step 3: 動作テスト**

```bash
python3 skin/skin_analyzer.py
```

Expected: `Still in learning phase` または `Analysis completed` と表示

- [ ] **Step 4: Commit**

```bash
git add skin/skin_analyzer.py
git commit -m "feat: implement skin_analyzer.py (pattern performance analysis)"
```

---

### Task 6: skin_optimizer.py を作成（最適化インデックス生成）

**Files:**
- Create: `skin/skin_optimizer.py`

**背景:** analytics の pattern_performance をもとに、Day01〜07 をスコア順にランキング化し、skin_optimization_index.json の pattern_ranking と next_post_queue を生成。

- [ ] **Step 1: 基本の骨組みを書く**

```python
import json
from datetime import datetime

def load_analytics():
    """skin_analytics.json を読む"""
    with open('skin/skin_analytics.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_pattern_ranking(pattern_performance):
    """pattern_performance からスコアでランキング化"""
    ranking_data = []
    
    for day in range(1, 8):
        day_key = f'day_{day}'
        
        if day_key not in pattern_performance:
            continue
        
        # morning と evening の平均スコアを計算
        morning_score = pattern_performance[day_key]['morning'].get('avg_engagement_score', 0)
        evening_score = pattern_performance[day_key]['evening'].get('avg_engagement_score', 0)
        avg_score = (morning_score + evening_score) / 2
        
        ranking_data.append({
            'day': day,
            'score': round(avg_score, 1),
            'priority': None  # 後で付与
        })
    
    # スコア順ソート
    ranking_data.sort(key=lambda x: x['score'], reverse=True)
    
    # priority を付与
    for i, item in enumerate(ranking_data, start=1):
        item['priority'] = i
    
    return ranking_data

def generate_next_post_queue(pattern_ranking):
    """pattern_ranking から next_post_queue を生成
    
    優先度の高いパターンを複数回、優先度が低いものを少ない回数投稿するようにキューを構成
    """
    queue = []
    
    # 優先度を重み付けして、複数回登録
    for item in pattern_ranking:
        day = item['day']
        priority = item['priority']
        
        # priority が小さい（反応がいい）ほど、多く登録される
        # priority 1 → 2回登録、priority 2 → 2回登録、priority 3 → 1回登録...
        times_to_add = max(1, 8 - priority // 2)
        
        for _ in range(times_to_add):
            queue.append({
                'day': day,
                'priority': priority,
                'reason': f'優先度{priority}：{["高反応", "次点", "中程度"][min(priority-1, 2)]}パターン'
            })
    
    return queue

def update_optimization_index(pattern_ranking, next_post_queue):
    """skin_optimization_index.json を更新"""
    # 既存の optimization_index を読む
    with open('skin/skin_optimization_index.json', 'r', encoding='utf-8') as f:
        opt_index = json.load(f)
    
    # 新しいデータを反映
    opt_index['last_analyzed'] = datetime.now().isoformat()
    opt_index['analysis_phase'] = 'learning'  # Day21 までは learning
    
    analytics = load_analytics()
    opt_index['days_accumulated'] = len(set([p.get('day') for p in analytics['posts_history']]))
    
    opt_index['pattern_ranking'] = pattern_ranking
    opt_index['next_post_queue'] = next_post_queue[:14]  # 2週間分のキュー
    
    if opt_index['days_accumulated'] >= 20:
        opt_index['analysis_phase'] = 'optimizing'
        opt_index['status'] = '最適化モード開始。ランキングに基づいて投稿を最適化します。'
    else:
        opt_index['status'] = f'データ蓄積中（{opt_index["days_accumulated"]}/20）。Day21以降に最適化開始。'
    
    # ファイルに保存
    with open('skin/skin_optimization_index.json', 'w', encoding='utf-8') as f:
        json.dump(opt_index, f, indent=2, ensure_ascii=False)
    
    print(f"Updated optimization_index. Phase: {opt_index['analysis_phase']}")

if __name__ == '__main__':
    analytics = load_analytics()
    pattern_perf = analytics.get('pattern_performance', {})
    
    if pattern_perf:
        ranking = generate_pattern_ranking(pattern_perf)
        queue = generate_next_post_queue(ranking)
        update_optimization_index(ranking, queue)
        print("Optimization index updated")
    else:
        print("No pattern performance data yet")
```

- [ ] **Step 2: 動作テスト**

```bash
python3 skin/skin_optimizer.py
```

Expected: `Optimization index updated` または `No pattern performance data yet` と表示

- [ ] **Step 3: Commit**

```bash
git add skin/skin_optimizer.py
git commit -m "feat: implement skin_optimizer.py (optimization index generation)"
```

---

## フェーズ 3: GitHub Actions ワークフロー

### Task 7: skin_analytics_daily.yml ワークフローを作成

**Files:**
- Create: `.github/workflows/skin_analytics_daily.yml`

**背景:** 毎日 06:00（データ計測）と 07:00（分析＆最適化）に自動実行。これにより、analytics と optimization_index が毎日更新される。

- [ ] **Step 1: 新しいワークフローファイルを作成**

```yaml
name: skin Analytics Daily

on:
  schedule:
    - cron: '0 6 * * *'  # 毎日 06:00 JST
    - cron: '0 7 * * *'  # 毎日 07:00 JST

jobs:
  analytics_pipeline:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: pip install requests
      
      - name: Collect data from Threads API
        if: github.event.schedule == '0 6 * * *'
        env:
          THREADS_ACCESS_TOKEN: ${{ secrets.THREADS_ACCESS_TOKEN }}
          THREADS_BUSINESS_ACCOUNT_ID_SKIN: ${{ secrets.THREADS_BUSINESS_ACCOUNT_ID_SKIN }}
        run: python3 skin/skin_data_collector.py
      
      - name: Analyze patterns
        if: github.event.schedule == '0 7 * * *'
        run: |
          python3 skin/skin_analyzer.py
          python3 skin/skin_optimizer.py
      
      - name: Commit and push changes
        run: |
          git config user.email "github-action@example.com"
          git config user.name "GitHub Action"
          git add skin/skin_analytics.json skin/skin_optimization_index.json
          git commit -m "自動更新: skin analytics $(date '+%Y/%m/%d %H:%M' -u)" || true
          git push
```

- [ ] **Step 2: ワークフロー構文が正しいか確認**

```bash
# GitHub上で、Actions タブから ワークフロー が正しく認識されているか確認
# または、ローカルでは以下でファイルが存在するか確認
ls -la .github/workflows/skin_analytics_daily.yml
```

Expected: ファイルが存在、エラー出力なし

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/skin_analytics_daily.yml
git commit -m "ci: add skin_analytics_daily workflow"
```

---

## フェーズ 4: 投稿スクリプト改造

### Task 8: skin_threads_auto_post.py を改造（Day21 までは均等投稿）

**Files:**
- Modify: `skin/skin_threads_auto_post.py`

**背景:** 現在の skin_threads_auto_post.py は Day01〜07 をローテーション投稿している。これを「Day21 までは均等投稿を継続」として、ロジックは変わらないが、コメントを加えて Day21 後の分岐に備える。

- [ ] **Step 1: 現在の skin_threads_auto_post.py を読む**

```bash
cat skin/skin_threads_auto_post.py
```

- [ ] **Step 2: main 関数に「Day21 チェック」を追加**

```python
def should_use_optimization():
    """Day21 以降かチェック"""
    # skin_optimization_index.json から analysis_phase を確認
    try:
        with open('skin/skin_optimization_index.json', 'r', encoding='utf-8') as f:
            opt_index = json.load(f)
        
        # analysis_phase が "optimizing" なら True
        return opt_index.get('analysis_phase') == 'optimizing'
    except:
        return False
```

- [ ] **Step 3: main 関数を修正**

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

def post_sequential():
    """Day01〜07 を順番に投稿（Day01〜20用）"""
    # 既存のロジック（ronin_threads_progress.json みたいに進捗を管理）
    post_data = load_posts('skin_threads_posts.json')
    progress = load_progress('skin/skin_threads_progress.json')
    
    # 次のパターンを決定（Day01→Day02→...→Day07→Day01...とローテーション）
    next_index = progress['index'] % len(post_data)
    post = post_data[next_index]
    
    # ...投稿実行...
    # progress を更新
    progress['index'] += 1
    save_progress('skin/skin_threads_progress.json', progress)
```

- [ ] **Step 4: Commit**

```bash
git add skin/skin_threads_auto_post.py
git commit -m "refactor: prepare skin_threads_auto_post.py for optimization (add Day21 check)"
```

---

### Task 9: skin_threads_auto_post.py を改造（Day21 以降は最適化投稿）

**Files:**
- Modify: `skin/skin_threads_auto_post.py`

**背景:** Day21 以降、optimization_index の next_post_queue から投稿内容を取得して、最適ハッシュタグセット + 最適時間で投稿する。

- [ ] **Step 1: post_optimized() 関数を実装**

```python
def post_optimized():
    """最適化インデックスを参照して投稿（Day21以降用）"""
    # 最適化インデックスを読む
    with open('skin/skin_optimization_index.json', 'r', encoding='utf-8') as f:
        opt_index = json.load(f)
    
    # posts データを読む
    post_data = load_posts('skin_threads_posts.json')
    
    # next_post_queue から次の投稿を取得
    queue = opt_index.get('next_post_queue', [])
    if not queue:
        print("No posts in queue. Fallback to sequential posting")
        post_sequential()
        return
    
    # キューの最初の投稿を取得
    next_post_info = queue[0]
    day = next_post_info['day']
    
    # posts データから該当の Day を取得
    post = next(p for p in post_data if p['day'] == day)
    
    # 朝夜の判定（簡易：朝は morning/夜 は evening）
    # 本来は最適化インデックスに「morning」「evening」フラグがあると理想的
    # ここでは朝夜交互に投稿（simple approach）
    post_type = 'morning' if check_is_morning() else 'evening'
    post_text = post[post_type]
    
    # 最適ハッシュタグセットを取得
    # skin_optimization_index.json に hashtag_optimization があれば参照
    hashtag_set = opt_index.get('hashtag_optimization', {}).get(f'day_{day}', 'hashtags_set_A')
    hashtags = post.get(hashtag_set, post.get('hashtags_set_A', []))
    
    # 投稿テキスト + ハッシュタグを結合
    full_text = post_text + '\n\n' + ' '.join(hashtags)
    
    # Threads API で投稿
    try:
        post_id = post_to_threads(full_text)
        print(f"Posted Day {day} ({post_type}) with hashtags {hashtag_set}")
        
        # キューから削除（progress の代わりに queue を更新）
        opt_index['next_post_queue'].pop(0)
        with open('skin/skin_optimization_index.json', 'w', encoding='utf-8') as f:
            json.dump(opt_index, f, indent=2, ensure_ascii=False)
    
    except Exception as e:
        print(f"Error posting: {e}")

def check_is_morning():
    """現在時刻が朝か夜かを判定（簡易版）"""
    from datetime import datetime
    hour = datetime.now().hour
    return 6 <= hour < 18
```

- [ ] **Step 2: post_to_threads() 関数が既に存在するか確認**

```bash
grep -n "def post_to_threads" skin/skin_threads_auto_post.py
```

既存なら、その関数をそのまま使用。

- [ ] **Step 3: main() 関数の最終版**

```python
def main():
    """メイン処理"""
    try:
        if should_use_optimization():
            print("Using optimization mode (Day 21+)")
            post_optimized()
        else:
            print("Using sequential mode (Day 1-20)")
            post_sequential()
    except Exception as e:
        print(f"Error in main: {e}")

if __name__ == '__main__':
    main()
```

- [ ] **Step 4: 動作テスト（ローカル）**

```bash
# Day21 前なら sequential mode が動くはず
python3 skin/skin_threads_auto_post.py
```

Expected: `Using sequential mode (Day 1-20)` と表示（または投稿実行）

- [ ] **Step 5: Commit**

```bash
git add skin/skin_threads_auto_post.py
git commit -m "feat: add optimization mode to skin_threads_auto_post.py (Day 21+)"
```

---

## フェーズ 5: テスト＆検証

### Task 10: ローカルテスト（統合テスト）

**Files:**
- N/A（全スクリプト）

**背景:** GitHub Actions にプッシュする前に、ローカルで全スクリプトが動くか確認。

- [ ] **Step 1: dry-run で skin_data_collector.py をテスト**

```bash
python3 skin/skin_data_collector.py --dry-run
```

Expected: `Dry run completed` と表示、skin_analytics.json にテストデータが追記される

- [ ] **Step 2: skin_analytics.json の内容を確認**

```bash
python3 -c "import json; print(json.dumps(json.load(open('skin/skin_analytics.json')), indent=2, ensure_ascii=False)[:500])"
```

Expected: posts_history にテストデータが含まれている

- [ ] **Step 3: skin_analyzer.py をテスト**

```bash
python3 skin/skin_analyzer.py
```

Expected: `Still in learning phase` と表示

- [ ] **Step 4: skin_optimizer.py をテスト**

```bash
python3 skin/skin_optimizer.py
```

Expected: `Optimization index updated` と表示

- [ ] **Step 5: skin_optimization_index.json を確認**

```bash
python3 -c "import json; print(json.dumps(json.load(open('skin/skin_optimization_index.json')), indent=2, ensure_ascii=False)[:500])"
```

Expected: analysis_phase が「learning」、status に蓄積日数が表示

- [ ] **Step 6: skin_threads_auto_post.py のテスト**

```bash
# エラーなく実行されるか確認（実際には投稿しないように dry-run 版があるとベスト）
python3 skin/skin_threads_auto_post.py --dry-run 2>&1 | head -20
```

Expected: エラーなし

---

### Task 11: GitHub Actions ワークフローの動作確認

**Files:**
- N/A（ワークフロー）

**背景:** GitHub に push 後、Actions が正しく実行されるか、ログを確認。

- [ ] **Step 1: すべての変更をコミット＆プッシュ**

```bash
git status
# （すべてがコミットされているか確認）

git push origin main
```

Expected: GitHub にプッシュ完了

- [ ] **Step 2: GitHub の Actions タブを確認**

```
https://github.com/[user]/[repo]/actions
```

Expected: `skin Analytics Daily` ワークフロー が表示される

- [ ] **Step 3: 手動実行で動作確認（オプション）**

GitHub Actions の UI から、skin_analytics_daily workflow を手動実行。

Expected: 緑のチェック（成功）が表示される

- [ ] **Step 4: ログを確認**

workflow run の詳細を開き、各ステップのログを確認。

Expected: 
- "Collect data from Threads API" → API エラーなし or トークンエラー（期待通り）
- "Analyze patterns" → "No pattern performance data yet" or "Analysis completed"
- "Commit and push changes" → コミット成功 or nothing to commit

---

## まとめ

このプランで以下が実現される：

✅ **フェーズ1**: JSON ファイル初期化（Day01〜07 にハッシュタグセット追加）  
✅ **フェーズ2**: Threads API からの自動データ計測（毎日 06:00）  
✅ **フェーズ3**: データ分析＆最適化インデックス生成（毎日 07:00、Day21 から）  
✅ **フェーズ4**: 投稿スクリプト改造（Day21 以降は最適化投稿）  
✅ **フェーズ5**: テスト＆検証  

---

**実装開始**: Task 1 から順番に進めてください
