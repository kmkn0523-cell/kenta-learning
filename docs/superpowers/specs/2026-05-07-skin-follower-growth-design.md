# skin アカウント フォロワー増加システム設計書

**作成日**: 2026-05-07  
**プロジェクト**: skin（肌荒れ改善）Threads 自動投稿  
**目的**: 自動投稿を活用しながら、フォロワーを段階的に増加させる仕組みを構築

---

## 1. プロジェクト概要

### 背景
- skin アカウントは現在、Threads に1日4回（朝7:30、夜19:30）の自動投稿を実行中
- 投稿内容は Day01〜07 の7パターンをローテーション
- **課題**: 投稿は自動化されているが、フォロワー増加の施策がない

### 目的
以下の3つの最適化を自動で実行し、フォロワー増加につなげる：
1. **ハッシュタグ戦略** — 反応の良いハッシュタグセットを自動選択
2. **エンゲージメント促進** — 投稿パターンごとの CTA（行動喚起）を最適化
3. **投稿時間最適化** — 各パターンで反応が最も良い時間帯に投稿

### 成功基準
- **フェーズ1（Day1〜20）**: 反応データを20日分蓄積（学習期間）
- **フェーズ2（Day21以降）**: 各パターンの反応スコアに基づいて自動投稿を最適化
- **目標**: 3ヶ月後に月間フォロワー増加率 +30% 以上

---

## 2. 全体アーキテクチャ

### 自動ループの流れ

```
毎日のサイクル（GitHub Actions で自動実行）

[06:00] データ計測
    ↓
    Threads API から過去の投稿データを取得
    （いいね数、コメント数、投稿時間など）
    ↓
    skin_analytics.json に蓄積

    ↓

[07:00] 分析・最適化（Day21以降）
    ↓
    蓄積されたデータから反応スコアを計算
    Day01〜07 のパターンをランキング化
    各パターンに最適なハッシュタグセットを判定
    各パターンの最適な投稿時間帯を判定
    ↓
    skin_optimization_index.json を更新

    ↓

[07:30, 19:30] 最適化された投稿を実行
    ↓
    skin_optimization_index.json から「次に投稿するパターン」を取得
    そのパターンの最適ハッシュタグ＋最適時間で投稿
    ↓
    投稿完了
```

### データフロー図

```
Threads API
    ↓
[skin_data_collector.py]
    ↓
skin_analytics.json（反応データ蓄積）
    ↓
[skin_analyzer.py]
    ↓
skin_optimization_index.json（ランキング＆最適化）
    ↓
[skin_threads_auto_post.py（改造版）]
    ↓
最適化された投稿を Threads へ
```

---

## 3. データ構造

### 3.1 skin_threads_posts.json（既存を拡張）

**役割**: 投稿文＋ハッシュタグセットの管理  
**更新者**: 手動（Kenta が新しいパターン追加時のみ）

```json
{
  "posts": [
    {
      "day": 1,
      "morning": "朝の投稿文...",
      "evening": "夜の投稿文...",
      "hashtags_set_A": ["#肌荒れ", "#スキンケア", "#美肌", "#肌悩み"],
      "hashtags_set_B": ["#敏感肌", "#肌改善", "#スキンケアルーティン"],
      "hashtags_set_C": ["#毛穴", "#ニキビ", "#美容"]
    },
    {
      "day": 2,
      "morning": "...",
      "evening": "...",
      "hashtags_set_A": [...],
      "hashtags_set_B": [...],
      "hashtags_set_C": [...]
    }
  ]
}
```

### 3.2 skin_analytics.json（新規作成）

**役割**: Threads API から取得した反応データを蓄積  
**更新者**: skin_data_collector.py（毎日自動）

```json
{
  "last_updated": "2026-05-07T06:00:00+09:00",
  "posts_history": [
    {
      "day": 1,
      "type": "morning",
      "post_id": "18439672186136143",
      "posted_at": "2026-05-07T07:30:00+09:00",
      "likes": 45,
      "comments": 12,
      "shares": 3,
      "followers_gained": 2,
      "hashtags_used": ["#肌荒れ", "#スキンケア", "#美肌", "#肌悩み"],
      "engagement_score": 62.5
    },
    {
      "day": 1,
      "type": "evening",
      "post_id": "17899009074440293",
      "posted_at": "2026-05-07T19:30:00+09:00",
      "likes": 38,
      "comments": 8,
      "shares": 1,
      "followers_gained": 1,
      "hashtags_used": ["#肌荒れ", "#スキンケア", "#美肌", "#肌悩み"],
      "engagement_score": 49.0
    }
  ],
  "pattern_performance": {
    "day_1": {
      "morning": {
        "total_posts": 3,
        "avg_likes": 45,
        "avg_comments": 12,
        "avg_engagement_score": 62.5,
        "best_hour": 7,
        "best_hashtag_set": "A"
      },
      "evening": {
        "total_posts": 2,
        "avg_likes": 38,
        "avg_comments": 8,
        "avg_engagement_score": 49.0,
        "best_hour": 19,
        "best_hashtag_set": "A"
      }
    },
    "day_2": { ... },
    "day_3": { ... }
  }
}
```

