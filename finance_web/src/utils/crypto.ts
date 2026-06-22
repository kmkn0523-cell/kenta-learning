// ────────── 暗号化ユーティリティ ──────────
// パスワードのハッシュ化（PBKDF2）とデータ暗号化（AES-GCM）に関する関数をまとめたファイル

// パスワードハッシュ用のイテレーション回数（OWASP 2026推奨: SHA-256で31万回）
const PBKDF2_HASH_ITERATIONS = 310_000;
// 暗号化鍵の導出用イテレーション回数（既存データとの互換性維持のため変更しない）
const PBKDF2_ENC_ITERATIONS  = 100_000;

// 暗号化鍵を作るためのsaltを保存するlocalStorageキー
export const ENC_SALT_KEY = "kk_enc_salt";

// 旧版の簡易ハッシュ（互換性チェック専用。新規には使わない）
export function simpleHash(str: string): string {
  let h = 0;
  for (let i = 0; i < str.length; i++) {
    h = (Math.imul(31, h) + str.charCodeAt(i)) | 0;
  }
  return (h >>> 0).toString(16).slice(0, 8);
}

// バイト列（数値の列）を base64（文字列）に変える
function bytesToB64(bytes: Uint8Array): string {
  let s = "";
  for (let i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i]);
  return btoa(s);
}

// base64（文字列）をバイト列（数値の列）に戻す
function b64ToBytes(b64: string): Uint8Array<ArrayBuffer> {
  const s = atob(b64);
  const bytes = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) bytes[i] = s.charCodeAt(i);
  return bytes;
}

// パスワードとsalt（毎回違うランダムな値）からPBKDF2で256ビットのハッシュを作る
// iterations: 何回混ぜるか（多いほど強い。v2=10万、v3=31万）
async function derivePwHash(password: string, saltBytes: Uint8Array<ArrayBuffer>, iterations: number): Promise<Uint8Array<ArrayBuffer>> {
  const enc = new TextEncoder();
  // パスワード文字列をWeb Cryptoが扱える形（CryptoKey）に変換する
  const baseKey = await crypto.subtle.importKey(
    "raw",
    enc.encode(password),
    { name: "PBKDF2" },
    false,
    ["deriveBits"]
  );
  // PBKDF2でビット列を導出する
  const bits = await crypto.subtle.deriveBits(
    { name: "PBKDF2", salt: saltBytes, iterations, hash: "SHA-256" },
    baseKey,
    256
  );
  return new Uint8Array(bits);
}

// 新形式の保存文字列を作る（"v3:イテレーション数:saltのbase64:hashのbase64" という形）
// v2（旧）は 100k 固定だったが、v3 からはイテレーション数を文字列に埋め込む
export async function makeNewHash(password: string): Promise<string> {
  // 16バイトのランダムなsaltを毎回作る（同じパスワードでも保存値が毎回違う）
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const hash = await derivePwHash(password, salt, PBKDF2_HASH_ITERATIONS);
  return `v3:${PBKDF2_HASH_ITERATIONS}:${bytesToB64(salt)}:${bytesToB64(hash)}`;
}

// 新形式の保存文字列と入力パスワードを照合する
// v2形式: "v2:saltB64:hashB64"（イテレーション100k固定）
// v3形式: "v3:イテレーション数:saltB64:hashB64"（イテレーション数を文字列から読む）
export async function verifyNewHash(password: string, stored: string): Promise<boolean> {
  const parts = stored.split(":");
  let iterations: number;
  let saltB64: string;
  let hashB64: string;

  if (parts[0] === "v2" && parts.length === 3) {
    // 旧v2形式: 100k固定
    iterations = PBKDF2_ENC_ITERATIONS;
    saltB64 = parts[1];
    hashB64 = parts[2];
  } else if (parts[0] === "v3" && parts.length === 4) {
    // 新v3形式: イテレーション数を読み取る
    iterations = Number(parts[1]);
    if (!Number.isInteger(iterations) || iterations < 1_000) return false;
    saltB64 = parts[2];
    hashB64 = parts[3];
  } else {
    return false;
  }

  let salt, expected;
  try {
    salt = b64ToBytes(saltB64);
    expected = b64ToBytes(hashB64);
  } catch (_) {
    return false;
  }
  const actual = await derivePwHash(password, salt, iterations);
  if (actual.length !== expected.length) return false;
  // タイミング攻撃を防ぐため、長さが同じなら必ず全バイト比較する（定数時間比較）
  let diff = 0;
  for (let i = 0; i < actual.length; i++) diff |= actual[i] ^ expected[i];
  return diff === 0;
}

// 保存値が旧形式（simpleHashの8桁hex）かを判定する
export function isLegacyHash(stored: string): boolean {
  return /^[0-9a-f]{8}$/.test(stored);
}

