# ログイン画面と価格ページの構造を一度だけ確認するための一時スクリプト（後で削除する）
# パスワードは画面に出さない。スクリーンショットとテキストだけ残す。
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()  # .env を読み込む
EMAIL = os.environ["RINGONODOREI_EMAIL"]  # ログイン用メール
PASSWORD = os.environ["RINGONODOREI_PASSWORD"]  # ログイン用パスワード
LOGIN_URL = "https://ringonodorei.com/admin/login"  # ログイン画面
TOOL_URL = "https://ringonodorei.com/admin/purchase-price-tool"  # 価格ツール

out = Path("price_watch")  # 出力先フォルダ
out.mkdir(exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)  # 画面なしブラウザを起動
    page = browser.new_page()
    page.set_default_timeout(30000)  # 各操作の待ち時間を30秒に

    # ログイン画面を開く
    page.goto(LOGIN_URL, wait_until="networkidle")

    # メール欄・パスワード欄に入力（Livewireに同期させるためTabでblurする）
    email_box = page.query_selector("input[type=email]")
    pass_box = page.query_selector("input[type=password]")
    email_box.click()
    email_box.fill(EMAIL)
    page.keyboard.press("Tab")  # blurでLivewireへ反映
    pass_box.click()
    pass_box.fill(PASSWORD)
    page.keyboard.press("Tab")
    page.wait_for_timeout(800)  # Livewireの同期待ち

    # 送信ボタンを押す
    btn = page.query_selector("button[type=submit]") or page.query_selector("button:has-text('ログイン')")
    print("submit button found:", bool(btn))
    btn.click()

    # ログイン画面から離れるのを待つ（最大25秒）。離れなければ失敗。
    try:
        page.wait_for_url(lambda u: "/admin/login" not in u, timeout=25000)
        print("login redirect ok ->", page.url)
    except Exception:
        print("still on login page ->", page.url)

    page.wait_for_load_state("networkidle")
    page.screenshot(path=str(out / "02_after_login.png"), full_page=True)

    # ログイン失敗時はエラーメッセージらしき文を出して終了
    if "/admin/login" in page.url:
        body = page.inner_text("body")
        print("=== possible error lines ===")
        for line in body.splitlines():
            if re.search(r"正し|失敗|一致|error|invalid|認証|無効", line, re.I):
                print(repr(line.strip())[:160])
        browser.close()
        raise SystemExit("login failed")

    # 価格ツールを開く
    page.goto(TOOL_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(4000)  # 動的描画を待つ
    print("=== url at price tool ===", page.url)
    page.screenshot(path=str(out / "03_price_tool.png"), full_page=True)

    # ページ全体のテキストを保存
    body_text = page.inner_text("body")
    (out / "price_tool_text.txt").write_text(body_text)
    print("page text length:", len(body_text))

    # "Pro Max" / 512 / 円 を含む行を表示
    print("=== lines with 'Pro Max' / '512' / '17' / 円 ===")
    shown = 0
    for line in body_text.splitlines():
        s = line.strip()
        if s and re.search(r"Pro\s*Max|512|17\s*Pro|¥|円|,\d{3}", s):
            print(repr(s)[:160])
            shown += 1
            if shown > 60:
                break

    browser.close()
print("done")
