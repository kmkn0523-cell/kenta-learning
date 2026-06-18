# iPhone買取価格 値動き通知 設計書

作成日: 2026-06-18

## 目的
りんごの奴隷（`ringonodorei.com`）の買取価格ツールを定期的に確認し、
`iPhone 17 Pro Max 512GB` の価格が前回から変わっていたら、Kenta宛にメールで通知する。

## 前提・決定事項
- 価格はログイン後の管理画面 `/admin/purchase-price-tool` の中にある（公開ページには無い）。
- ログイン情報（メール・パスワード）はKentaのアカウントを使い、自動ログインで取得する。
- 通知先は **Gmail（自分宛メール）**。LINE Notifyは2025年3月終了のため不採用。
- チェック頻度は **1日に数回**（GitHub Actionsのcron、例: 朝7時・昼13時・夜21時 JST）。
- 通知条件は **少しでも価格が変わったら**（前回と1円でも違えば通知）。
- 監視する価格は **暫定で「最高買取価格」**。PCでログイン画面を実際に見たうえで最終確定する
  （業者ごと表示か・代表値かを確認し、必要なら特定業者に変更）。

## 取得方式
**Playwright（ヘッドレスブラウザ）を採用。**
りんごの奴隷は動的なWebアプリの可能性が高く、価格がHTMLに直接無い場合でも、
画面に描画された数字を確実に読み取れるため。仕組みが変わっても直しやすい。

## ファイル構成
```
/price_watch/
  iphone_price_watcher.py      本体（ログイン→価格取得→比較→メール送信）
  iphone_price_state.json      前回価格を記録（GitHub Actionsが書き換え。手動編集禁止）
.github/workflows/
  iphone_price_watch.yml       1日数回の定期実行
```

## 処理の流れ
1. `.env` / GitHub Secrets から認証情報を読む
   （`RINGONODOREI_EMAIL`, `RINGONODOREI_PASSWORD`, `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`）。
2. Playwrightで `ringonodorei.com` にログイン。
3. `/admin/purchase-price-tool` を開き、`iPhone 17 Pro Max` の `512GB` の最高買取価格を読み取る。
4. `iphone_price_state.json` の前回価格と比較する。
5. 価格が変わっていたら、Gmail（SMTP・アプリパスワード）で自分宛にメール送信。
6. `iphone_price_state.json` を新しい価格に更新し、GitHub Actionsがコミット
   （既存の `progress.json` 系と同じ運用）。

## 通知メールの形式
```
件名: 【値動き】iPhone17ProMax 512GB 買取 +3,000円
本文:
  前回 198,000円 → 今回 201,000円（差額 +3,000円）
  確認: https://ringonodorei.com/admin/purchase-price-tool
  取得時刻: 2026-06-18 13:00 JST
```

## エラーハンドリング
- ログイン失敗・価格が画面で見つからない場合は、黙って終了せず「取得失敗」メールを送る。
- 初回（`state.json` に前回価格が無い）は通知せず、価格の記録だけ行う。
- Playwrightのタイムアウトは余裕を持たせ（例: 30秒）、失敗時はスクリーンショットをActionsのログに残す。

## 秘密情報の扱い
- ローカルは `.env`、本番（GitHub Actions）は Secrets に保存。コードに直書きしない。
- Gmailは通常パスワードではなく「アプリパスワード」を使う（2段階認証前提）。

## 利用規約の確認（実装前にKentaとPCで確認）
- りんごの奴隷の利用規約・robots等で、会員エリアへの自動アクセス／スクレイピングが
  禁止されていないかを実装着手前に確認する。問題があれば方式を見直す。

## テスト
- `state.json` 比較ロジック（変化あり／なし／初回）は、Playwright無しで単体テスト可能にする。
  価格取得部分と通知部分を関数として分離し、比較・通知判定だけを `tests/` でテストする。

## 実装時に画面を見て確定する項目
- 価格表のHTML構造（どの要素に価格があるか / セレクタ）。
- 「最高買取価格」がそのまま1つ表示されるのか、業者一覧から最大を取るのか。
- ログインフォームの入力欄・ボタンのセレクタ、ログイン後の遷移。