// 暗号化用saltを取得する（無ければ新しく作って保存）
export function getOrCreateEncSalt(): Uint8Array<ArrayBuffer> {
  try {
    const saved = localStorage.getItem(ENC_SALT_KEY);
    if (saved) return b64ToBytes(saved);
  } catch (error) { console.warn("[crypto] getOrCreateEncSalt read failed", error); }
  // 16バイトのランダムなsaltを新規作成
  const fresh = crypto.getRandomValues(new Uint8Array(16));
  try { localStorage.setItem(ENC_SALT_KEY, bytesToB64(fresh)); } catch (error) { console.warn("[crypto] getOrCreateEncSalt write failed", error); }
  return fresh;
}

// パスワードと暗号化用saltから AES-GCM 256bit の鍵（CryptoKey）を派生
export async function deriveEncryptionKey(password: string, encSaltBytes: Uint8Array<ArrayBuffer>): Promise<CryptoKey> {
  const enc = new TextEncoder();
  const baseKey = await crypto.subtle.importKey(
    "raw",
    enc.encode(password),
    { name: "PBKDF2" },
    false,
    ["deriveKey"]
  );
  return crypto.subtle.deriveKey(
    { name: "PBKDF2", salt: encSaltBytes, iterations: PBKDF2_ENC_ITERATIONS, hash: "SHA-256" },
    baseKey,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt", "decrypt"]
  );
}

// 任意の値（JSONにできるもの）をAES-GCMで暗号化して文字列にする
// 形式: "enc:<ivのbase64>:<暗号文のbase64>"
export async function encryptValue(cryptoKey: CryptoKey, value: unknown): Promise<string> {
  // IV（初期化ベクトル）は毎回12バイトのランダム値（同じデータでも保存値が毎回違う）
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const enc = new TextEncoder();
  const plaintext = enc.encode(JSON.stringify(value));
  const ct = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv },
    cryptoKey,
    plaintext
  );
  return `enc:${bytesToB64(iv)}:${bytesToB64(new Uint8Array(ct))}`;
}

// 暗号化された文字列を復号して元の値を返す
export async function decryptValue(cryptoKey: CryptoKey, stored: string): Promise<unknown> {
  const parts = stored.split(":");
  if (parts.length !== 3 || parts[0] !== "enc") throw new Error("invalid encrypted format");
  const iv = b64ToBytes(parts[1]);
  const ct = b64ToBytes(parts[2]);
  const plaintext = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv },
    cryptoKey,
    ct
  );
  return JSON.parse(new TextDecoder().decode(plaintext));
}

// 保存値が暗号化済みかどうかを判定する
export function isEncrypted(stored: unknown): boolean {
  return typeof stored === "string" && stored.startsWith("enc:");
}

// ════════════════════════════════════════════════════════════
// 複数端末同期：復元キー(Recovery Key) 関連
// 設計書: docs/finance_web_sync_design_v2.md
// パスワード＝端末ローカルの鍵／復元キー(RK)＝同期・復号・課金のルート
// RK から「サーバの置き場所ID(accountId)」と「データ暗号鍵(DEK)」を決定的に導出する
// ════════════════════════════════════════════════════════════

// 復元キーの長さ（20バイト＝160ビット。総当たり不可・base32でちょうど32文字になり書き写しやすい）
const RECOVERY_KEY_BYTES = 20;

// base32（RFC4648）の文字テーブル。0/1/8/Oなどの紛らわしさを避けるためA-Z2-7のみ
const BASE32_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";

// バイト列を base32 文字列にする（パディングなし）
function bytesToBase32(bytes: Uint8Array): string {
  let bits = 0;       // 今ためているビット
  let value = 0;      // ビットをためる入れ物
  let output = "";
  for (let i = 0; i < bytes.length; i++) {
    value = (value << 8) | bytes[i];
    bits += 8;
    // 5ビットたまるごとに1文字に変換する
    while (bits >= 5) {
      output += BASE32_ALPHABET[(value >>> (bits - 5)) & 31];
      bits -= 5;
    }
  }
  // 余ったビットがあれば最後の1文字を出す
  if (bits > 0) output += BASE32_ALPHABET[(value << (5 - bits)) & 31];
  return output;
}

// base32 文字列をバイト列に戻す（区切りのハイフン・空白・小文字は許容して正規化）
function base32ToBytes(str: string): Uint8Array {
  // ハイフンや空白を取り除き、大文字化する
  const clean = str.toUpperCase().replace(/[^A-Z2-7]/g, "");
  let bits = 0;
  let value = 0;
  const out: number[] = [];
  for (let i = 0; i < clean.length; i++) {
    const idx = BASE32_ALPHABET.indexOf(clean[i]);
    if (idx === -1) continue; // 不正文字は無視
    value = (value << 5) | idx;
    bits += 5;
    // 8ビットたまるごとに1バイト取り出す
    if (bits >= 8) {
      out.push((value >>> (bits - 8)) & 0xff);
      bits -= 8;
    }
  }
  return new Uint8Array(out);
}