**engagement_score の計算式**（Day21以降）:
```
engagement_score = (いいね × 1.0) + (コメント × 2.5) + (シェア × 5.0)
```
- コメントはいいねより価値が高い（会話につながるため）
- シェアは拡散効果があるため最も価値が高い

### 3.3 skin_optimization_index.json（新規作成）

**役割**: 最適化インデックス（Day21以降に自動生成）  
**更新者**: skin_optimizer.py（毎日自動、Day21から）  
**参照者**: skin_threads_auto_post.py（投稿時に参照）

```json
{
  "last_analyzed": "2026-05-07T07:00:00+09:00",
  "analysis_phase": "learning",
  "days_accumulated": 3,
  "status": "データ蓄積中。Day21 以降に分析開始。",
  
  "pattern_ranking": [
    { "day": 3, "score": 75.2, "priority": 1 },
    { "day": 7, "score": 68.5, "priority": 2 },
    { "day": 1, "score": 62.5, "priority": 3 },
    { "day": 5, "score": 58.3, "priority": 4 },
    { "day": 2, "score": 55.0, "priority": 5 },
    { "day": 4, "score": 52.1, "priority": 6 },
    { "day": 6, "score": 48.9, "priority": 7 }
  ],
  
  "time_optimization": {
    "day_1_morning": { "best_hour": 7, "confidence": 0.85 },
    "day_1_evening": { "best_hour": 19, "confidence": 0.72 },
    "day_3_morning": { "best_hour": 8, "confidence": 0.88 },
    "day_3_evening": { "best_hour": 20, "confidence": 0.78 }
  },
  
  "hashtag_optimization": {
    "day_1": "hashtags_set_A",
    "day_3": "hashtags_set_B",
    "day_7": "hashtags_set_C"
  },
  
  "next_post_queue": [
    {
      "scheduled_at": "2026-05-08T07:30:00+09:00",
      "day": 3,
      "type": "morning",
      "reason": "優先度1：高反応パターン",
      "hashtag_set": "hashtags_set_B"
    },
    {
      "scheduled_at": "2026-05-08T19:30:00+09:00",
      "day": 7,
      "type": "evening",
      "reason": "優先度2：次点パターン",
      "hashtag_set": "hashtags_set_C"
    }
  ]
}
```

---

## 4. 主要コンポーネント（Pythonスクリプト）

### 4.1 skin_data_collector.py（新規作成）

**役割**: Threads API からデータ取得＆計測

**実行タイミング**: 毎日 06:00 JST（GitHub Actions）

**処理内容**:
1. Threads API を使い、過去の投稿データを取得
2. 各投稿の「いいね数」「コメント数」「シェア数」を記録
3. `skin_analytics.json` に追記

**疑似コード**:
```python
# Threads API から過去の投稿を取得
posts = fetch_from_threads_api(account_id)

# 各投稿の反応データを記録
for post in posts:
    engagement_score = calculate_score(post)
    
    # skin_analytics.json に記録
    append_to_analytics(post, engagement_score)
```

### 4.2 skin_analyzer.py（新規作成）

**役割**: 蓄積されたデータを分析＆スコア計算

**実行タイミング**: 毎日 07:00 JST（GitHub Actions）、Day21 から開始

**処理内容**:
1. `skin_analytics.json` を読み込む
2. Day01〜07 ごとに「平均スコア」を計算
3. `pattern_performance` を更新

**疑似コード**:
```python
# analytics データを読む
analytics = load_json('skin_analytics.json')

# Day01〜07 ごとのパフォーマンスを計算
for day in range(1, 8):
    posts = [p for p in analytics if p['day'] == day]
    avg_score = sum([p['score'] for p in posts]) / len(posts)
    
    pattern_performance[f'day_{day}'] = {
        'avg_likes': avg(likes),
        'avg_comments': avg(comments),
        'avg_engagement_score': avg_score
    }
```

