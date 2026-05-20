# Kenta's SNS自動化 & マネタイズプロジェクト

## ユーザー情報
- 名前: Kenta / レベル: プログラミング未経験（2026年4月開始）
- 環境: Windows + WSL2 (Ubuntu) + VS Code / 主な言語: Python3

## コードスタイル
- 各行に初心者向け日本語コメント（小学生でも雰囲気が伝わるレベル）
- 変数名・関数名は略さず分かりやすい英単語

## コミュニケーション方針
- 説明はすべて日本語。専門用語には1行で説明を添える
- フィードバックへの謝辞・励まし・同調はNG（「精進します」「おっしゃる通りです」等）
- コード・コマンド・トークン・URL・ファイルパスは必ずコードブロック（` `` ` または ```）で囲む。コピペしやすさ優先
  - シェルコマンドは `$` などのプロンプト記号を付けない
  - 複数行は ``` で囲む。1行は `` で囲む
  - トークン等の長い文字列は単独行に置く（前後に説明文を混ぜない）
  - ドラッグ選択事故防止：行頭/行末に空白を入れない・全角スペース禁止・長いトークンやURLは改行しない・コマンドは説明文に埋め込まず単独行

## 指示の優先順位
1. セッション内でユーザーが明示した指示
2. このCLAUDE.md
3. memory/

## 作業方針
- 作業開始時は `TODO.md` を読んで現状把握。完了後は `[ ]` → `[x]` に更新
- 既存コードの修正時は関係ない部分を変えない
- エラーが起きそうな処理にはエラーハンドリングを入れる
- 新しいライブラリを使うときは事前に必要か確認する

## ディレクトリ構造
- `/skin/` — skinアカウント Threads + Instagram自動投稿
- `/ronin/` — @RoninWords Threads自動投稿（Substack連携あり）
- `/finance_web/` — 家計簿Webアプリ（Next.js / Vercel）
- `/linkedin/` — LinkedIn投稿スクリプト
- `/docs/` — 運用手順書（トークン更新等）
- `/tests/`, `/skin/tests/` — pytest対象
- `/learning/` — 学習ノート
- ルート直下の `.py` — 共通スクリプト

## よく使うコマンド
- pytest: `pytest tests/ skin/tests/`
- finance_webローカル起動: `cd finance_web && npm run dev`
- finance_web本番デプロイ: `cd finance_web && npx vercel --prod`
- GitHub Actions手動実行: `gh workflow run <name>.yml`
- Threadsトークン残日数確認: `/token-expiry-check`
- 投稿JSON検証: `/validate-threads-posts`

## プロジェクト固有の罠
- `progress.json` 系は GitHub Actions が書き換える → 手動編集禁止
- Threads投稿JSON は重複NG → 編集後必ず `/validate-threads-posts`
- finance_web は GitHub 経由ではなく `vercel --prod` で直接デプロイ
- `.env` の `GITHUB_PERSONAL_ACCESS_TOKEN` はMCP github用、コミット禁止

## 稼働中の自動化（触るときは慎重に）
- **@RoninWords Threads**: 1日16回（毎時30分 7:30〜22:30 JST）GitHub Actions経由
- **skin Threads**: 1日4回（7:30/12:30/18:30/21:30 JST）GitHub Actions経由
- **Threadsトークン期限**: 2026/06/26頃 → 手順: `docs/threads_token_renewal.md`

## 呼び出しヒント
- 「動いてる？」「自動投稿失敗してない？」と聞かれたら → `automation-doctor` サブエージェント
- skin/ronin Threads投稿JSON編集後 → `/validate-threads-posts` 推奨
- トークン期限が話題になったら → `/token-expiry-check`
- ライブラリ仕様確認 → `mcp__context7__*`（推測より優先）

## 実行前に必ず確認（要承認）
- ファイル・フォルダの削除
- `git push --force` など破壊的なgitコマンド
- APIキー・`.env` を触るとき
- `threads_posts.json`・GitHub Actionsワークフローの大きな書き換え
- 自動投稿スクリプトの停止・再起動
- 新しいライブラリのインストール（`pip install` / `npm install`）

## ファイル管理
- Pythonファイルは `/home/kenta_kamijyo/` 直下。ファイル名は英小文字＋アンダースコア
- 新しいプログラムを作ったら `learning/learning_notes.md` の一覧表に追記
- 秘密情報は `.env` に保存（コードに直書きしない）

## エラー対応
- エラーメッセージは省略せず全文を受け取って原因を特定
- ①何のエラーか ②どう直すか ③なぜ起きたか の3点セットで返す
