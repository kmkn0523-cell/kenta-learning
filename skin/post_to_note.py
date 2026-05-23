# post_to_note.py
# note.com に自動投稿するスクリプト
# release_note.py が出力した note_ready.md を読み込み、
# Playwright を使ってブラウザを操作し記事を公開する。
# GitHub Actions の skin_note_release.yml から呼び出される。
#
# 必要な環境変数:
#   - NOTE_SESSION_V5: note.com のセッションクッキー値（Chrome DevToolsから抽出）
#
# 進捗管理:
#   - note_queue_progress.json の history 配列に投稿履歴を追加する

import os                                      # 環境変数を読み取るための道具
import sys                                     # エラー時に終了するための道具
import re                                      # 正規表現で文字列を切り出す道具
import json                                    # JSONファイルを読み書きする道具
import asyncio                                 # 非同期処理を動かすための道具
from pathlib import Path                       # ファイルパスを扱う道具
from datetime import datetime, timezone, timedelta  # 日付・時刻を扱う道具

# ファイルパスを定義する（このスクリプトと同じフォルダ＝skin/ を基準）
BASE_DIR = Path(__file__).parent                          # skinフォルダ
READY_FILE = BASE_DIR / "note_ready.md"                   # 今週の記事
PROGRESS_FILE = BASE_DIR / "note_queue_progress.json"     # 進捗記録
LP_MAP_FILE = BASE_DIR / "note_lp_map.json"               # 記事→LP画像のマッピング
SCREENSHOT_DIR = BASE_DIR / "note_screenshots"            # デバッグ用スクショ置き場

# 日本時間のタイムゾーン（GitHub Actionsは UTC で動くので明示する）
JST = timezone(timedelta(hours=9))


def parse_ready_file():
    """note_ready.md からタイトル・本文・記事ファイル名を取り出す"""
    # ファイルがなければエラー終了する
    if not READY_FILE.exists():
        print(f"❌ {READY_FILE} が見つかりません")
        sys.exit(1)

    # ファイル全体を読み込む
    content = READY_FILE.read_text(encoding="utf-8")

    # 1行目のコメントから記事ファイル名を抽出する
    match = re.search(r"<!--.*?\|\s*(article_\d+\.md)", content)
    article_filename = match.group(1) if match else "unknown.md"

    # コメント行を除外する（HTMLコメントはnoteには貼らない）
    lines = [line for line in content.split("\n") if not line.startswith("<!--")]
    cleaned = "\n".join(lines).strip()

    # 最初のH1見出しをタイトルとして取り出す
    body_lines = cleaned.split("\n")
    title = ""
    body_start_index = 0
    for index, line in enumerate(body_lines):
        if line.startswith("# "):
            title = line[2:].strip()
            body_start_index = index + 1
            break

    # H1見出し以降を本文として取り出す（前後の空行を削除）
    body = "\n".join(body_lines[body_start_index:]).strip()

    return article_filename, title, body


def get_cover_image_path(article_filename):
    """note_lp_map.json から記事に対応するLP画像のパスを取得する"""
    try:
        with open(LP_MAP_FILE, "r", encoding="utf-8") as f:
            lp_map = json.load(f)
    except FileNotFoundError:
        return None

    # マッピングからファイル名を取り出す
    lp_filename = lp_map.get(article_filename)
    if not lp_filename:
        return None

    # 実ファイルが存在するか確認してから返す
    lp_path = BASE_DIR / lp_filename
    return str(lp_path) if lp_path.exists() else None


async def take_screenshot(page, name):
    """デバッグ用にスクリーンショットを保存する（失敗解析用）"""
    SCREENSHOT_DIR.mkdir(exist_ok=True)
    path = SCREENSHOT_DIR / f"{name}.png"
    try:
        await page.screenshot(path=str(path), full_page=True)
        print(f"📸 スクリーンショット: {path}")
    except Exception as e:
        print(f"⚠️ スクリーンショット失敗 ({name}): {e}")


def is_draft_mode():
    """環境変数 NOTE_DRAFT_MODE が真値ならテスト/下書きモード"""
    val = os.environ.get("NOTE_DRAFT_MODE", "").strip().lower()
    return val in ("1", "true", "yes", "on")


