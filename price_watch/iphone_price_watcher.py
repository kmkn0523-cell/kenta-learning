"""iPhone 17 Pro Max 512GB の買取最高価格を監視して、変わったらメール通知するスクリプト。

やること（おおまかな流れ）:
1. りんごの奴隷にログインする（Playwrightでブラウザ操作）
2. 価格ツールのページを開く
3. iPhone 17 Pro Max 512GB の店舗買取価格の最高値を読み取る
4. 前回の値（iphone_price_state.json）と比べる
5. 変わっていたらGmailで自分宛にメールを送る
6. 新しい値を記録ファイルに保存する

ローカルでもGitHub Actionsでも動く。秘密情報はすべて環境変数（.env または Secrets）から読む。
"""
import os
import re
import json
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime, timezone, timedelta
from pathlib import Path

# .env があれば読み込む（GitHub Actionsでは環境変数が直接入るので無くてもOK）
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ===== 設定 =====
LOGIN_URL = "https://ringonodorei.com/admin/login"  # ログイン画面
TOOL_URL = "https://ringonodorei.com/admin/purchase-price-tool"  # 価格ツール
TARGET_MODEL = "iPhone 17 Pro Max"  # 監視する機種名
TARGET_CAPACITY = "512GB"  # 監視する容量
STATE_FILE = Path(__file__).with_name("iphone_price_state.json")  # 前回価格の記録先
JST = timezone(timedelta(hours=9))  # 日本時間


def now_jst_text() -> str:
    """今の日本時間を読みやすい文字列で返す。"""
    return datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")


def parse_max_price(model_text: str, row_text: str) -> int | None:
    """1行分のテキストから、店舗買取価格の最高値（円・整数）を取り出す。

    model_text: その行の機種名（例 'iPhone 17 Pro Max 512GB シルバー'）。
    row_text:   その行の表示テキスト全体（店舗価格や差額を含む）。
    対象機種・容量に合わない行は None を返す。
    定価（¥付き）や差額（円の前に空白なし）は最大値計算に影響しないので自然に除外される。
    """
    # 対象の機種・容量でなければ無視する
    if TARGET_MODEL not in model_text or TARGET_CAPACITY not in model_text:
        return None
    # 「数字 円」（円の直前に空白あり）の形だけを店舗価格として拾う。定価は ¥ 記号なので除外。
    matches = re.findall(r"([0-9]{1,3}(?:,[0-9]{3})+)\s+円", row_text)
    prices = [int(m.replace(",", "")) for m in matches]
    if not prices:
        return None
    return max(prices)


def parse_list_price(model_text: str, row_text: str) -> int | None:
    """1行分のテキストから、定価（¥付き数値・整数）を取り出す。

    model_text: その行の機種名。row_text: その行の表示テキスト全体。
    対象機種・容量に合わない行や、定価が見つからない行は None を返す。
    定価は「¥229,800」のように ¥ 記号付きで書かれている。
    """
    # 対象の機種・容量でなければ無視する
    if TARGET_MODEL not in model_text or TARGET_CAPACITY not in model_text:
        return None
    # 「¥数字」の形（カンマ区切りでもなくてもOK）を定価として拾う
    matches = re.findall(r"¥\s*([0-9]{1,3}(?:,[0-9]{3})*)", row_text)
    prices = [int(m.replace(",", "")) for m in matches]
    if not prices:
        return None
    # 定価は1機種につき1つの想定。複数あれば最大を採用（保険）
    return max(prices)


def fetch_highest_price() -> dict:
    """ログインして価格ページを開き、対象機種の最高買取価格を返す。

    戻り値: {"price": int, "label": str, "list_price": int | None}
    （labelは最高値だった行の機種名、list_priceはその行の定価。定価が無ければ None）。
    取得できなければ ValueError を投げる。
    """
    from playwright.sync_api import sync_playwright

    email = os.environ["RINGONODOREI_EMAIL"]  # ログイン用メール
    password = os.environ["RINGONODOREI_PASSWORD"]  # ログイン用パスワード

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # 画面なしブラウザ
        page = browser.new_page()
        page.set_default_timeout(30000)  # 各操作30秒待ち
        try:
            # ログイン画面を開いてメール・パスワードを入力（Tabでblurし、Livewireへ反映）
            page.goto(LOGIN_URL, wait_until="domcontentloaded")
            page.query_selector("input[type=email]").fill(email)
            page.keyboard.press("Tab")
            page.query_selector("input[type=password]").fill(password)
            page.keyboard.press("Tab")
            page.wait_for_timeout(800)
            page.query_selector("button[type=submit]").click()
            # ログイン画面から離れられなければ失敗
            page.wait_for_url(lambda u: "/admin/login" not in u, timeout=25000)

            # 価格ツールを開いて動的描画を待つ
            page.goto(TOOL_URL, wait_until="domcontentloaded")
            page.wait_for_timeout(4000)

            # 各行（tr）から「機種名」と「行テキスト」を取り出す
            rows = page.evaluate(
                r"""
                () => {
                  const result = [];
                  document.querySelectorAll('tr').forEach(tr => {
                    // 行の中の open-chart 呼び出しから機種名を取得
                    const link = tr.querySelector('a[\\@click\\.prevent], a[href="#"]');
                    let model = '';
                    if (link) {
                      const attr = link.getAttribute('@click.prevent') || '';
                      const m = attr.match(/model:\s*'([^']+)'/);
                      if (m) model = m[1];
                    }
                    if (!model) model = tr.innerText;  // 取れなければ行テキストで代用
                    result.push({ model: model, text: tr.innerText });
                  });
                  return result;
                }
                """
            )
        finally:
            browser.close()

    # 対象機種の各行から最高値を集め、その中の最大を「最高買取価格」とする
    best_price = None
    best_label = ""
    best_list_price = None  # 最高値だった行の定価（取れなければ None）
    for row in rows:
        price = parse_max_price(row["model"], row["text"])
        if price is not None and (best_price is None or price > best_price):
            best_price = price
            best_label = row["model"]
            best_list_price = parse_list_price(row["model"], row["text"])

    if best_price is None:
        raise ValueError(
            f"{TARGET_MODEL} {TARGET_CAPACITY} の価格が見つかりませんでした。ページ構造が変わった可能性があります。"
        )
    return {"price": best_price, "label": best_label, "list_price": best_list_price}


