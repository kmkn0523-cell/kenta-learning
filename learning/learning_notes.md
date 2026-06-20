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
| 6/7 | ronin_hashtags.py | @RoninWordsのハッシュタグを4セットで回す（純粋関数） | 投稿カウントの余りでローテーション、純粋関数はI/Oと分離してテストしやすくする |
| 6/7 | ronin_engagement.py | コメント誘発投稿(engagement post)の在庫ロード/選択/検証 | JSON在庫の読込・選択、必須キー/字数/重複のバリデーション、検証関数をエラー文字列リストで返す設計 |
| 6/7 | ronin_comment_seeder.py | 投稿直後に付ける「1コメ目」の文章生成（純粋関数） | 早期リプライでreachを伸ばす考え方、本文とリンクの分離、500字丸め |
| 6/15 | skin_reply_engine.py | skin Threads自動リプライ・エンジン（keyword_searchで見つけた投稿にテンプレ返信） | 公式keyword_search API、純粋関数のTDD（分類/選別/合成/状態）とネットワークI/Oの分離、日次上限・著者上限・連投禁止のスロットル、環境変数キルスイッチ、GitHub Actionsで状態をキャッシュ＋コミット永続化 |
| 6/16 | skin_reply_review_ui.py | skin リプライ運用者ビュー（keyword_search結果を一覧表示し人が確認して返信するローカルWeb UI・App Review用） | 標準ライブラリhttp.serverだけでWeb UI（新ライブラリ無し）、エンジンの純粋関数を再利用（DRY）、--demoモードでトークン無しでも動作確認・スクリーンキャスト録画、HTMLエスケープでXSS対策、送信は人の確認後に1件ずつ |
| 6/16 | ronin/ronin_reply_engine.py | @RoninWords Threads自動リプライ・エンジン（skin版の英語アカウント移植） | skin_reply_engineと同構造を英語アカウントに移植、日本語判定→英語判定(contains_english)に差し替え、自己投稿除外を大小無視に、ronin専用トークン(RONIN_THREADS_ACCESS_TOKEN)、英語キーワード15件、テスト27件、別キルスイッチ(RONIN_REPLY_ENGINE_ENABLED) |
| 6/16 | ronin/ronin_reply_review_ui.py | ronin リプライ運用者ビュー（skin UIの@RoninWords版・英語・App Review用） | 標準ライブラリhttp.serverのみ、ronin_reply_engineの純粋関数を再利用、--demoで英語サンプル表示、ポート8766でskin版と非衝突、HTMLエスケープでXSS対策 |
| 6/15 | skin_reels_engine.py | 既存カルーセル画像からffmpegで縦型Reelsを自動生成・投稿（generate→push→publishの2フェーズ） | ffmpegコマンドのlist組み立てとsubprocess実行、9:16/5〜90秒のReels要件、media_type=REELSの3ステップ公開、動画をgit pushして公開URLを生やす設計、wait_for_urlで配信待ち、既存publish関数の遅延import再利用 |
| 6/18 | price_watch/iphone_price_watcher.py | りんごの奴隷のiPhone17ProMax512GB買取最高価格を監視し、前回から変わったらGmail通知（GitHub Actionsで1日3回） | Playwrightでログイン要のFilament/Livewire画面を操作、純粋関数parse_max_priceを抽出ロジックとして分離しTDD（円付き数値の最大＝差額や¥定価を自然除外）、smtplib+Gmailアプリパスワードで自分宛メール、状態JSONをコミットで永続化、取得失敗も黙らず通知 |
| 6/21 | jewelry_watch/jewelry_sns_digest.py | 「サントスネックレス」「ジュストアンクルブレスレット」のSNS言及をExa検索でX/Instagram/Threads/Web横断収集し、新規分だけHTMLメールで週1回(土曜7:30 JST)通知 | Exa Web検索APIでSNSドメイン横断（無料運用）、純粋関数（パース/重複除外/HTML生成）とAPI/メールI/Oを分離しTDD（14件）、URL単位の重複防止＋60日でstate掃除、html.escape(quote=True)＋hrefスキーム検証でXSS対策、1クエリ失敗でも他は継続、状態JSONをコミットで永続化 |

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
| 6/7 | @RoninWords reach加速：コメント誘発投稿32本＋1コメ目自動シード＋動的ハッシュタグ＋analyzer 0日バグ修正（TDD・feature隔離→mainマージ） | Threadsはリプライ数で非フォロワー拡散が決まる、reply_to_idで自分の投稿に返信、本文クリーン化で配信抑制回避、auto_syncがmainを自動pushするのでfeatureブランチで本番保護、純粋関数のTDD、死んだコードの撤去 |

---

## 学習継続の記録

- 学習開始: 2026年4月23日
- 連続学習日数: （Claude Codeの `/stats` で確認可能）
