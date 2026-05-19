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

## 指示の優先順位
1. セッション内でユーザーが明示した指示
2. このCLAUDE.md
3. memory/

## 作業方針
- 作業開始時は `TODO.md` を読んで現状把握。完了後は `[ ]` → `[x]` に更新
- 既存コードの修正時は関係ない部分を変えない。改造時は「既存機能を壊さない」を徹底
- エラーが起きそうな処理にはエラーハンドリングを入れる
- 新しいライブラリを使うときは事前に必要か確認する

## 稼働中の自動化（触るときは慎重に）
- **@RoninWords Threads**: 1日16回（毎時30分 7:30〜22:30 JST）GitHub Actions経由
- **skin Threads**: 1日4回（7:30/12:30/18:30/21:30 JST）GitHub Actions経由
- **Threadsトークン期限**: 2026/06/26頃 → 手順: `docs/threads_token_renewal.md`

## Claude Code 自動化（このプロジェクト専用）

### スキル（チャット欄で `/コマンド名`）
- `/validate-threads-posts`: skin/ronin Threads投稿JSONを検証（重複/文字数/絵文字）。投稿ファイル編集後に推奨
- `/token-expiry-check`: Threads/Instagramトークンの期限残日数を表示

### サブエージェント
- `automation-doctor`: GitHub Actions失敗診断＋progress.json状態確認＋修復手順提示。「動いてる？」と聞かれたら呼ぶ

### 自動実行hook
- `skin_/ronin_/threads_/linkedin_` 系Python編集後 → pytest自動実行（tests/, skin/tests/）
- finance_web 編集後 → Stop時にVercel自動デプロイ
- git commit前 → シークレット検出（PreToolUse）

### MCPサーバー
- `mcp__github__*`: GitHub Issue/PR/Actions操作（PATは `.env` の `GITHUB_PERSONAL_ACCESS_TOKEN`）
- `mcp__context7__*`: React/Vite/Threads API などライブラリ最新ドキュメント取得
- `mcp__claude_ai_Google_Calendar__*`: トークン期限リマインダー管理

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
