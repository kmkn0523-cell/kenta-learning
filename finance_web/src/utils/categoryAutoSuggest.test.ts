// ────────── categoryAutoSuggest のテスト ──────────
import { describe, it, expect } from "vitest";
import { suggestCategory } from "./categoryAutoSuggest";

// テスト用の過去取引データ（memo と category だけ持つ）
const pastTx = [
  { memo: "スタバ", category: "カフェ" },
  { memo: "スタバ コーヒー", category: "カフェ" },
  { memo: "スタバ ランチ", category: "食費" },
  { memo: "セブンイレブン", category: "食費" },
  { memo: "セブン コーヒー", category: "カフェ" },
  { memo: "ガソリン", category: "交通費" },
  { memo: "", category: "その他" },
];

describe("suggestCategory", () => {
  it("最頻カテゴリを返す", () => {
    // "スタバ" は カフェ2件・食費1件 → カフェ
    expect(suggestCategory("スタバ", pastTx)).toBe("カフェ");
  });

  it("部分一致でも機能する", () => {
    // "セブン" はセブンイレブン（食費）・セブンコーヒー（カフェ）各1件 → どちらか（先頭を返す）
    const result = suggestCategory("セブン", pastTx);
    expect(result).not.toBeNull();
  });

  it("1文字では候補を返さない", () => {
    expect(suggestCategory("ス", pastTx)).toBeNull();
  });

  it("空文字では候補を返さない", () => {
    expect(suggestCategory("", pastTx)).toBeNull();
  });

  it("スペースのみでは候補を返さない", () => {
    expect(suggestCategory("   ", pastTx)).toBeNull();
  });

  it("一致する過去取引がなければ null", () => {
    expect(suggestCategory("ラーメン", pastTx)).toBeNull();
  });

  it("大文字小文字を無視してマッチする", () => {
    const tx = [{ memo: "Amazon Prime", category: "サブスク" }];
    expect(suggestCategory("amazon", tx)).toBe("サブスク");
  });

  it("過去取引が空なら null", () => {
    expect(suggestCategory("スタバ", [])).toBeNull();
  });
});
