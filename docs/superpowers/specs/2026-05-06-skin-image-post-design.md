# skin 画像付きThreads自動投稿 設計ドキュメント

作成日: 2026-05-06

## 概要

skinアカウントのThreads自動投稿（3本ツリー）の「本1（フック）」に、テーマ別のカード画像を添付する。

## 前提

- 投稿は3本ツリー（フック→本題→CTA）
- 画像は本1（フック）にのみ添付する
- 14テーマ × 1枚 = 14枚の画像を生成済み
- GitHub Pagesはすでに有効（roninで設定済み）
- 画像ホスト先: `https://kmkn0523-cell.github.io/kenta-learning/skin/skin_images/`

## カードデザイン

- サイズ: 1080×1080px
- 上半分: ダーク背景（テーマごとに色違い）+ タイトル・フック文
- 下半分: ホワイト背景 + 番号フロー図
- 下部固定: 「今すぐできること」アクションボックス
- 最下部: ブランドバー「毎日1つ、肌荒れ改善のヒントを投稿中」
- テーマごとに配色を変える（14色）

## ファイル構成

| ファイル | 変更内容 |
|---|---|
| `skin/generate_skin_cards.py` | 14枚一括生成スクリプト（新規・作成済み） |
| `skin/skin_images/theme01.png`〜`theme14.png` | 生成済み画像（14枚） |
| `skin/skin_threads_action.py` | 本1投稿時に画像URLを渡すよう変更 |

## 画像URLの対応

スレッドID（1〜14）→ `theme{id:02d}.png` のファイル名に対応。

```
thread id=1 → theme01.png
thread id=2 → theme02.png
...
thread id=14 → theme14.png
```

## 変更しないもの

- `skin_threads_posts.json`（投稿データ）
- GitHub Actionsワークフロー
- 本2・本3の投稿（テキストのまま）
