// ────────── アフィリエイト広告の一元管理 ──────────
// 広告リンク・表示文言・「どの文脈で出すか」をこのファイルにまとめる
// 審査が通ったら APPROVED_OFFERS に1件追加するだけで画面に反映される

// 広告1件の形
export interface AffiliateOffer {
  id: string;       // プログラム識別子（例: "dmm_stock"）
  tag: string;      // 小さく出すジャンルラベル（例: "日本株・米国株・NISA"）
  title: string;    // サービス名
  desc: string;     // 短い説明文
  cta: string;      // ボタンのテキスト
  href: string;     // アフィリエイトリンクURL
  context: "invest" | "tax" | "loan"; // どの文脈で出してよいか
}

// ── 承認済み広告（2026/05/17 A8.net広告リンクから取得）──
export const APPROVED_OFFERS: AffiliateOffer[] = [
  {
    id: "fujitomi_fx",
    tag: "FX自動売買",
    title: "シストレセレクト365（フジトミ証券）",
    desc: "ローン返済と並行して資産を増やしたい方に。FX自動売買で24時間稼働",
    cta: "詳しく見る →",
    href: "https://px.a8.net/svt/ejp?a8mat=4B3SMZ+EPVT6A+34QW+BWVTE",
    context: "invest",
  },
  {
    id: "dmm_tossy",
    tag: "株・FX・先物をアプリひとつで",
    title: "TOSSY（DMM証券）",
    desc: "あらゆる取引がアプリひとつで完結。初心者でも使いやすいUI",
    cta: "口座開設（無料）→",
    href: "https://px.a8.net/svt/ejp?a8mat=4B3SMZ+EOOXYQ+1WP2+1HLNLE",
    context: "invest",
  },
  {
    id: "dmm_stock",
    tag: "日本株・米国株・NISA",
    title: "DMM 株",
    desc: "手数料業界最安水準。NISA口座対応・米国株も1株から購入可能",
    cta: "口座開設（無料）→",
    href: "https://px.a8.net/svt/ejp?a8mat=4B3SMZ+EO3ICY+1WP2+15QHIA",
    context: "invest",
  },
  {
    id: "moneyforward",
    tag: "確定申告・家計管理",
    title: "マネーフォワード クラウド確定申告",
    desc: "自動化で80%以上の時間削減。銀行・カード連携でラクラク申告",
    cta: "無料で試す →",
    href: "https://px.a8.net/svt/ejp?a8mat=4B3RV6+8OKLDE+4JGQ+BYT9E",
    context: "tax",
  },
];

// ── 審査待ち（A8.net審査通過後に上の配列へ移動する）──
// promise_visa: プロミスVISAカード（報酬10,000円）tag:"消費者金融 → カード借り換え" context:"loan"
// smbc_nl:      三井住友カード(NL)（報酬12,000円）tag:"年会費無料・高還元" context:"loan"
// epos:         エポスカード（報酬7,000円）tag:"年会費無料・優待豊富" context:"loan"
// recruit:      リクルートカード（報酬4,800円）tag:"高還元・Pontaポイント" context:"loan"
// tokyu:        TOKYU CARD ClubQ JMB（報酬4,135円）tag:"東急線ユーザー向け" context:"loan"

// IDからオファーを探す（見つからなければ undefined）
export function getOfferById(id: string): AffiliateOffer | undefined {
  return APPROVED_OFFERS.find(offer => offer.id === id);
}

// ローンタブ（cf=消費者金融 / bl=銀行・リボ / lo=住宅・車）ごとに出す広告のID一覧
export const OFFERS_BY_LOAN_TAB: Record<"cf" | "bl" | "lo", string[]> = {
  cf: ["moneyforward"],
  bl: ["dmm_stock", "dmm_tossy"],
  lo: ["fujitomi_fx", "moneyforward"],
};

// 診断連動の選定に使う入力値の形
export interface OfferSelectionContext {
  savingRate: number;   // 貯蓄率（%）
  hasAccounts: boolean; // 口座が1件以上登録されているか
  month: number;        // 今の月（1〜12）
}

// 家計の状態に合った広告を最大1件選ぶ（合うものがなければ null）
// ルールは上から順に判定して最初にマッチしたものだけ返す
export function selectAffiliateOffer(ctx: OfferSelectionContext): AffiliateOffer | null {
  // ① 確定申告期（2〜3月）→ 確定申告ツール
  if (ctx.month === 2 || ctx.month === 3) {
    return getOfferById("moneyforward") ?? null;
  }
  // ② 貯蓄率が理想水準（20%以上）で口座管理もしている → 余剰資金の投資提案
  if (ctx.savingRate >= 20 && ctx.hasAccounts) {
    return getOfferById("dmm_stock") ?? null;
  }
  // ③ 合う提案がなければ何も出さない（無理に出すと信頼を失う）
  return null;
}