async def post_to_note_com(title, body_markdown, cover_image_path):
    """note.com にログインして記事を公開し、公開後のURLを返す"""
    draft_mode = is_draft_mode()
    if draft_mode:
        print("🧪 下書きモード（DRAFT_MODE=true）：公開せず下書き保存のみ実行")

    # 環境変数からクッキー値を取得する
    cookie_value = os.environ.get("NOTE_SESSION_V5", "").strip()
    if not cookie_value:
        print("❌ NOTE_SESSION_V5 環境変数が設定されていません")
        print("   GitHub Secrets に NOTE_SESSION_V5 を登録してください")
        print("   抽出手順: docs/note_cookie_setup.md")
        sys.exit(1)

    # Playwrightは動的importにする（ローカルで未インストールでも他のスクリプトを壊さないため）
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("❌ playwright がインストールされていません")
        print("   pip install playwright && playwright install chromium")
        sys.exit(1)

    async with async_playwright() as p:
        # ヘッドレスChromiumを起動する（GitHub Actionsで画面なし動作）
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",  # Playwright検知回避
                "--no-sandbox",                                    # GitHub Actions用
            ],
        )

        # ブラウザコンテキストを作る（クッキー・タイムゾーン・言語を日本仕様に）
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1440, "height": 900},
            locale="ja-JP",
            timezone_id="Asia/Tokyo",
        )

        # セッションクッキーを注入してログイン状態を再現する
        await context.add_cookies([{
            "name": "_note_session_v5",
            "value": cookie_value,
            "domain": ".note.com",
            "path": "/",
            "httpOnly": True,
            "secure": True,
            "sameSite": "Lax",
        }])

        page = await context.new_page()

        # 新規記事ページを開く（note.comエディタに遷移する）
        print("🌐 noteエディタを開いています...")
        await page.goto(
            "https://note.com/notes/new",
            wait_until="domcontentloaded",
            timeout=60000,
        )
        await page.wait_for_timeout(5000)
        await take_screenshot(page, "01_editor_opened")

        # ログイン状態を確認する（URLにloginが含まれていたら失敗）
        if "login" in page.url:
            print(f"❌ ログイン失敗: クッキー期限切れの可能性（リダイレクト先: {page.url}）")
            await take_screenshot(page, "error_login_failed")
            await context.close()
            await browser.close()
            sys.exit(1)

        # タイトル入力欄を見つけて入力する
        print(f"📌 タイトルを入力: {title}")
        title_input = page.locator("textarea[placeholder*='タイトル']").first
        await title_input.wait_for(state="visible", timeout=20000)
        await title_input.click()
        await title_input.fill(title)
        await page.wait_for_timeout(1500)

        # カバー画像をアップロードする（LP画像が存在する場合のみ）
        if cover_image_path:
            print(f"🖼️ カバー画像をアップロード: {cover_image_path}")
            try:
                # まずデバッグ：エディタ上の input/button の状態をログ出力する
                init_input_count = await page.locator('input[type="file"]').count()
                print(f"   初期 input[type=file] 数: {init_input_count}")

                # 戦略：アイコンクリックで input を動的生成 → file_chooser を待ち受け
                # タイトル左上の画像追加アイコンを複数セレクタで探す
                candidate_selectors = [
                    'button[aria-label*="画像"]',
                    'button[aria-label*="カバー"]',
                    'button[aria-label*="サムネイル"]',
                    'button[aria-label*="アイキャッチ"]',
                    'button[aria-label*="image"]',
                    '[data-testid*="cover"]',
                    '[data-testid*="thumbnail"]',
                    '[data-v-cover-image]',
                    # タイトルtextareaの兄弟/親側にある最初の button
                    'form button:has(svg)',
                ]

                cover_btn = None
                matched_selector = None
                for sel in candidate_selectors:
                    loc = page.locator(sel).first
                    if await loc.count() > 0 and await loc.is_visible():
                        cover_btn = loc
                        matched_selector = sel
                        break

                if cover_btn is None:
                    # 最終手段：エディタ内の全 button の aria-label をデバッグ出力
                    all_buttons = page.locator("button")
                    btn_count = await all_buttons.count()
                    print(f"   エディタ内 button 総数: {btn_count}")
                    for i in range(min(btn_count, 15)):
                        try:
                            label = await all_buttons.nth(i).get_attribute("aria-label")
                            text = (await all_buttons.nth(i).inner_text())[:30]
                            print(f"   button[{i}]: aria-label={label!r} text={text!r}")
                        except Exception:
                            pass
                    raise Exception("カバー画像ボタンが見つかりません（上のデバッグログ参照）")

                print(f"   マッチしたセレクタ: {matched_selector}")

                # ステップ1: アイコンをクリックしてメニューを開く
                await cover_btn.click()
                await page.wait_for_timeout(1500)
                await take_screenshot(page, "02a_cover_menu_opened")

                # ステップ2: メニュー内の「画像をアップロード」をクリック → file_chooser
                upload_item = page.get_by_text("画像をアップロード", exact=False).first
                async with page.expect_file_chooser(timeout=15000) as fc_info:
                    await upload_item.click()

                file_chooser = await fc_info.value
                await file_chooser.set_files(cover_image_path)
                await page.wait_for_timeout(8000)
                await take_screenshot(page, "02_image_uploaded")

                # トリミングモーダルの確定ボタン
                save_btn = page.get_by_role("button", name=re.compile("保存|適用|決定|完了"))
                if await save_btn.count() > 0:
                    await save_btn.first.click()
                    await page.wait_for_timeout(3000)
                    await take_screenshot(page, "02b_image_saved")
            except Exception as e:
                print(f"⚠️ カバー画像アップロード失敗（記事本文のみで進めます）: {e}")
                await take_screenshot(page, "error_image_upload")

        # 本文エディタをクリックして入力モードにする
        print("✍️ 本文を入力中...")
        body_editor = page.locator("[contenteditable='true']").first
        await body_editor.click()
        await page.wait_for_timeout(1000)

        # マークダウンを1行ずつタイプする
        # note.comのエディタは "# " "## " "**bold**" "- " などの記法を自動変換するため、
        # マークダウン記法のままタイプすれば見出し・太字・リストが正しく成形される
        body_lines = body_markdown.split("\n")
        for line in body_lines:
            if line == "":
                # 空行は Enter のみ
                await page.keyboard.press("Enter")
            else:
                # 1文字ずつタイプして改行（delayは小さくして高速化）
                await page.keyboard.type(line, delay=5)
                await page.keyboard.press("Enter")

        await page.wait_for_timeout(3000)
        await take_screenshot(page, "03_body_typed")

        if draft_mode:
            # 下書きモード：エディタ右上の「下書き保存」をクリックして終了
            print("💾 下書き保存を実行...")
            draft_btn = page.get_by_role("button", name=re.compile("下書き保存|下書きに保存"))
            if await draft_btn.count() == 0:
                # フォールバック：テキストで一致する button を探す
                draft_btn = page.locator("button:has-text('下書き')")
            await draft_btn.first.click()
            await page.wait_for_timeout(6000)
            await take_screenshot(page, "04_draft_saved")
            post_url = page.url
            print(f"✅ 下書き保存完了: {post_url}")
        else:
            # 「公開に進む」ボタンを探してクリックする（エディタ右上）
            print("🚀 公開フローを開始...")
            publish_btn = page.get_by_role("button", name=re.compile("公開に進む|公開"))
            await publish_btn.first.click()
            await page.wait_for_timeout(3000)
            await take_screenshot(page, "04_publish_modal")

            # 公開モーダル内の「投稿する」/「公開する」ボタンをクリックする
            # 複数候補がある場合はモーダル内の最後のボタンが本物の確定ボタン
            confirm_btn = page.get_by_role("button", name=re.compile("投稿する|公開する"))
            await confirm_btn.last.click()
            await page.wait_for_timeout(10000)  # 投稿処理完了 + リダイレクト待ち
            await take_screenshot(page, "05_published")

            # 公開後のURLを取得する（note.com/{username}/n/{id} 形式）
            post_url = page.url
            print(f"✅ 投稿完了: {post_url}")

        await context.close()
        await browser.close()

        return post_url