def load_last_price() -> int | None:
    """記録ファイルから前回価格を読む。無ければ None。"""
    if not STATE_FILE.exists():
        return None
    try:
        data = json.loads(STATE_FILE.read_text())
        return data.get("price")
    except Exception:
        return None


def format_vs_list_price(price: int, list_price: int | None) -> str:
    """買取価格が定価からプラスマイナスいくらかを表す文字列を返す。

    例: 定価¥229,800・買取230,000円 → '定価 ¥229,800 から +200円'。
    定価が取れていなければ '定価: 不明' を返す。
    """
    if list_price is None:
        return "定価: 不明"
    diff = price - list_price  # 買取 − 定価（ふつうはマイナス＝定価より安い）
    sign = "+" if diff >= 0 else ""  # マイナスは数値側に符号が付く
    return f"定価 ¥{list_price:,} から {sign}{diff:,}円"


def save_price(price: int, label: str, list_price: int | None = None) -> None:
    """今回価格を記録ファイルに保存する。"""
    data = {
        "model": f"{TARGET_MODEL} {TARGET_CAPACITY}",
        "price": price,
        "label": label,
        "list_price": list_price,
        "updated_at": now_jst_text(),
    }
    STATE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def send_email(subject: str, body: str) -> None:
    """Gmailで自分宛にメールを送る（アプリパスワードを使う）。"""
    gmail_address = os.environ["GMAIL_ADDRESS"]  # 送信元Gmail
    gmail_app_password = os.environ["GMAIL_APP_PASSWORD"]  # アプリパスワード
    notify_to = os.environ.get("NOTIFY_TO", gmail_address)  # 通知先（既定は自分宛）

    message = MIMEText(body, "plain", "utf-8")
    message["Subject"] = Header(subject, "utf-8")
    message["From"] = gmail_address
    message["To"] = notify_to

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_address, gmail_app_password)
        server.sendmail(gmail_address, [notify_to], message.as_string())


def main() -> None:
    """全体の処理を実行する。"""
    try:
        result = fetch_highest_price()
    except Exception as error:
        # 取得に失敗したら、黙って終わらず失敗を知らせる
        print(f"[ERROR] 価格取得に失敗: {error}")
        try:
            send_email(
                subject="【取得失敗】iPhone買取価格チェック",
                body=f"価格の取得に失敗しました。\n\n理由: {error}\n時刻: {now_jst_text()}\n確認: {TOOL_URL}",
            )
        except Exception as mail_error:
            print(f"[ERROR] 失敗通知メールも送れませんでした: {mail_error}")
        raise

    price = result["price"]
    label = result["label"]
    list_price = result["list_price"]  # 定価（取れなければ None）
    vs_list = format_vs_list_price(price, list_price)  # 定価からの差額の文章
    last = load_last_price()
    print(f"今回価格: {price:,}円（{vs_list}） / 前回価格: {last if last is None else format(last, ',') + '円'}")

    if last is None:
        # 初回は通知せず、記録だけする
        save_price(price, label, list_price)
        print("初回のため記録のみ（通知なし）")
        return

    if price != last:
        # 値が変わっていれば通知する
        diff = price - last
        sign = "+" if diff > 0 else ""
        subject = f"【値動き】iPhone17ProMax 512GB 買取 {sign}{diff:,}円"
        body = (
            f"前回 {last:,}円 → 今回 {price:,}円（前回差 {sign}{diff:,}円）\n"
            f"{vs_list}\n"
            f"対象: {label}\n"
            f"確認: {TOOL_URL}\n"
            f"取得時刻: {now_jst_text()}\n"
        )
        send_email(subject, body)
        save_price(price, label, list_price)
        print(f"値動きあり → メール送信（{sign}{diff:,}円 / {vs_list}）")
    else:
        # 変わっていなくても、毎回チェック結果を通知する（設定B）
        subject = f"【変化なし】iPhone17ProMax 512GB 買取 {price:,}円"
        body = (
            f"今日も価格は変わっていません。\n"
            f"現在の買取最高価格 {price:,}円（前回と同じ）\n"
            f"{vs_list}\n"
            f"対象: {label}\n"
            f"確認: {TOOL_URL}\n"
            f"取得時刻: {now_jst_text()}\n"
        )
        send_email(subject, body)
        save_price(price, label, list_price)
        print("変化なし → チェック結果メール送信")


if __name__ == "__main__":
    main()