// base64 を URL安全な形に変える（+→- /→_ 末尾の=を削除）
function b64ToB64Url(b64: string): string {
  return b64.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

// 復元キーを新規生成する。raw=バイト列・display=ユーザーに見せる "XXXX-XXXX-..." 形式
export function generateRecoveryKey(): { raw: Uint8Array; display: string } {
  const raw = crypto.getRandomValues(new Uint8Array(RECOVERY_KEY_BYTES));
  const base32 = bytesToBase32(raw);
  // 4文字ごとにハイフンで区切って読みやすくする
  const display = (base32.match(/.{1,4}/g) || []).join("-");
  return { raw, display };
}

// ユーザーが入力した復元キー文字列をバイト列に戻す（長さが合わなければ null）
export function parseRecoveryKey(display: string): Uint8Array | null {
  const bytes = base32ToBytes(display);
  if (bytes.length !== RECOVERY_KEY_BYTES) return null;
  return bytes;
}

// HKDF で RK から用途別のビット列を導出する内部ヘルパー
// info（用途ラベル）を変えると別々の鍵になる＝1つのRKから複数の鍵を安全に作れる
async function hkdfBits(rk: Uint8Array, info: string, lengthBits: number): Promise<Uint8Array> {
  const baseKey = await crypto.subtle.importKey("raw", rk as BufferSource, "HKDF", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits(
    { name: "HKDF", hash: "SHA-256", salt: new Uint8Array(0), info: new TextEncoder().encode(info) },
    baseKey,
    lengthBits
  );
  return new Uint8Array(bits);
}

// RK から accountId（サーバ上のデータの置き場所ID）を導出する
// 256ビット乱数由来＝推測不可。同じRKなら必ず同じIDになる（端末非依存）
export async function deriveAccountId(rk: Uint8Array): Promise<string> {
  const bits = await hkdfBits(rk, "byb-account-id", 256);
  return b64ToB64Url(bytesToB64(bits));
}

// RK からデータ暗号鍵(DEK)を導出する。AES-GCM 256bit・端末非依存
// → どの端末でも同じRKから同じ鍵が出るので、サーバの暗号文を別端末で復号できる
export async function deriveDataKey(rk: Uint8Array): Promise<CryptoKey> {
  const keyBits = await hkdfBits(rk, "byb-data-enc", 256);
  return crypto.subtle.importKey("raw", keyBits as BufferSource, { name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"]);
}

// RK をパスワード派生鍵で包んで(wrap)ローカル保存用の文字列にする
// 形式: "rkw:v1:イテレーション数:saltB64:ivB64:暗号文B64"
export async function wrapRecoveryKey(rk: Uint8Array, password: string): Promise<string> {
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const enc = new TextEncoder();
  const baseKey = await crypto.subtle.importKey("raw", enc.encode(password), { name: "PBKDF2" }, false, ["deriveKey"]);
  const wrapKey = await crypto.subtle.deriveKey(
    { name: "PBKDF2", salt, iterations: PBKDF2_ENC_ITERATIONS, hash: "SHA-256" },
    baseKey,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt"]
  );
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ct = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, wrapKey, rk as BufferSource);
  return `rkw:v1:${PBKDF2_ENC_ITERATIONS}:${bytesToB64(salt)}:${bytesToB64(iv)}:${bytesToB64(new Uint8Array(ct))}`;
}

// 包まれたRK文字列とパスワードから元のRKバイト列を取り戻す
// パスワードが違う・形式が壊れている場合は null を返す（例外で落とさない）
export async function unwrapRecoveryKey(wrapped: string, password: string): Promise<Uint8Array | null> {
  const parts = wrapped.split(":");
  if (parts[0] !== "rkw" || parts[1] !== "v1" || parts.length !== 6) return null;
  const iterations = Number(parts[2]);
  if (!Number.isInteger(iterations) || iterations < 1_000) return null;
  try {
    const salt = b64ToBytes(parts[3]);
    const iv = b64ToBytes(parts[4]);
    const ct = b64ToBytes(parts[5]);
    const enc = new TextEncoder();
    const baseKey = await crypto.subtle.importKey("raw", enc.encode(password), { name: "PBKDF2" }, false, ["deriveKey"]);
    const wrapKey = await crypto.subtle.deriveKey(
      { name: "PBKDF2", salt, iterations, hash: "SHA-256" },
      baseKey,
      { name: "AES-GCM", length: 256 },
      false,
      ["decrypt"]
    );
    const rk = await crypto.subtle.decrypt({ name: "AES-GCM", iv }, wrapKey, ct as BufferSource);
    return new Uint8Array(rk);
  } catch (_) {
    // パスワード違いなどは復号失敗で例外→null扱い
    return null;
  }
}

// 重複しないユニークなIDを作る（crypto.randomUUID() または予備の方法）
export function newId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  // 予備：時刻（ミリ秒）+ ランダム文字。同じミリ秒内に複数件追加されてもIDが被らないようにする
  return Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 10);
}
