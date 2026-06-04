# Claude Code 学習記録

## プロフィール
- 学習開始日: 2026年4月23日
- 目標: 各種SNSの自動運用ができるレベル
- 学習方針: Claude Codeを自然言語で使いこなす（プログラミングの深い理解より、AIへの指示力を重視）
- 環境: Windows + WSL2 (Ubuntu)

---

## セットアップ済みの環境

| ツール | 役割 |
|---|---|
| WSL2 + Ubuntu | Windowsの中でLinuxを動かす環境 |
| VS Code + WSL拡張 | コードを書く本拠地 |
| Node.js | JavaScriptの実行環境、Claude Codeの土台 |
| Claude Code | AIコーディングアシスタント |
| Python3 + pip + requests | Pythonとライブラリ管理 |

---

## 作成したプログラム

| 日付 | ファイル名 | 内容 | 学んだ要素 |
|---|---|---|---|
| 4/23 | omikuji.py | おみくじ（全部盛り版） | ランダム、リスト、絵文字 |
| 4/24 | janken.py | じゃんけんゲーム | 入力、勝敗判定、ループ |
| 4/24 | weather.py | 11都市×7日天気予報×服装提案 | API通信、JSON、表示整形 |
| 4/25 | timer.py | 作業時間タイマー | 時間処理、ファイル追記、記録機能 |
| 4/25 | number_game.py | 数当てゲーム（難易度選択） | 範囲指定、エラー処理、通算成績 |
| 4/25 | today_weekday.py | 今日の曜日表示 | CLAUDE.mdの効果体感、日時処理 |
| 4/27 | ronin_threads_action.py | @RoninWords用Threads自動投稿（GitHub Actions版） | API認証、環境変数、JSONローテーション、共通タグ自動付与 |
| 6/2 | skin_reply_hunter.py | skinのリプ巡回ツール（探す→書く→記録を1コマンドに・半自動／Threads APIは使わない） | TDD（テスト先行）、純粋関数とファイル操作の分離、キーワードで話題判定、テンプレ共通化（skin_comment_templates.py） |
| 6/4 | reaction_dashboard.py | skin/ronin全SNS（Threads・Instagram・note・Substack）の投稿数と反応を1枚の dashboard.md に集約するダッシュボード生成 | 複数JSONの集約読み込み、標準ライブラリのみ（json/pathlib/datetime）、「読むだけ＝既存ファイルを壊さない」設計、複数の日時形式のパース、try/exceptで一部が壊れても全体を止めないエラー処理 |

---

## 覚えたPython要素

- `import` — ライブラリ読み込み
- 変数、リスト、辞書
- `input()` — ユーザー入力
- `print()` — 出力
- `if / elif / else` — 条件分岐
- `while / for` — ループ
- `random` — ランダム選択
- `requests` — API通信
- ファイル読み書き
- コメント (`#`)

---

## 覚えたターミナルコマンド

| コマンド | 内容 |
|---|---|
| `ls / cd / pwd` | ファイル操作の基本 |
| `python3 ファイル名` | プログラム実行 |
| `pip install` | ライブラリインストール |
| `clear / Ctrl+L` | 画面クリア |
| `Ctrl+C` | 中断 |
| `code .` | VS Codeで現在フォルダを開く |

---

## 覚えたClaude Codeコマンド

| コマンド | 内容 |
|---|---|
| `claude` | 起動 |
| `/exit` | 終了 |
| `/status` | 状態確認 |
| `/stats` | 統計確認 |
| `Ctrl+C 2回` | 強制終了 |

---

## 覚えたVS Code操作

| ショートカット | 内容 |
|---|---|
| `Ctrl+S` | 保存 |
| `Ctrl+@` | ターミナルを開く |
| `Ctrl+A` | 全選択 |
| 左下「><」 | WSL接続 |
| `Ctrl+Shift+V` | ターミナルへ貼り付け |

---

## 重要な学び・気づき

- 全部理解しようとせず動かして楽しむ方が伸びる
- エラーは恐れず全文コピペで質問
- Claude Codeは「育てる」道具（最初から完璧な指示は不要）
- 指示する時は: 目的・条件・例・注意点・完成イメージ
- 「既存を壊さないで」と書くのが重要テクニック

---

## トラブルシューティング履歴

| 問題 | 解決策 |
|---|---|
| VS Codeのフォルダ承認プロンプトが毎回出る | settings.jsonで信頼済みフォルダに登録して解決 |
| pipで `externally-managed-environment` エラー | `--break-system-packages` オプションで解決 |
| Claude Codeから抜けられない | `Ctrl+C 2回` または `/exit` で解決 |

---

## 今後の学習予定

- [x] CLAUDE.md でプロジェクト設定を作る
- [ ] エラー対応の型を身につける
- [ ] Threads 開発者登録
- [ ] SNS API での自動投稿
- [ ] 定期実行の仕組み（cron / クラウド）
- [ ] 複数SNSへの横展開

---

## 学習履歴

| 日付 | やったこと | 学んだこと |
|---|---|---|
| 4/23 | 環境構築、おみくじ作成 | WSL2/VS Code/Claude Code セットアップ、Pythonの基本 |
| 4/24 | じゃんけん、天気予報作成 | API通信、JSON、勝敗判定ロジック |
| 4/25 | タイマー・数当て・曜日表示作成、learning_notes.md・CLAUDE.md作成 | 指示文の書き方、CLAUDE.mdでClaudeに好みを覚えさせる方法、エラー自己解決 |
| 6/4 | reaction_dashboard.py作成、ronin反応収集のcomments→500修正、ronin/skin analyzerの+0000日付バグ修正 | 複数JSONの集約・既存ファイルを壊さない「読むだけ」設計、複数日時フォーマットのパース、try/exceptで部分失敗しても全体を止めないエラー処理 |

---

## 学習継続の記録

- 学習開始: 2026年4月23日
- 連続学習日数: （Claude Codeの `/stats` で確認可能）
