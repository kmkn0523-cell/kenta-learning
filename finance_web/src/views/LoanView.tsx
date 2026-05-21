// ────────── ローンタブ表示コンポーネント ──────────
// App.tsx のローンタブ部分を切り出したファイル
// 全ローン合計・アバランチ法アドバイス・種別ごとのローン一覧を表示する

import React from "react";
import { Loan } from "../types";
import { formatYen } from "../utils/format";
import { calculateMonthlyInterest, calculateTotalInterest, calculateCompletionDate, BRANDS_CF, BRANDS_BL } from "../utils/loanCalc";
import { COLOR_TEXT_HINT, COLOR_TEXT_SECONDARY, COLOR_TEXT_PRIMARY, COLOR_ACCENT, COLOR_POSITIVE, COLOR_NEGATIVE, COLOR_BORDER, STYLE_CARD } from "../utils/styles";
import { StatLabel } from "../components/ui";
import LoanSection from "../components/LoanSection";
import StatBlock from "../components/StatBlock";

// ────────── A8.netアフィリエイトリンク ──────────
// A8.net管理画面 → 提携中プログラム → 広告素材 → テキストリンク で取得したURL
const AFFILIATE = {
  // 審査待ち（通過後にURLを差し替える）
  promise_visa: "https://px.a8.net/svt/ejp?a8mat=PROMISE_VISA_PLACEHOLDER",       // プロミスVISAカード（報酬10,000円）
  smbc_nl:      "https://px.a8.net/svt/ejp?a8mat=SMBC_NL_PLACEHOLDER",            // 三井住友カード(NL)（報酬12,000円）
  epos:         "https://px.a8.net/svt/ejp?a8mat=EPOS_PLACEHOLDER",               // エポスカード（報酬7,000円）
  recruit:      "https://px.a8.net/svt/ejp?a8mat=RECRUIT_PLACEHOLDER",            // リクルートカード（報酬4,800円）
  tokyu:        "https://px.a8.net/svt/ejp?a8mat=TOKYU_PLACEHOLDER",              // TOKYU CARD（報酬4,135円）
  // 承認済み（2026/05/17 A8.net広告リンクから取得）
  fujitomi_fx:  "https://px.a8.net/svt/ejp?a8mat=4B3SMZ+EPVT6A+34QW+BWVTE",     // フジトミ証券 シストレセレクト365（報酬11,000円）
  dmm_tossy:    "https://px.a8.net/svt/ejp?a8mat=4B3SMZ+EOOXYQ+1WP2+1HLNLE",    // DMM証券 TOSSY（報酬15,000円）
  dmm_stock:    "https://px.a8.net/svt/ejp?a8mat=4B3SMZ+EO3ICY+1WP2+15QHIA",    // DMM株（報酬10,000円）
  moneyforward: "https://px.a8.net/svt/ejp?a8mat=4B3RV6+8OKLDE+4JGQ+BYT9E",     // マネーフォワード クラウド確定申告（報酬1,500円）
};

// アフィリエイトバナー1枚を描画するコンポーネント
function AffiliateBanner({ tag, title, desc, cta, href }: {
  tag: string;   // タグ（例: "年会費無料" "高還元"）
  title: string; // サービス名
  desc: string;  // 短い説明文
  cta: string;   // ボタンのテキスト
  href: string;  // アフィリエイトリンクURL
}) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer sponsored"
      style={{ textDecoration: "none", display: "block" }}
    >
      <div style={{
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
      }}>
        {/* 左：テキスト情報 */}
        <div style={{ flex: 1, minWidth: 0 }}>
          {/* 広告タグ + カテゴリラベル */}
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
            <span style={{ fontSize: 9, background: "rgba(34,211,238,0.15)", color: COLOR_ACCENT, borderRadius: 4, padding: "1px 6px", letterSpacing: "0.5px" }}>PR</span>
            <span style={{ fontSize: 10, color: COLOR_TEXT_HINT }}>{tag}</span>
          </div>
          {/* サービス名 */}
          <div style={{ fontSize: 13, fontWeight: 700, color: COLOR_TEXT_PRIMARY, marginBottom: 2, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{title}</div>
          {/* 説明文 */}
          <div style={{ fontSize: 11, color: COLOR_TEXT_SECONDARY }}>{desc}</div>
        </div>
        {/* 右：CTAボタン */}
        <div style={{
          flexShrink: 0,
          background: COLOR_ACCENT,
          color: "#070b14",
          borderRadius: 10,
          padding: "8px 12px",
          fontSize: 11,
          fontWeight: 700,
          whiteSpace: "nowrap",
        }}>{cta}</div>
      </div>
    </a>
  );
}

