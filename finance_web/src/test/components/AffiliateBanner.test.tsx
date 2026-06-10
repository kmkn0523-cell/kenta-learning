// ────────── AffiliateBanner コンポーネントのテスト ──────────
import { render, screen } from "@testing-library/react";
import AffiliateBanner, { AffiliateSection } from "../../components/AffiliateBanner";
import { APPROVED_OFFERS } from "../../utils/affiliates";

describe("AffiliateBanner（広告バナー1枚）", () => {
  const offer = APPROVED_OFFERS[0];

  it("PRラベル・タイトル・説明文が表示される", () => {
    render(<AffiliateBanner offer={offer} />);
    expect(screen.getByText("PR")).toBeInTheDocument();
    expect(screen.getByText(offer.title)).toBeInTheDocument();
    expect(screen.getByText(offer.desc)).toBeInTheDocument();
  });

  it("リンクに rel=sponsored と正しいURLが付いている", () => {
    render(<AffiliateBanner offer={offer} />);
    const link = screen.getByRole("link");
    expect(link.getAttribute("rel")).toContain("sponsored");
    expect(link).toHaveAttribute("href", offer.href);
    expect(link).toHaveAttribute("target", "_blank");
  });
});

describe("AffiliateSection（ローンタブ用のまとまり）", () => {
  it("blタブでは承認済みの投資系2件（DMM株・TOSSY）が表示される", () => {
    render(<AffiliateSection tab="bl" />);
    expect(screen.getByText("DMM 株")).toBeInTheDocument();
    expect(screen.getByText("TOSSY（DMM証券）")).toBeInTheDocument();
  });

  it("cfタブでは審査待ちのプロミスVISAは表示されない", () => {
    render(<AffiliateSection tab="cf" />);
    expect(screen.queryByText("プロミスVISAカード")).not.toBeInTheDocument();
    expect(screen.getByText("マネーフォワード クラウド確定申告")).toBeInTheDocument();
  });
});
