# 設計書：skin 無料note 週1自動リリースシステム

作成日: 2026-05-11

---

## 目的

肌荒れ改善アカウント（skin）の無料note記事を、毎週1本ずつ自動で「投稿準備完了状態」にする。Kentaはファイルを開いてコピー＆ペーストするだけでnoteに投稿できる。

---

## 全体の流れ

```
【セットアップ時（1回だけ）】
  記事を30本執筆
  → skin/note_queue/article_01.md 〜 article_30.md に保存
  → skin/note_queue_progress.json を {"next_index": 0} で初期化

【毎週月曜 9:00 JST（自動）】
  GitHub Actions が skin/release_note.py を実行
  → note_queue_progress.json から next_index を読む
  → skin/note_queue/article_{next_index+1:02d}.md を読み込む
  → skin/note_ready.md として上書き保存
  → next_index を +1 して保存
  → git commit & push

【Kentaの作業（毎週）】
  GitHubでskin/note_ready.mdを開く
  → 内容をコピー → noteに貼り付け → 公開
```

---

## 作成ファイル一覧

| ファイル | 役割 |
|---|---|
| `skin/note_queue/article_01〜30.md` | 記事ストック30本 |
| `skin/note_queue_progress.json` | 次に出す記事番号（0始まり） |
| `skin/release_note.py` | キューから次の記事を取り出すスクリプト |
| `.github/workflows/skin_note_release.yml` | 毎週月曜9:00JST自動実行 |
| `skin/note_ready.md` | 当週の投稿準備完了記事（毎週上書き） |

---

## 記事フォーマット

既存記事（note_article_sleep.md 等）に準拠：

```
# タイトル

（体験談ベースの書き出し・問題提起）

---

## 見出し1

本文...

## 見出し2

本文...

---

（まとめ・CTA）

![バナー](https://raw.githubusercontent.com/kmkn0523-cell/kenta-learning/main/skin/note_header.png)
```

- 文字数：2000字前後
- 構成：問題提起 → 原因解説 → 解決策 → まとめ
- バナー：既存の `note_header.png` を参照

---

## 記事テーマ一覧（30本）

| No | テーマ |
|----|--------|
| 01 | 睡眠と肌荒れ（投稿済み・キューには含めない） |
| 02 | 腸活と肌（投稿済み記事あり・別テーマで追加） |
| 03 | ファスティングと肌 |
| 04 | 肌荒れを悪化させる食べ物5選 |
| 05 | スキンケアの間違い |
| 06〜30 | 亜鉛・ストレスホルモン・砂糖・乳製品・グルテン・水分・運動・紫外線・腸内細菌・プロバイオティクス・ビタミンD・オメガ3・血糖値スパイク・リーキーガット・副腎疲労・甲状腺・ホルモンバランス・洗顔の頻度・シャンプー・枕カバー・スマホ・アルコール・カフェイン・たばこ・夜食 など |

---

## GitHub Actionsワークフロー仕様

```yaml
name: skin 無料note 週次リリース
on:
  schedule:
    - cron: '0 0 * * 1'  # 毎週月曜 9:00 JST（UTC 0:00）
  workflow_dispatch:
permissions:
  contents: write
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: python3 skin/release_note.py
      - run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add skin/note_ready.md skin/note_queue_progress.json
          git diff --cached --quiet || git commit -m "note週次リリース: 記事更新"
          git pull --rebase origin main
          git push
```

---

## エラーハンドリング

- 記事ストックが0本になったら警告メッセージを出してスキップ（ワークフローは失敗させない）
- 進捗ファイルが壊れていたら 0 にリセット

---

## 完了条件

- [ ] 記事30本が `skin/note_queue/` に存在する
- [ ] `release_note.py` を手動実行して `note_ready.md` が生成される
- [ ] GitHub Actionsで自動実行される
- [ ] `note_ready.md` の内容をnoteにそのまま貼り付けできる品質