### 4.3 skin_optimizer.py（新規作成）

**役割**: 最適化インデックスを計算＆投稿キューを生成

**実行タイミング**: 毎日 07:00 JST（analyzer の後）、Day21 から開始

**処理内容**:
1. `pattern_performance` を読む
2. Day01〜07 をスコア順にランキング化
3. 各パターンの「最適なハッシュタグセット」を決定（最も反応が良かったセット）
4. 各パターンの「最適な投稿時間」を決定（反応が最も良かった時刻）
5. `next_post_queue` を生成（優先度順）

**疑似コード**:
```python
# pattern_performance を読む
perf = load_json('skin_analytics.json')['pattern_performance']

# スコアでランキング化
ranking = sorted(perf.items(), key=lambda x: x['avg_score'], desc=True)

# 次の投稿キューを作成
next_queue = []
for day, priority in enumerate(ranking, start=1):
    next_queue.append({
        'day': day,
        'priority': priority,
        'best_hashtag_set': perf[day]['best_hashtag_set'],
        'best_hour': perf[day]['best_hour']
    })
```

### 4.4 skin_threads_auto_post.py（既存を改造）

**役割**: 最適化インデックスを参照して、最適な投稿を実行

**実行タイミング**: 毎日 07:30, 19:30 JST（GitHub Actions）

**改造内容**:
- Day21 まで: 既存通り Day01〜07 を順番に投稿
- Day21 以降: `skin_optimization_index.json` の `next_post_queue` から投稿内容を取得

**疑似コード**:
```python
if days_accumulated < 21:
    # Day01〜07 を均等投稿（順番に）
    next_pattern = get_next_pattern_sequential()
else:
    # 最適化インデックスから取得
    opt_index = load_json('skin_optimization_index.json')
    next_pattern = opt_index['next_post_queue'][current_index]
    
    # 最適ハッシュタグセットを使用
    hashtags = posts_data[next_pattern['day']][next_pattern['hashtag_set']]

# 投稿を実行
post_to_threads(post_text, hashtags)
```

---

## 5. GitHub Actions ワークフロー

### 5.1 新規ワークフロー: skin_analytics_daily.yml

```yaml
name: skin Analytics Daily

on:
  schedule:
    - cron: '0 6 * * *'  # 毎日 06:00 JST
    - cron: '0 7 * * *'  # 毎日 07:00 JST

jobs:
  collect_and_analyze:
    runs-on: ubuntu-latest
    
    steps:
      # Step 1: データ計測（06:00）
      - name: Collect data from Threads API
        if: github.event.schedule == '0 6 * * *'
        run: python3 skin/skin_data_collector.py
        env:
          THREADS_ACCESS_TOKEN: ${{ secrets.THREADS_ACCESS_TOKEN }}
          THREADS_BUSINESS_ACCOUNT_ID: ${{ secrets.THREADS_BUSINESS_ACCOUNT_ID_SKIN }}
      
      # Step 2: 分析＆最適化（07:00、Day21以降）
      - name: Analyze and optimize
        if: github.event.schedule == '0 7 * * *'
        run: |
          python3 skin/skin_analyzer.py
          python3 skin/skin_optimizer.py
      
      # Step 3: コミット＆プッシュ
      - name: Commit changes
        run: |
          git config user.email "action@github.com"
          git config user.name "GitHub Action"
          git add skin/skin_analytics.json skin/skin_optimization_index.json
          git commit -m "自動分析更新: $(date '+%Y/%m/%d %H:%M')" || true
          git push
```

### 5.2 既存ワークフロー: skin_threads_post.yml（改造）

```yaml
# 既存の投稿ワークフローを改造
# - 朝: 7:30 実行 → skin_threads_auto_post.py が最適化インデックスを参照
# - 夜: 19:30 実行 → 同じく最適化インデックスを参照
```

---

## 6. フェーズ

### フェーズ 1: 学習期間（Day 1〜20）

**期間**: 約3週間

**何が起こるか**:
- Day01〜07 を毎日ローテーション投稿（均等に）
- Threads API から反応データを毎日自動取得
- `skin_analytics.json` にデータが蓄積される
- `skin_optimizer.py` は動くが、Day21 まで `next_post_queue` は生成されない

**結果**:
- 20日分の反応データが蓄積
- 各パターンの平均スコアが見える状態に

### フェーズ 2: 最適化開始（Day 21〜）

**期間**: 無期限

