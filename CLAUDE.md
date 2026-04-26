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

## 作業方針
- 既存のコードを修正する時は、関係ない部分は変更しない
- 新しいライブラリを使うときは、事前に必要かを確認する
- エラーが起きそうな処理にはエラーハンドリングを入れる
- 改造時は「既存機能を壊さない」を徹底する

## ファイル管理ルール
- Pythonファイルは /home/kenta_kamijyo/ 直下に作成
- ファイル名は英語小文字 + アンダースコア (例: number_game.py)
- 新しくプログラムを作ったら learning_notes.md の「作成したプログラム」表に追記する
- APIキー・パスワードなどの秘密情報は必ず `.env` ファイルに保存し、コードに直接書かない

## これまでに作成したプログラム
- omikuji.py: おみくじ
- janken.py: じゃんけんゲーム
- weather.py: 天気予報(11都市・7日間・服装提案)
- timer.py: 作業時間タイマー
- number_game.py: 数当てゲーム
- learning_notes.md: 学習記録
- today_weekday.py: 今日の曜日表示
- ronin_words.jsx: 書道カードアプリ（日本の格言100枚・React製・@RoninWords用）
- ronin_words_strategy.md: @RoninWordsのThreads／X投稿戦略メモ
- ronin_words_schedule.md: @RoninWords 1ヶ月×2投稿/日のX投稿スケジュール（Day01〜30）
- ronin_words_schedule_day31_100.md: @RoninWords X投稿スケジュール（Day31〜100、70日分）
- ronin_words_business.md: @RoninWords マネタイズ・ビジネスアイデアメモ（DMサービス・グッズ・電子書籍など）
- ronin_words_proverbs_100.md: 海外に刺さる日本の諺・格言100選（英語解説つき、カテゴリ別）
- ronin_words_scripts.md: @RoninWords ショート動画台本30本（TikTok／Reels／Shorts用、Day01〜30）
- ronin_words_script_template.md: @RoninWords バズる台本の型（フック6種・ナレーション原則・改善例つき）
- ronin_words_threads_template.md: @RoninWords Threads投稿テンプレート（フック6種・フォーマット4種・週次運用スケジュール）
- ronin_words_threads_day01_10.md: @RoninWords Threads実投稿文 Day01〜10（朝+夜 × 10日分）
- ronin_words_threads_day11_20.md: @RoninWords Threads実投稿文 Day11〜20（朝+夜 × 10日分）
- ronin_words_threads_day21_30.md: @RoninWords Threads実投稿文 Day21〜30（朝+夜 × 10日分）
- threads_auto_post.py: Threads自動投稿スクリプト（Threads API使用・.envからキー読み込み）
- threads_posts.json: 投稿データ（Day01〜30 朝夜 全60投稿）
- CLAUDE.md: プロジェクト設定ファイル（このファイル）

## 学習履歴
- 2026/4/23: 環境構築開始、おみくじプログラム作成
- 2026/4/24: じゃんけん、天気予報プログラム
- 2026/4/25: タイマー・数当てゲーム作成、指示術レッスン、learning_notes.md・CLAUDE.md作成、today_weekday.pyでCLAUDE.mdの効果体感、エラー自己解決（command not found）
- (今後追記)

## 困ったときの対応
- エラーが出たらエラーメッセージを全文受け取って原因を特定
- 解決策は必ず初心者向けに説明
- 「これは何のため?」を伝えて納得感を持たせる
