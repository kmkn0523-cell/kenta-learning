/**
 * note.com のセッションクッキーを保存するスクリプト（一度だけ手動実行）
 *
 * 使い方（ローカルのWindows環境で実行）:
 *   node skin/save_note_session.js
 *
 * 開いたブラウザで手動でnote.comにログインすると、
 * クッキーがコンソールに表示されます。
 * それをGitHub Secretsの NOTE_COOKIES に貼り付けてください。
 */

const { chromium } = require('@playwright/test');

async function run() {
  console.log('ブラウザを起動します...');
  console.log('note.comにログインしてください（reCAPTCHAも手動で対応）\n');

  // headless: false → 実際のブラウザウィンドウを開く
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page    = await context.newPage();

  await page.goto('https://note.com/login');

  // ログイン完了まで最大2分待つ
  console.log('ログインが完了したら、このスクリプトが自動的にクッキーを保存します...');
  await page.waitForURL(/^https:\/\/note\.com(?!\/login)/, { timeout: 120000 });

  // クッキーを取得してJSON文字列にする
  const cookies = await context.cookies();
  const cookieJson = JSON.stringify(cookies);
  const cookieBase64 = Buffer.from(cookieJson).toString('base64');

  console.log('\n===== GitHub Secretsに以下をコピーしてください =====');
  console.log('Secret名: NOTE_COOKIES');
  console.log('値（以下の1行をすべてコピー）:');
  console.log(cookieBase64);
  console.log('===================================================\n');

  await browser.close();
  console.log('完了！');
}

run().catch(err => {
  console.error('エラー:', err.message);
  process.exit(1);
});