**何が起こるか**:
- `skin_optimizer.py` が Day01〜07 をスコア順にランキング化
- 優先度の高いパターン（反応がいい）から投稿される
- 各パターンの最適ハッシュタグセット＆最適時間が自動選択される

**例**:
- Day 3（反応スコア 75.2）が優先度1 → 毎週 1回以上投稿
- Day 2（反応スコア 55.0）が優先度5 → 毎週 0.5〜1回投稿

---

## 7. エラーハンドリング

### 7.1 API エラー

**状況**: Threads API が一時的に落ちている、トークンが失効した  
**対応**: ログに記録、該当日のデータはスキップ、次日にリトライ

```python
try:
    posts = fetch_from_threads_api()
except APIError as e:
    logger.error(f"API Error: {e}")
    # 該当日のデータは取得できないが、スクリプトは止まらない
```

### 7.2 データ不足

**状況**: Day21 を迎える前に、データが20日分未満  
**対応**: Day01〜07 を均等投稿継続。分析は開始しない。

```python
if len(analytics['posts_history']) < 20:
    optimizer_status = "learning"
    # 均等投稿継続
else:
    optimizer_status = "optimizing"
    # ランキング化＆最適化開始
```

### 7.3 ハッシュタグセットなし

**状況**: パターン A のハッシュタグセットが定義されていない  
**対応**: デフォルトハッシュタグセット（基本的な肌荒れ関連タグ）を使用

```python
if not hashtags:
    hashtags = DEFAULT_HASHTAG_SET
```

---

## 8. 計測・テスト方針

### 8.1 計測項目

| 項目 | 取得元 | 更新頻度 |
|---|---|---|
| いいね数 | Threads API | 毎日 06:00 |
| コメント数 | Threads API | 毎日 06:00 |
| シェア数 | Threads API | 毎日 06:00 |
| フォロワー増加数 | Threads API | 毎日 06:00 |
| エンゲージメント率 | 計算値 | 毎日 07:00 |
| パターンランキング | 計算値 | 毎日 07:00（Day21〜） |

### 8.2 テスト方針

**フェーズ1テスト** (Day1〜20 中に):
- [ ] skin_data_collector.py が正常に API からデータ取得できるか
- [ ] skin_analytics.json に正しくデータが記録されるか
- [ ] GitHub Actions が指定時刻に実行されるか

**フェーズ2テスト** (Day20:
- [ ] skin_analyzer.py が pattern_performance を正しく計算するか
- [ ] skin_optimizer.py が next_post_queue を正しく生成するか
- [ ] skin_threads_auto_post.py が最適化インデックスを参照して投稿するか

---

## 9. 今後の拡張

### 短期（1ヶ月以内）
- [ ] コメント返信の自動化（エンゲージメント向上）
- [ ] ハッシュタグの定期更新（トレンド対応）

### 中期（3ヶ月以内）
- [ ] ronin アカウントへの同じシステム展開
- [ ] 投稿文の A/B テスト自動化

### 長期（6ヶ月以上）
- [ ] Instagram への自動クロスポスト
- [ ] AI による投稿文の自動生成

---

## 10. ファイル一覧

| ファイル | 新規/既存 | 役割 |
|---|---|---|
| `skin/skin_threads_posts.json` | 既存（拡張） | 投稿文＋ハッシュタグセット |
| `skin/skin_analytics.json` | 新規 | 反応データ蓄積 |
| `skin/skin_optimization_index.json` | 新規 | 最適化インデックス |
| `skin/skin_data_collector.py` | 新規 | API データ取得 |
| `skin/skin_analyzer.py` | 新規 | データ分析 |
| `skin/skin_optimizer.py` | 新規 | 最適化計算 |
| `skin/skin_threads_auto_post.py` | 既存（改造） | 最適化された投稿実行 |
| `.github/workflows/skin_analytics_daily.yml` | 新規 | データ計測＆分析ワークフロー |
| `.github/workflows/skin_threads_post.yml` | 既存（改造） | 投稿ワークフロー |

---

## 11. まとめ

このシステムは以下を自動で実現します：

✅ **フェーズ1**：20日間、安全にデータを蓄積  
✅ **フェーズ2**：蓄積されたデータから自動学習＆最適化  
✅ **完全自動化**：手作業ゼロで、ハッシュタグ・時間帯・パターン優先度を最適化  
✅ **初心者向け**：複雑さを段階的に、学習期間を設けて、リスク回避  

---

**次ステップ**: 実装計画を作成
