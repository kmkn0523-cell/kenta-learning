/**
 * note.com に記事の下書きを自動作成するスクリプト
 * GitHub Actions から実行される（headless Chromium 使用）
 *
 * 使い方: node skin/create_note_draft.js
 * 環境変数: NOTE_EMAIL, NOTE_PASSWORD
 */

const { chromium } = require('@playwright/test');
const fs   = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// 今回の push で追加・変更された記事ファイルを探す
function findNewArticle() {
  try {
    const diff = execSync('git diff --name-only HEAD~1 HEAD 2>/dev/null')
      .toString().trim().split('\n')
      .filter(f => /^skin\/note_article_.+\.md$/.test(f));
    if (diff.length > 0) return diff[0];
  } catch (e) { /* git diff が使えない場合は fallback へ */ }

  // fallback: skin/ 内で最も新しい記事ファイルを返す
  const skinDir = path.join(process.cwd(), 'skin');
  const files = fs.readdirSync(skinDir)
    .filter(f => /^note_article_.+\.md$/.test(f))
    .sort((a, b) =>
      fs.statSync(path.join(skinDir, b)).mtimeMs -
      fs.statSync(path.join(skinDir, a)).mtimeMs
    );
  return files.length > 0 ? `skin/${files[0]}` : null;
}

// Markdown ファイルを読んでタイトルと本文（記号なし）を取得する
function parseArticle(filePath) {
  const raw   = fs.readFileSync(filePath, 'utf-8');
  const lines = raw.split('\n');

  // # タイトル 行を探す
  const titleIdx = lines.findIndex(l => l.startsWith('# ') && !l.startsWith('## '));
  const title    = titleIdx >= 0 ? lines[titleIdx].replace(/^# /, '') : '無題';

  // タイトル行以降を本文とし、Markdown 記号を除去する
  const body = lines
    .slice(titleIdx + 1)
    .join('\n')
    .trim()
    .replace(/^## /gm, '')           // ## 見出し記号を除去
    .replace(/\*\*(.*?)\*\*/g, '$1') // **太字** 記号を除去
    .replace(/^\*(.*?)\*$/gm, '$1'); // *イタリック* 記号を除去

  return { title, body };
}

async function run() {
  // ===== 記事ファイルを特定 =====
  const articlePath = findNewArticle();
  if (!articlePath) {
    console.log('新しい記事ファイルが見つかりませんでした。スキップします。');
    process.exit(0);
  }
  console.log(`処理する記事: ${articlePath}`);

  const { title, body } = parseArticle(articlePath);
  console.log(`タイトル: ${title}`);

  // ===== ブラウザを起動 =====
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
  });
  const context = await browser.newContext({
    permissions: ['clipboard-read', 'clipboard-write'],
  });
  const page = await context.newPage();

  try {
    // ===== note.com にログイン =====
    console.log('note.com にログイン中...');
    await page.goto('https://note.com/login');
    await page.waitForLoadState('networkidle');

    // メールアドレスとパスワードを入力
    await page.locator('input[type="email"], input[name="email"]').first().fill(process.env.NOTE_EMAIL);
    await page.locator('input[type="password"]').first().fill(process.env.NOTE_PASSWORD);
    await page.locator('button[type="submit"]').click();

    // ログイン完了（/login 以外のページに遷移するまで待つ）
    await page.waitForURL(/^https:\/\/note\.com(?!\/login)/, { timeout: 20000 });
    console.log('ログイン完了');

    // ===== 新規記事エディタを開く =====
    await page.goto('https://note.com/notes/new');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000); // エディタの JavaScript 初期化を待つ

    // ===== タイトルを入力 =====
    const titleBox = page.getByRole('textbox', { name: '記事タイトル' });
    await titleBox.click();
    await titleBox.fill(title);
    console.log('タイトル入力完了');

    // ===== 本文をクリップボード経由でペースト =====
    // クリップボードに本文をセット
    await page.evaluate(t => navigator.clipboard.writeText(t), body);

    // Tab キーで本文エリアにフォーカスを移す（タイトル → 本文）
    await page.keyboard.press('Tab');
    await page.waitForTimeout(500);

    // Ctrl+V でペースト
    await page.keyboard.press('Control+v');
    await page.waitForTimeout(2000);
    console.log('本文入力完了');

    // ===== 下書き保存 =====
    await page.getByRole('button', { name: /下書き保存|一時保存/ }).first().click();
    await page.waitForTimeout(2000);

    console.log(`✅ 下書き保存完了！`);
    console.log(`   URL: ${page.url()}`);

  } finally {
    await browser.close();
  }
}

run().catch(err => {
  console.error('❌ エラーが発生しました:', err.message);
  process.exit(1);
});
