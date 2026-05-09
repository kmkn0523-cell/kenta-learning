# Kenta Kamijyo's Learning Project

## プロジェクトの目標
- Threadsで自動投稿できるようになること
- 段階的に他のSNS(Instagram等)にも横展開する

## 学習方針
- プログラミング基礎の深い理解より、AIへの指示力を重視する
- 全部完璧に理解しなくてOK、動かして楽しむことを優先する
- Claude Codeを自然言語で使いこなすスキルを身につける

## ユーザー情報
- 名前: Kenta
- レベル: プログラミング完全未経験(2026年4月開始)
- 環境: Windows + WSL2 (Ubuntu) + VS Code
- 主な使用言語: Python3

## コードスタイル
- コードの各行に初心者向けの日本語コメントを入れる
- 変数名・関数名は分かりやすい英単語にする(略さない)
- 小学生でも雰囲気が伝わるくらい、コメントを丁寧に書く

## コミュニケーション方針
- 説明はすべて日本語で行う
- 専門用語を使うときは、初心者向けに1行で説明を添える
- コードを作った後、「主な変更点」や「使い方」を教える
- 新しい概念を使うときは、その概念を初心者向けに簡単に説明する
- フィードバックへの謝辞・励まし・同調は書かない（「精進します」「おっしゃる通りです」等はNG）

## 指示の優先順位
1. セッション内でユーザーが明示した指示（最優先）
2. このCLAUDE.md の内容
3. memory/ の内容

## 作業方針
- セッション開始時・作業内容が不明な時は必ず `/home/kenta_kamijyo/TODO.md` を読んで現状のTODOを把握すること
- 作業が完了したらTODO.mdの該当項目を `[ ]` → `[x]` に更新すること
- 既存のコードを修正する時は、関係ない部分は変更しない
- 新しいライブラリを使うときは、事前に必要かを確認する
- エラーが起きそうな処理にはエラーハンドリングを入れる
- 改造時は「既存機能を壊さない」を徹底する

## 稼働中の自動化システム
- **@RoninWords Threads自動投稿**: 1日16回（7:30〜22:30 毎時30分 JST）GitHub Actions経由
- **skin（肌荒れ）Threads自動投稿**: 1日16回（7:30〜22:30 毎時30分 JST）GitHub Actions経由
- **Threadsトークン期限**: 2026/06/26頃（60日後にリマインド予約済み）
- 投稿データ: `threads_posts.json`（Day01〜60の朝夜120投稿をローテーション）
- 進捗管理: `ronin_threads_progress.json`（次に投稿する番号を記録）

## 安全のための確認ルール（実行前に必ず聞く）
- ファイル・フォルダの削除（特に複数まとめての削除）
- `git push --force` など破壊的なgitコマンド
- APIキー・.env ファイルを触るとき
- 既存ファイル（特に `threads_posts.json`・GitHub Actionsワークフロー）の大きな書き換え
- 自動投稿スクリプトの停止・再起動
- 新しいライブラリのインストール（`pip install`・`npm install`）

## ファイル管理ルール
- Pythonファイルは /home/kenta_kamijyo/ 直下に作成
- ファイル名は英語小文字 + アンダースコア (例: number_game.py)
- 新しくプログラムを作ったら learning_notes.md の「作成したプログラム」表に追記する
- APIキー・パスワードなどの秘密情報は必ず `.env` ファイルに保存し、コードに直接書かない

## 主要ファイル一覧

### フォルダ構成
```
/home/kenta_kamijyo/
├── ronin/          ← @RoninWords 関連ファイル
├── skin/           ← skin（肌荒れ）アカウント関連ファイル
├── learning/       ← 学習用Pythonスクリプト
├── finance_web/    ← 家計簿Webアプリ（React）
└── CLAUDE.md / TODO.md / .env など
```

### roninフォルダの主要ファイル
| ファイル名 | 役割 |
|---|---|
| `ronin/ronin_threads_action.py` | @RoninWords の手動投稿スクリプト |
| `ronin/threads_auto_post.py` | @RoninWords の自動投稿スクリプト |
| `ronin/threads_posts.json` | 投稿データ（Day01〜60、120投稿） |
| `ronin/ronin_threads_progress.json` | 次に投稿する番号の記録 |

### skinフォルダの主要ファイル
| ファイル名 | 役割 |
|---|---|
| `skin/skin_threads_auto_post.py` | skinアカウントのThreads自動投稿スクリプト |
| `skin/skin_threads_action.py` | skinアカウントの手動投稿スクリプト |
| `skin/skin_threads_progress.json` | skin投稿の進捗記録 |
| `skin/skin_x_auto_post.py` | skin の X（旧Twitter）自動投稿スクリプト |
| `skin/skin_x_posts.json` | skin の X 投稿データ |

### その他の重要ファイル
| ファイル名 | 役割 |
|---|---|
| `.env` | APIキーなどの秘密情報（Gitに入れない） |
| `TODO.md` | 現在のタスク一覧（セッション開始時に必ず読む） |
| `threads_token_renewal.md` | Threadsトークン更新の手順書 |
| `learning/learning_notes.md` | 学習メモ・作成したプログラム一覧 |

## よく使うコマンド
```bash
# Threads手動投稿テスト
python3 ronin/ronin_threads_action.py
python3 skin/skin_threads_auto_post.py

インスタが増えてない


# GitHub Actions確認
# → https://github.com/ からリポジトリのActionsタブを見る

# 環境変数確認（APIキー等）
cat .env

# Gitの状態確認・同期
git status
git add . && git commit -m "更新" && git push
```

## Threadsトークン更新
- 期限: **2026/06/26頃**（詳細手順は `threads_token_renewal.md` を参照）

## 困ったときの対応
- エラーが出たらエラーメッセージを全文受け取って原因を特定
- 解決策は必ず初心者向けに説明
- 「これは何のため?」を伝えて納得感を持たせる

## エラー対応のお作法（ユーザー側ルール）
- エラーメッセージは省略せず全文をそのままClaude Codeに貼る
- 以下3点セットで返す:
  1. **これは何のエラーか**（原因をわかりやすく）
  2. **どう直すか**（具体的な手順）
  3. **なぜ起きたか**（再発防止のための理解）
- 勝手に直そうとせず、まず原因を理解してから動く
- 「とりあえず動いた」で終わらせず、「なぜ動いたか」を確認する
