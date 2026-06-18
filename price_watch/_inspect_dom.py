# iPhone 17 Pro Max 512GB のブロックのHTML構造を調べる一時スクリプト（後で削除）
import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
EMAIL = os.environ["RINGONODOREI_EMAIL"]
PASSWORD = os.environ["RINGONODOREI_PASSWORD"]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.set_default_timeout(30000)
    page.goto("https://ringonodorei.com/admin/login", wait_until="networkidle")
    page.query_selector("input[type=email]").fill(EMAIL)
    page.keyboard.press("Tab")
    page.query_selector("input[type=password]").fill(PASSWORD)
    page.keyboard.press("Tab")
    page.wait_for_timeout(800)
    page.query_selector("button[type=submit]").click()
    page.wait_for_url(lambda u: "/admin/login" not in u, timeout=25000)
    page.goto("https://ringonodorei.com/admin/purchase-price-tool", wait_until="domcontentloaded")
    page.wait_for_timeout(4000)

    # "iPhone 17 Pro Max" を含む見出し要素から、512GBと価格を含む祖先ブロックを特定
    info = page.evaluate(
        r"""
        () => {
          // テキストが完全一致する要素を探す
          const all = Array.from(document.querySelectorAll('*'));
          const head = all.find(el =>
            el.children.length === 0 && el.textContent.trim() === 'iPhone 17 Pro Max');
          if (!head) return {found:false};
          // 512GB と 円 を両方含む最小の祖先を探す
          let node = head;
          for (let i=0; i<8; i++) {
            if (node.parentElement) node = node.parentElement;
            const t = node.textContent;
            if (t.includes('512GB') && t.includes('円')) break;
          }
          // 価格らしき "NNN,NNN 円" を抽出
          const prices = (node.textContent.match(/\d{1,3}(?:,\d{3})+\s*円/g) || []);
          return {
            found:true,
            headTag: head.tagName,
            headClass: head.className,
            blockTag: node.tagName,
            blockClass: node.className,
            blockId: node.id,
            pricesInBlock: prices.slice(0,40),
            outer: node.outerHTML.slice(0, 1800)
          };
        }
        """
    )
    print("HEAD tag/class:", info.get("headTag"), "|", info.get("headClass"))
    print("BLOCK tag/class/id:", info.get("blockTag"), "|", info.get("blockClass"), "|", info.get("blockId"))
    print("prices in block:", info.get("pricesInBlock"))
    print("=== outerHTML (trimmed) ===")
    print(info.get("outer"))
    browser.close()