// タブ内のアフィリエイトセクション全体
function AffiliateSection({ tab }: { tab: "cf" | "bl" | "lo" }) {
  return (
    <div style={{ marginTop: 16, marginBottom: 4 }}>
      {/* 区切りラベル */}
      <div style={{ fontSize: 9, color: COLOR_TEXT_HINT, textTransform: "uppercase", letterSpacing: "2px", marginBottom: 10 }}>
        💳 おすすめ金融サービス
      </div>

      {/* 消費者金融タブ：カード切り替え提案 + 確定申告ツール */}
      {tab === "cf" && (
        <>
          <AffiliateBanner
            tag="消費者金融 → カード借り換え"
            title="プロミスVISAカード"
            desc="カードローン機能付きVISAカード。最短当日融資・年会費無料"
            cta="詳しく見る →"
            href={AFFILIATE.promise_visa}
          />
          <AffiliateBanner
            tag="確定申告・家計管理"
            title="マネーフォワード クラウド確定申告"
            desc="自動化で80%以上の時間削減。銀行・カード連携でラクラク申告"
            cta="無料で試す →"
            href={AFFILIATE.moneyforward}
          />
        </>
      )}

      {/* 銀行・リボ払いタブ：高還元カード + 株式投資サービス */}
      {tab === "bl" && (
        <>
          <AffiliateBanner
            tag="年会費無料・高還元"
            title="三井住友カード(NL)"
            desc="対象コンビニ・飲食店で最大7%還元。ナンバーレスでセキュリティ◎"
            cta="詳しく見る →"
            href={AFFILIATE.smbc_nl}
          />
          <AffiliateBanner
            tag="年会費無料・優待豊富"
            title="エポスカード"
            desc="マルイで10%OFF・国内外旅行保険付き・即日発行OK"
            cta="詳しく見る →"
            href={AFFILIATE.epos}
          />
          <AffiliateBanner
            tag="高還元・Pontaポイント"
            title="リクルートカード"
            desc="基本還元率1.2%・じゃらん/ホットペッパーでさらにお得"
            cta="詳しく見る →"
            href={AFFILIATE.recruit}
          />
          <AffiliateBanner
            tag="東急線ユーザー向け"
            title="TOKYU CARD ClubQ JMB"
            desc="東急線・東急百貨店でポイント2重取り。年会費初年度無料"
            cta="詳しく見る →"
            href={AFFILIATE.tokyu}
          />
          <AffiliateBanner
            tag="日本株・米国株・NISA"
            title="DMM 株"
            desc="手数料業界最安水準。NISA口座対応・米国株も1株から購入可能"
            cta="口座開設（無料）→"
            href={AFFILIATE.dmm_stock}
          />
          <AffiliateBanner
            tag="株・FX・先物をアプリひとつで"
            title="TOSSY（DMM証券）"
            desc="あらゆる取引がアプリひとつで完結。初心者でも使いやすいUI"
            cta="口座開設（無料）→"
            href={AFFILIATE.dmm_tossy}
          />
        </>
      )}

      {/* 住宅・車ローンタブ：FX自動売買 + 確定申告ツール */}
      {tab === "lo" && (
        <>
          <AffiliateBanner
            tag="FX自動売買"
            title="シストレセレクト365（フジトミ証券）"
            desc="ローン返済と並行して資産を増やしたい方に。FX自動売買で24時間稼働"
            cta="詳しく見る →"
            href={AFFILIATE.fujitomi_fx}
          />
          <AffiliateBanner
            tag="確定申告・家計管理"
            title="マネーフォワード クラウド確定申告"
            desc="住宅ローン控除の申告もラクラク。銀行・カード連携で自動集計"
            cta="無料で試す →"
            href={AFFILIATE.moneyforward}
          />
        </>
      )}
    </div>
  );
}