def update_progress(article_filename, title, post_url):
    """note_queue_progress.json に投稿履歴を追加する（既存のnext_indexは保持）"""
    # 進捗ファイルを読み込む（release_note.pyが next_index を更新済み）
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        progress = json.load(f)

    # history 配列がなければ作成する
    if "history" not in progress:
        progress["history"] = []

    # 新しい履歴エントリを追加する（Substackの substack_progress.json と同じ構造）
    history_entry = {
        "date": datetime.now(JST).strftime("%Y/%m/%d %H:%M"),
        "article": article_filename,
        "title": title,
        "post_url": post_url,
    }
    progress["history"].append(history_entry)

    # ファイルに書き戻す
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

    print(f"📝 進捗ファイルに履歴を追加: {history_entry['date']} {article_filename}")


async def main():
    """メイン処理: note_ready.md を読み込み → note.com に投稿 → 進捗を記録"""
    print(f"=== note.com 自動投稿開始 ({datetime.now(JST).strftime('%Y/%m/%d %H:%M')}) ===")

    # note_ready.md を解析する
    article_filename, title, body = parse_ready_file()
    print(f"📄 記事: {article_filename}")
    print(f"📌 タイトル: {title}")
    print(f"📝 本文長: {len(body)} 文字")

    # カバー画像のパスを取得する
    cover_image_path = get_cover_image_path(article_filename)
    if cover_image_path:
        print(f"🖼️ カバー画像: {cover_image_path}")
    else:
        print(f"⚠️ カバー画像が見つかりません（{article_filename}）")

    # note.com に投稿する（戻り値は公開後のURL）
    post_url = await post_to_note_com(title, body, cover_image_path)

    # 下書きモードでは進捗ファイルを更新しない（本番履歴を汚さないため）
    if is_draft_mode():
        print("🧪 下書きモードのため history への書き込みはスキップ")
    else:
        update_progress(article_filename, title, post_url)

    print("=== 完了 ===")


if __name__ == "__main__":
    asyncio.run(main())
