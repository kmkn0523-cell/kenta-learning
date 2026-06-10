// ────────── アフィリエイトバナー ──────────
// 広告1枚のカードUIと、ローンタブ用のセクションをまとめたファイル
// 広告データ本体は utils/affiliates.ts が持つ。ここは「表示」だけを担当する

import { CSSProperties } from "react";
import { AffiliateOffer, OFFERS_BY_LOAN_TAB, getOfferById } from "../utils/affiliates";
import { COLOR_TEXT_HINT, COLOR_TEXT_SECONDARY, COLOR_TEXT_PRIMARY, COLOR_ACCENT } from "../utils/styles";

// ── スタイル定数 ──────────────────────────────────────────

// バナーのカード外枠
const STYLE_AFFIL_CARD: CSSProperties = {
  background: "rgba(15,23,42,0.85)",
  border: "1px solid rgba(34,211,238,0.2)",
  borderRadius: 14,
  padding: "14px 16px",
  marginBottom: 10,
  display: "flex",
  alignItems: "center",
  gap: 12,
  cursor: "pointer",
  transition: "border-color 0.15s",
};

// CTAボタン（右端の申し込みボタン風テキスト）
const STYLE_AFFIL_CTA: CSSProperties = {
  flexShrink: 0,
  background: COLOR_ACCENT,
  color: "#070b14",
  borderRadius: 10,
  padding: "8px 12px",
  fontSize: 12,
  fontWeight: 700,
  whiteSpace: "nowrap",
};

// ─────────────────────────────────────────────────────────

// 広告バナー1枚を描画するコンポーネント
export default function AffiliateBanner({ offer }: { offer: AffiliateOffer }) {
  return (
    <a
      href={offer.href}
      target="_blank"
      rel="noopener noreferrer sponsored"
      style={{ textDecoration: "none", display: "block" }}
    >
      <div style={STYLE_AFFIL_CARD}>
        {/* 左：テキスト情報 */}
        <div style={{ flex: 1, minWidth: 0 }}>
          {/* 広告タグ + ジャンルラベル */}
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
            <span style={{ fontSize: 12, background: "rgba(34,211,238,0.15)", color: COLOR_ACCENT, borderRadius: 4, padding: "1px 6px", letterSpacing: "0.5px" }}>PR</span>
            <span style={{ fontSize: 12, color: COLOR_TEXT_HINT }}>{offer.tag}</span>
          </div>
          {/* サービス名 */}
          <div style={{ fontSize: 13, fontWeight: 700, color: COLOR_TEXT_PRIMARY, marginBottom: 2, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{offer.title}</div>
          {/* 説明文 */}
          <div style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY }}>{offer.desc}</div>
        </div>
        {/* 右：CTAボタン */}
        <div style={STYLE_AFFIL_CTA}>{offer.cta}</div>
      </div>
    </a>
  );
}

// ローンタブ（cf/bl/lo）内のアフィリエイトセクション全体
// 承認済みの広告だけが OFFERS_BY_LOAN_TAB に載っているので、ここでは並べるだけ
export function AffiliateSection({ tab }: { tab: "cf" | "bl" | "lo" }) {
  // タブに対応する広告ID一覧を実データに変換する（存在しないIDは無視）
  const offers = OFFERS_BY_LOAN_TAB[tab]
    .map(getOfferById)
    .filter((offer): offer is AffiliateOffer => offer !== undefined);

  // 表示できる広告が1件もなければセクションごと出さない
  if (offers.length === 0) return null;

  return (
    <div style={{ marginTop: 16, marginBottom: 4 }}>
      {/* 区切りラベル */}
      <div style={{ fontSize: 12, color: COLOR_TEXT_HINT, textTransform: "uppercase", letterSpacing: "2px", marginBottom: 10 }}>
        💳 おすすめ金融サービス
      </div>
      {offers.map(offer => (
        <AffiliateBanner key={offer.id} offer={offer} />
      ))}
    </div>
  );
}
