// ────────── 暗号化ユーティリティ ──────────
// パスワードのハッシュ化（PBKDF2）とデータ暗号化（AES-GCM）に関する関数をまとめたファイル

// PBKDF2 のイテレーション回数（何回まぜまぜするか）。多いほど安全で少し遅い
const PBKDF2_ITERATIONS = 100000;

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
export function bytesToB64(bytes: Uint8Array): string {
  let s = "";
  for (let i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i]);
  return btoa(s);
}

// base64（文字列）をバイト列（数値の列）に戻す
export function b64ToBytes(b64: string): Uint8Array<ArrayBuffer> {
  const s = atob(b64);
  const bytes = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) bytes[i] = s.charCodeAt(i);
  return bytes;
}

// パスワードとsalt（毎回違うランダムな値）からPBKDF2で256ビットのハッシュを作る
export async function derivePwHash(password: string, saltBytes: Uint8Array<ArrayBuffer>): Promise<Uint8Array<ArrayBuffer>> {
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
    { name: "PBKDF2", salt: saltBytes, iterations: PBKDF2_ITERATIONS, hash: "SHA-256" },
    baseKey,
    256
  );
  return new Uint8Array(bits);
}

// 新形式の保存文字列を作る（"v2:saltのbase64:hashのbase64" という形）
export async function makeNewHash(password: string): Promise<string> {
  // 16バイトのランダムなsaltを毎回作る（同じパスワードでも保存値が毎回違う）
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const hash = await derivePwHash(password, salt);
  return `v2:${bytesToB64(salt)}:${bytesToB64(hash)}`;
}

// 新形式の保存文字列と入力パスワードを照合する
export async function verifyNewHash(password: string, stored: string): Promise<boolean> {
  const parts = stored.split(":");
  if (parts.length !== 3 || parts[0] !== "v2") return false;
  let salt, expected;
  try {
    salt = b64ToBytes(parts[1]);
    expected = b64ToBytes(parts[2]);
  } catch (_) {
    return false;
  }
  const actual = await derivePwHash(password, salt);
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
    { name: "PBKDF2", salt: encSaltBytes, iterations: PBKDF2_ITERATIONS, hash: "SHA-256" },
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

// 重複しないユニークなIDを作る（crypto.randomUUID() または予備の方法）
export function newId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  // 予備：時刻（ミリ秒）+ ランダム文字。同じミリ秒内に複数件追加されてもIDが被らないようにする
  return Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 10);
}
