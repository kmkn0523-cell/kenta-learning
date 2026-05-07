# @RoninWords 画像付きThreads自動投稿 設計ドキュメント

作成日: 2026-05-06

## 概要

@RoninWordsのThreads自動投稿に書道カード画像を添付する。
GitHub Pagesで画像を公開し、Threads APIの `media_type: IMAGE` で投稿する。

## 前提

- 書道カード画像100枚（day01.png〜day100.png）は `ronin/ronin_images/` に生成済み
- `ronin_threads_action.py` に画像投稿の処理はすでに実装済み（`post_to_threads(text, image_url=None)`）
- 過去にGitHub Raw URLで試みたが、Threads APIにブロックされたためテキスト投稿に戻した経緯がある

## 問題

GitHub Raw URL（`raw.githubusercontent.com`）はThreads APIに拒否される。

## 解決策：GitHub Pages

リポジトリをGitHub Pagesで公開し、`github.io` ドメインの画像URLを使う。

- 画像URL例: `https://kmkn0523-cell.github.io/kenta-learning/ronin/ronin_images/day01.png`

## 変更内容

### ユーザー手作業（1回のみ）

GitHub → Settings → Pages → Source を `main` ブランチに設定する。

### コード変更（`ronin/ronin_threads_action.py`）

1. `GITHUB_RAW_BASE` を GitHub Pages URL に変更（1行）
2. `main()` で `image_url` を渡すよう変更（1行）

## 変更しないもの

- `threads_posts.json`（投稿データ）
- GitHub Actionsワークフロー（`ronin_threads_post.yml`）
- 進捗管理ファイル（`ronin_threads_progress.json`）
- 画像生成スクリプト（`generate_ronin_cards.py`）