// このコンポーネントが受け取るデータの型定義
interface LoanViewProps {
  allL: Loan[];                          // 全ローンをまとめた配列
  totalLoanRepayment: number;            // 月次返済合計額
  ltab: string;                          // 現在のローン種別タブ（"cf" | "bl" | "lo"）
  setLtab: (v: string) => void;          // タブ切り替え関数
  cashFlow: any[];                       // 消費者金融のローン配列（LoanSection内部型に合わせてanyを使用）
  setCashFlow: (u: any) => void;         // 消費者金融の更新関数
  balance: any[];                        // 銀行・リボ払いのローン配列
  setBalance: (u: any) => void;          // 銀行・リボ払いの更新関数
  loans: any[];                          // 住宅・車ローンの配列
  setLoans: (u: any) => void;            // 住宅・車ローンの更新関数
  pays: any;                             // 支払済みフラグの記録（LoanSection内部型に合わせてanyを使用）
  setPays: (u: any) => void;             // 支払済みフラグの更新関数
  delItem: (id: string, setArr: (u: any) => void) => void; // ローン削除関数
  showT: (msg: string, type?: string) => void;             // トースト通知表示関数
}

// ローンタブの中身を描画するコンポーネント
export default function LoanView({
  allL,
  totalLoanRepayment,
  ltab,
  setLtab,
  cashFlow,
  setCashFlow,
  balance,
  setBalance,
  loans,
  setLoans,
  pays,
  setPays,
  delItem,
  showT,
}: LoanViewProps) {
  // 全ローンの集計値（カードに使う）
  const totalRemaining = allL.reduce((s, l) => s + Number(l.remaining || 0), 0);
  const totalPrincipal = allL.reduce((s, l) => s + Number(l.principal || l.remaining || 0), 0);
  const totalPaid = Math.max(0, totalPrincipal - totalRemaining);
  const totalProgressPct = totalPrincipal > 0 ? (totalPaid / totalPrincipal) * 100 : 0;
  const totalMonthlyInterest = allL.reduce((s, l) => s + calculateMonthlyInterest(l.remaining, l.rate), 0);
  const totalFutureInterest = allL.reduce((s, l) => {
    const r = calculateTotalInterest(l.remaining, l.rate, l.monthly);
    return r ? s + r.interest : s;
  }, 0);
  // 最長完済までの月数（全ローン中で最も長いものが「全完済」のタイミング）
  const longestMonths = allL.reduce((max, l) => {
    const r = calculateTotalInterest(l.remaining, l.rate, l.monthly);
    return r && r.months > max ? r.months : max;
  }, 0);
  const finalCompletion = longestMonths > 0 ? calculateCompletionDate(longestMonths) : null;

  return (
    <div>
      {/* ────────── 完済カウントダウンカード（借金返済フォーカス） ────────── */}
      {totalRemaining > 0 && longestMonths > 0 && (
        <div style={{ ...STYLE_CARD, background: "linear-gradient(135deg,rgba(15,23,42,0.95) 0%,rgba(52,211,153,0.06) 100%)", border: "1px solid rgba(52,211,153,0.25)" }}>
          <div style={{ fontSize: 10, color: COLOR_POSITIVE, letterSpacing: "2px", textTransform: "uppercase", fontWeight: 700, marginBottom: 8 }}>
            🏁 借金ゼロまで
          </div>
          <div style={{ display: "flex", alignItems: "baseline", gap: 10, marginBottom: 10 }}>
            <span style={{ fontFamily: "monospace", fontSize: 36, fontWeight: 700, color: COLOR_POSITIVE, letterSpacing: "-1px" }}>
              {longestMonths}
            </span>
            <span style={{ fontSize: 14, color: COLOR_TEXT_SECONDARY }}>ヶ月</span>
            {finalCompletion && (
              <span style={{ fontSize: 11, color: COLOR_TEXT_HINT, marginLeft: "auto" }}>
                {finalCompletion.y}年{finalCompletion.m}月完済予定
              </span>
            )}
          </div>
          {/* 元本の返済進捗バー（principal データがあるローン分のみ反映） */}
          {totalPrincipal > totalRemaining && (
            <>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: COLOR_TEXT_HINT, marginBottom: 4 }}>
                <span>元本の返済進捗</span>
                <span style={{ fontFamily: "monospace", color: COLOR_POSITIVE, fontWeight: 700 }}>{totalProgressPct.toFixed(1)}%</span>
              </div>
              <div style={{ height: 8, background: "rgba(255,255,255,0.06)", borderRadius: 4, overflow: "hidden", marginBottom: 6 }}>
                <div style={{ height: "100%", width: `${totalProgressPct}%`, background: COLOR_POSITIVE, borderRadius: 4, transition: "width 0.4s ease" }} />
              </div>
              <div style={{ fontSize: 10, color: COLOR_TEXT_HINT, fontFamily: "monospace" }}>
                {formatYen(totalPaid)} 返済済 / 元本 {formatYen(totalPrincipal)}
              </div>
            </>
          )}
        </div>
      )}

      {/* 全ローン合計カード：総残債・月次返済・今月の利息・支払総利息を表示 */}
      <div style={STYLE_CARD}>
        <div style={{ fontSize: 9, color: COLOR_TEXT_HINT, textTransform: "uppercase", letterSpacing: "2px", marginBottom: 12, display: "flex", justifyContent: "space-between" }}>
          <span>全ローン合計</span>
          <span>{allL.length}件</span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 12 }}>
          <span style={{ fontSize: 9, color: COLOR_TEXT_HINT, letterSpacing: "1px", textTransform: "uppercase" }}>総残債</span>
          <span style={{ fontFamily: "monospace", fontSize: 28, fontWeight: 700, letterSpacing: "-0.5px" }}>
            {formatYen(totalRemaining)}
          </span>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 8 }}>
          <StatLabel label="月次返済" value={formatYen(totalLoanRepayment)} />
          <StatLabel label="今月の利息" value={formatYen(totalMonthlyInterest)} color={COLOR_NEGATIVE} />
          <StatLabel label="支払総利息" value={formatYen(totalFutureInterest)} color={COLOR_NEGATIVE} />
        </div>
        {/* 利息累計の動機づけメッセージ：完済までに払う利息額を強調表示 */}
        {totalFutureInterest > 0 && (
          <div style={{ marginTop: 10, padding: "10px 12px", background: "rgba(248,113,113,0.06)", border: "1px solid rgba(248,113,113,0.2)", borderRadius: 10, fontSize: 12, color: COLOR_NEGATIVE, lineHeight: 1.5 }}>
            💸 このペースで返すと、完済までに <span style={{ fontWeight: 700, fontFamily: "monospace" }}>{formatYen(totalFutureInterest)}</span> を利息として支払います。繰り上げ返済で減らせます。
          </div>
        )}
      </div>

      {/* 返済戦略アドバイス（金利のある複数借入がある時だけ表示） */}
      {allL.filter(l => l.remaining > 0 && l.rate > 0).length > 1 && ((): React.ReactElement => {
        const active = allL.filter(l => l.remaining > 0 && l.rate > 0);
        // 雪崩方式（Avalanche）= 金利の高い順
        const avalanche = [...active].sort((a, b) => b.rate - a.rate);
        // 雪だるま方式（Snowball）= 残債の少ない順
        const snowball = [...active].sort((a, b) => a.remaining - b.remaining);
        return (
          <div style={{ ...STYLE_CARD, background: "rgba(129,140,248,0.05)", border: "1px solid rgba(129,140,248,0.25)", marginBottom: 12 }}>
            <div style={{ fontSize: 11, color: COLOR_ACCENT, fontWeight: 700, marginBottom: 10 }}>
              💡 返済戦略アドバイス（複数借入の優先順）
            </div>
            {/* 雪崩方式 */}
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: COLOR_TEXT_PRIMARY, marginBottom: 4 }}>
                ⛰ 雪崩方式（利息を最小化）
              </div>
              <div style={{ fontSize: 11, color: COLOR_TEXT_HINT, marginBottom: 6, lineHeight: 1.5 }}>
                金利の高い順に集中して返す。数学的に最もお得。
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                {avalanche.map((l, i) => (
                  <span key={l.id} style={{ fontSize: 11, padding: "3px 8px", borderRadius: 999, background: i === 0 ? `${COLOR_ACCENT}33` : "rgba(255,255,255,0.04)", border: `1px solid ${i === 0 ? COLOR_ACCENT : COLOR_BORDER}`, color: i === 0 ? COLOR_ACCENT : COLOR_TEXT_SECONDARY, fontWeight: i === 0 ? 700 : 400 }}>
                    {i + 1}. {l.name} <span style={{ fontFamily: "monospace" }}>({l.rate}%)</span>
                  </span>
                ))}
              </div>
            </div>
            {/* 雪だるま方式 */}
            <div>
              <div style={{ fontSize: 12, fontWeight: 700, color: COLOR_TEXT_PRIMARY, marginBottom: 4 }}>
                ⛄ 雪だるま方式（達成感重視）
              </div>
              <div style={{ fontSize: 11, color: COLOR_TEXT_HINT, marginBottom: 6, lineHeight: 1.5 }}>
                残債の少ない順に集中して返す。早く1件完済できてモチベが上がる。
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                {snowball.map((l, i) => (
                  <span key={l.id} style={{ fontSize: 11, padding: "3px 8px", borderRadius: 999, background: i === 0 ? `${COLOR_POSITIVE}22` : "rgba(255,255,255,0.04)", border: `1px solid ${i === 0 ? COLOR_POSITIVE : COLOR_BORDER}`, color: i === 0 ? COLOR_POSITIVE : COLOR_TEXT_SECONDARY, fontWeight: i === 0 ? 700 : 400 }}>
                    {i + 1}. {l.name} <span style={{ fontFamily: "monospace" }}>({formatYen(l.remaining)})</span>
                  </span>
                ))}
              </div>
            </div>
          </div>
        );
      })()}

      {/* ローン種別タブ切り替え：消費者金融 / 銀行・リボ払い / 住宅・車ローン */}
      <StatBlock tabs={[["cf", "🏧 消費者金融"], ["bl", "🏛 銀行・リボ払い"], ["lo", "🏦 住宅・車ローン"]]} v={ltab} on={setLtab} />

      {/* 消費者金融ローン一覧（元本表示なし） + アフィリエイトバナー */}
      {ltab === "cf" && (
        <>
          <LoanSection arr={cashFlow} setArr={setCashFlow} pfx="cf" pays={pays} setPays={setPays} showPrincipal={false} onDelete={delItem} showT={showT} brands={BRANDS_CF} />
          <AffiliateSection tab="cf" />
        </>
      )}

      {/* 銀行・リボ払いローン一覧（元本表示なし） + アフィリエイトバナー */}
      {ltab === "bl" && (
        <>
          <LoanSection arr={balance} setArr={setBalance} pfx="bl" pays={pays} setPays={setPays} showPrincipal={false} onDelete={delItem} showT={showT} brands={BRANDS_BL} />
          <AffiliateSection tab="bl" />
        </>
      )}

      {/* 住宅・車ローン一覧（元本表示あり） + アフィリエイトバナー */}
      {ltab === "lo" && (
        <>
          <LoanSection arr={loans} setArr={setLoans} pfx="lo" pays={pays} setPays={setPays} showPrincipal={true} onDelete={delItem} showT={showT} />
          <AffiliateSection tab="lo" />
        </>
      )}
    </div>
  );
}
