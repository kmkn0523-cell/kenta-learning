// ────────── affiliates.ts（広告データ・選定ロジック）のテスト ──────────
import {
  APPROVED_OFFERS,
  OFFERS_BY_LOAN_TAB,
  getOfferById,
  selectAffiliateOffer,
} from "../../utils/affiliates";

describe("APPROVED_OFFERS（承認済み広告データ）", () => {
  it("承認済みは4件だけ（審査待ちプレースホルダーを含まない）", () => {
    expect(APPROVED_OFFERS).toHaveLength(4);
  });

  it("全件が実際のA8リンク（px.a8.netドメイン）でPLACEHOLDERを含まない", () => {
    for (const offer of APPROVED_OFFERS) {
      expect(offer.href).toContain("px.a8.net");
      expect(offer.href).not.toContain("PLACEHOLDER");
    }
  });
});

describe("getOfferById", () => {
  it("存在するIDならオファーを返す", () => {
    expect(getOfferById("dmm_stock")?.title).toBe("DMM 株");
  });

  it("存在しないIDなら undefined を返す", () => {
    expect(getOfferById("unknown_id")).toBeUndefined();
  });
});

describe("OFFERS_BY_LOAN_TAB（ローンタブ別の表示リスト）", () => {
  it("全タブのIDが承認済みオファーに解決できる", () => {
    for (const ids of Object.values(OFFERS_BY_LOAN_TAB)) {
      for (const id of ids) {
        expect(getOfferById(id)).toBeDefined();
      }
    }
  });
});

describe("selectAffiliateOffer（診断連動の選定ロジック）", () => {
  it("2月は確定申告オファー（マネーフォワード）を返す", () => {
    const offer = selectAffiliateOffer({ savingRate: 0, hasAccounts: false, month: 2 });
    expect(offer?.id).toBe("moneyforward");
  });

  it("3月も確定申告オファーを返す（投資条件を満たしていても申告期を優先）", () => {
    const offer = selectAffiliateOffer({ savingRate: 50, hasAccounts: true, month: 3 });
    expect(offer?.id).toBe("moneyforward");
  });

  it("貯蓄率20%以上かつ口座ありなら投資オファー（DMM株）を返す", () => {
    const offer = selectAffiliateOffer({ savingRate: 20, hasAccounts: true, month: 6 });
    expect(offer?.id).toBe("dmm_stock");
  });

  it("貯蓄率20%未満なら null（無理に出さない）", () => {
    expect(selectAffiliateOffer({ savingRate: 19.9, hasAccounts: true, month: 6 })).toBeNull();
  });

  it("口座未登録なら投資オファーは出さず null", () => {
    expect(selectAffiliateOffer({ savingRate: 30, hasAccounts: false, month: 6 })).toBeNull();
  });
});
