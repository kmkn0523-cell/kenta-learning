// ────────── 復元キー(Recovery Key)関連のテスト ──────────
// 複数端末同期の土台。RKの生成・パース・accountId/DEK導出・wrap/unwrap を確認する
// 設計書: docs/finance_web_sync_design_v2.md
import { describe, it, expect } from "vitest";
import {
  generateRecoveryKey,
  parseRecoveryKey,
  deriveAccountId,
  deriveDataKey,
  wrapRecoveryKey,
  unwrapRecoveryKey,
  encryptValue,
  decryptValue,
} from "./crypto";

describe("generateRecoveryKey / parseRecoveryKey", () => {
  it("表示形式は4文字ごとにハイフン区切り（A-Z2-7のみ）", () => {
    const { display } = generateRecoveryKey();
    // 例: "ABCD-EFGH-...". ハイフンを除くと32文字のbase32
    const groups = display.split("-");
    groups.forEach(g => expect(g).toMatch(/^[A-Z2-7]{1,4}$/));
    expect(display.replace(/-/g, "").length).toBe(32);
  });

  it("生成→表示→パースで元のバイト列に戻る（往復一致）", () => {
    const { raw, display } = generateRecoveryKey();
    const parsed = parseRecoveryKey(display)!;
    expect(Array.from(parsed)).toEqual(Array.from(raw));
  });

  it("小文字・空白混じりでもパースできる（入力の揺れを吸収）", () => {
    const { raw, display } = generateRecoveryKey();
    const messy = display.toLowerCase().replace(/-/g, " ");
    const parsed = parseRecoveryKey(messy)!;
    expect(Array.from(parsed)).toEqual(Array.from(raw));
  });

  it("長さが合わない文字列は null", () => {
    expect(parseRecoveryKey("ABCD-EFGH")).toBeNull();
  });

  it("毎回異なるキーが生成される", () => {
    expect(generateRecoveryKey().display).not.toBe(generateRecoveryKey().display);
  });
});

describe("deriveAccountId（サーバ上の置き場所ID）", () => {
  it("同じRKなら必ず同じID（端末非依存）", async () => {
    const { raw } = generateRecoveryKey();
    const id1 = await deriveAccountId(raw);
    const id2 = await deriveAccountId(raw);
    expect(id1).toBe(id2);
  });

  it("違うRKなら違うID", async () => {
    const id1 = await deriveAccountId(generateRecoveryKey().raw);
    const id2 = await deriveAccountId(generateRecoveryKey().raw);
    expect(id1).not.toBe(id2);
  });

  it("URL安全な文字だけで構成される（+ / = を含まない）", async () => {
    const id = await deriveAccountId(generateRecoveryKey().raw);
    expect(id).toMatch(/^[A-Za-z0-9_-]+$/);
  });
});

describe("deriveDataKey（データ暗号鍵・端末非依存）", () => {
  it("同じRKから導出した鍵は別インスタンスでも相互に復号できる（＝別端末で復号可）", async () => {
    const { raw } = generateRecoveryKey();
    // 端末Aの鍵で暗号化
    const keyA = await deriveDataKey(raw);
    const encrypted = await encryptValue(keyA, { tx: [{ id: "1", amount: 1200 }] });
    // 端末Bが同じRKから鍵を作り直して復号
    const keyB = await deriveDataKey(raw);
    const decrypted = await decryptValue(keyB, encrypted);
    expect(decrypted).toEqual({ tx: [{ id: "1", amount: 1200 }] });
  });

  it("違うRKの鍵では復号できない", async () => {
    const keyA = await deriveDataKey(generateRecoveryKey().raw);
    const keyB = await deriveDataKey(generateRecoveryKey().raw);
    const encrypted = await encryptValue(keyA, { secret: 42 });
    await expect(decryptValue(keyB, encrypted)).rejects.toThrow();
  });
});

describe("wrapRecoveryKey / unwrapRecoveryKey（パスワードでローカル保護）", () => {
  it("正しいパスワードで往復一致", async () => {
    const { raw } = generateRecoveryKey();
    const wrapped = await wrapRecoveryKey(raw, "myPassword123");
    const unwrapped = await unwrapRecoveryKey(wrapped, "myPassword123");
    expect(Array.from(unwrapped!)).toEqual(Array.from(raw));
  });

  it("間違ったパスワードでは null（例外で落ちない）", async () => {
    const { raw } = generateRecoveryKey();
    const wrapped = await wrapRecoveryKey(raw, "correct");
    expect(await unwrapRecoveryKey(wrapped, "wrong")).toBeNull();
  });

  it("壊れた文字列・別形式は null", async () => {
    expect(await unwrapRecoveryKey("おかしな文字列", "x")).toBeNull();
    expect(await unwrapRecoveryKey("enc:aaa:bbb", "x")).toBeNull();
  });

  it("保存形式は rkw:v1: で始まる", async () => {
    const wrapped = await wrapRecoveryKey(generateRecoveryKey().raw, "pw");
    expect(wrapped.startsWith("rkw:v1:")).toBe(true);
  });
});
