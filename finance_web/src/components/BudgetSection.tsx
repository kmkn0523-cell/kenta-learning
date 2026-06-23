// ────────── 予算管理コンポーネント ──────────
// カテゴリ別の月予算を設定し、今月の実績と比較するバー表示を出す
// 使用率が80%超で黄色、100%超で赤にして超過を視覚的に伝える

import { useState, CSSProperties } from "react";
import { EXPENSE_CATEGORIES, EXPENSE_CATEGORY_ICONS, formatYen } from "../utils/format";
import { STYLE_CARD, STYLE_BUTTON_PRIMARY, STYLE_BUTTON_OUTLINE, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_HINT, COLOR_BORDER, COLOR_POSITIVE, COLOR_NEGATIVE, COLOR_ACCENT } from "../utils/styles";
import { Input } from "./ui";
import OverspendNotifySettings from "./OverspendNotifySettings";

// ── スタイル定数 ──────────────────────────────────────────

// 前月比バッジの静的スタイル（background・color は動的にスプレッドで上書き）
const STYLE_BS_BADGE_BASE: CSSProperties = {
  fontSize: 12, fontWeight: 700, fontFamily: "monospace",
  borderRadius: 4, padding: "1px 5px", letterSpacing: "0.3px",
};

// ─────────────────────────────────────────────────────────

// 収支1件のデータ型（category と amount だけ使う）
interface TxEntry {
  category?: string;
  amount?: number | string;
}

// このコンポーネントが受け取る props の型
interface BudgetSectionProps {
  budget: Record<string, number>;
  setBudget: (b: Record<string, number>) => void;
  mTx: TxEntry[];
  // 前月の変動支出配列（省略可。前月比バッジの計算に使う）
  prevMTx?: TxEntry[];
  // 使いすぎ通知の設定（任意。渡された時だけ予算の下に表示する）
  notifySettings?: {
    enabled: boolean;
    onToggle: (value: boolean) => void;
    permission: NotificationPermission | "unsupported";
    onRequestPermission: () => void;
  };
}

// budget: {食費: 30000, ...} のオブジェクト
// setBudget: budget の更新関数
// mTx: 今月の変動支出配列（日付フィルタ済み）
// prevMTx: 前月の変動支出配列（前月比バッジ用）
export default function BudgetSection({ budget, setBudget, mTx, prevMTx = [], notifySettings }: BudgetSectionProps) {
  const [editing, setEditing] = useState(false);                  // 予算設定フォームの表示フラグ
  const [draft, setDraft] = useState<Record<string, string>>({});  // 編集中の仮の予算値（文字列として管理）

  // 今月の支出をカテゴリ別に集計する
  const actual: Record<string, number> = {};
  mTx.forEach(t => {
    actual[t.category] = (actual[t.category] || 0) + Number(t.amount || 0);
  });

  // 前月の支出をカテゴリ別に集計する
  const prevActual: Record<string, number> = {};
  prevMTx.forEach(t => {
    prevActual[t.category] = (prevActual[t.category] || 0) + Number(t.amount || 0);
  });

  // カテゴリの前月比（%）を返す。前月データが0なら null（バッジ非表示）
  function momPct(cat: string): number | null {
    const cur = actual[cat] || 0;
    const prev = prevActual[cat] || 0;
    if (prev === 0) return null; // 前月データなし → バッジ非表示
    return ((cur - prev) / prev) * 100;
  }

  // 予算か実績のどちらかがあるカテゴリだけ表示する
  const activeCats = EXPENSE_CATEGORIES.filter(c => budget[c] || actual[c]);

  // 全カテゴリの予算合計と実績合計
  const totalBudget = EXPENSE_CATEGORIES.reduce((s, c) => s + Number(budget[c] || 0), 0);
  const totalActual = mTx.reduce((s, t) => s + Number(t.amount || 0), 0);

  // 「予算を設定」を押した時：現在の予算値をドラフトに写す
  function startEdit() {
    const d = {};
    EXPENSE_CATEGORIES.forEach(c => { d[c] = String(budget[c] || ""); });
    setDraft(d);
    setEditing(true);
  }

  // 「保存」を押した時：空欄・0のカテゴリを除いて保存する
  function save() {
    const next = {};
    EXPENSE_CATEGORIES.forEach(c => {
      const v = Number(draft[c]);
      if (v > 0) next[c] = v;
    });
    setBudget(next);
    setEditing(false);
  }

  // 使用率に応じた色を返す（green/yellow/red）
  // Dashboard の paceWarning と同じ色使いに統一する
  function progressColor(ratio: number | null): string {
    if (ratio === null) return COLOR_TEXT_SECONDARY;
    if (ratio > 1) return COLOR_NEGATIVE;      // 100%超：赤
    if (ratio > 0.8) return "#fbbf24";         // 80〜100%：黄色（注意ライン）
    return COLOR_POSITIVE;                     // 80%以下：緑（安全）
  }

  return (
    <div style={STYLE_CARD}>
      {/* ヘッダー：タイトルと設定ボタン */}
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:12 }}>
        <div style={{ fontSize:12, color:COLOR_TEXT_HINT, textTransform:"uppercase", letterSpacing:"1.5px" }}>予算管理</div>
        {!editing && (
          <button type="button" onClick={startEdit} style={{ ...STYLE_BUTTON_OUTLINE, fontSize:12, padding:"5px 12px", minHeight:32 }}>
            予算を設定
          </button>
        )}
      </div>

      {/* 予算が1件も設定されていない かつ 編集中でもない時：案内メッセージ */}
      {totalBudget === 0 && !editing && (
        <div style={{ textAlign:"center", padding:"20px 0", color:COLOR_TEXT_HINT, fontSize:13 }}>
          <div style={{ fontSize:28, marginBottom:8 }}>📊</div>
          <div>「予算を設定」からカテゴリ別の月予算を入力できます</div>
        </div>
      )}

      {/* 予算設定済みで通常表示の時：全体バー＋カテゴリ別バーを表示 */}
      {totalBudget > 0 && !editing && (
        <div>
          {/* 全体の使用状況 */}
          <div style={{ display:"flex", justifyContent:"space-between", fontSize:12, marginBottom:4 }}>
            <span style={{ color:COLOR_TEXT_HINT }}>変動支出合計</span>
            <span style={{ fontFamily:"monospace", color: totalActual > totalBudget ? COLOR_NEGATIVE : COLOR_TEXT_PRIMARY }}>
              {formatYen(totalActual)} <span style={{ color:COLOR_TEXT_HINT }}>/ {formatYen(totalBudget)}</span>
            </span>
          </div>
          {/* 全体プログレスバー */}
          <div style={{ height:6, background:"rgba(255,255,255,0.08)", borderRadius:3, overflow:"hidden", marginBottom:18 }}>
            <div style={{
              height:"100%",
              width: Math.min(100, totalBudget > 0 ? (totalActual / totalBudget) * 100 : 0) + "%",
              background: progressColor(totalBudget > 0 ? totalActual / totalBudget : null),
              borderRadius:3,
              transition:"width 0.4s",
            }}/>
          </div>

          {/* ──────── 予算アラートバナー ────────
              80%以上使っているカテゴリがある時だけ上部に一覧表示する
              超過（赤）と注意（黄色）を分けて見せる */}
          {activeCats.some(c => budget[c] && (actual[c] || 0) / budget[c] > 0.8) && (
            <div style={{
              background: "rgba(251,191,36,0.06)",
              border: "1px solid rgba(251,191,36,0.22)",
              borderRadius: 10,
              padding: "10px 14px",
              marginBottom: 16,
            }}>
              {/* バナーのタイトル行 */}
              <div style={{ fontSize: 12, color: "#fbbf24", fontWeight: 600, marginBottom: 8, letterSpacing: "0.5px" }}>
                ⚠ 予算アラート
              </div>
              {/* アラート対象カテゴリを1行ずつ表示 */}
              {activeCats
                .filter(c => budget[c] && (actual[c] || 0) / budget[c] > 0.8)
                .map(c => {
                  const b = Number(budget[c]);
                  const a = Number(actual[c] || 0);
                  const isOver = a > b;
                  const alertColor = isOver ? COLOR_NEGATIVE : "#fbbf24";
                  return (
                    <div key={c} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                      {/* カテゴリ名（超過は赤・注意は黄色） */}
                      <span style={{ fontSize: 12, color: alertColor }}>
                        {EXPENSE_CATEGORY_ICONS[c]} {c}
                      </span>
                      {/* 残り金額 or 超過金額 */}
                      <span style={{ fontSize: 12, fontFamily: "monospace", fontWeight: 600, color: alertColor }}>
                        {isOver
                          ? `${formatYen(a - b)} 超過`
                          : `残り ${formatYen(b - a)}`}
                      </span>
                    </div>
                  );
                })
              }
            </div>
          )}

          {/* カテゴリ別の使用状況 */}
          {activeCats.map(c => {
            const b = Number(budget[c] || 0);
            const a = Number(actual[c] || 0);
            const ratio = b > 0 ? a / b : null; // 予算が設定されていない場合は null
            const col = progressColor(ratio);
            // 前月比バッジの計算
            const pct = momPct(c);
            // pctが正（出費増）→ 赤、負（出費減）→ 緑
            const badgeColor = pct === null ? null : pct > 0 ? COLOR_NEGATIVE : COLOR_POSITIVE;
            const badgeText = pct === null ? null : `${pct > 0 ? "+" : ""}${Math.round(pct)}%`;
            return (
              <div key={c} style={{ marginBottom:12 }}>
                <div style={{ display:"flex", justifyContent:"space-between", fontSize:12, marginBottom:4 }}>
                  {/* カテゴリ名＋前月比バッジ */}
                  <span style={{ display:"flex", alignItems:"center", gap:5 }}>
                    {EXPENSE_CATEGORY_ICONS[c]} {c}
                    {/* 前月データがある場合だけバッジを表示 */}
                    {badgeText !== null && (
                      <span style={{
                        ...STYLE_BS_BADGE_BASE,
                        background: pct > 0 ? "rgba(248,113,113,0.13)" : "rgba(74,222,128,0.13)",
                        color: badgeColor,
                      }}>
                        {badgeText}
                      </span>
                    )}
                  </span>
                  <span style={{ fontFamily:"monospace", color:col }}>
                    {formatYen(a)}
                    {b > 0 && <span style={{ color:COLOR_TEXT_HINT }}> / {formatYen(b)}</span>}
                    {/* 超過した時は「超過」バッジを表示 */}
                    {ratio !== null && ratio > 1 && (
                      <span style={{ marginLeft:6, fontSize:12, background:"rgba(248,113,113,0.15)", color:COLOR_NEGATIVE, borderRadius:4, padding:"1px 5px" }}>
                        超過
                      </span>
                    )}
                  </span>
                </div>
                {/* 予算が設定されているカテゴリだけプログレスバーを出す */}
                {b > 0 && (
                  <>
                    {/* プログレスバー */}
                    <div style={{ height:4, background:"rgba(255,255,255,0.08)", borderRadius:2, overflow:"hidden" }}>
                      <div style={{
                        height:"100%",
                        width: Math.min(100, ratio * 100) + "%",
                        background: col,
                        borderRadius:2,
                        transition:"width 0.4s",
                      }}/>
                    </div>
                    {/* バーの下に「残り ¥X,XXX」or「¥X,XXX 超過」を小さく表示 */}
                    <div style={{ fontSize: 12, color: col, textAlign: "right", marginTop: 3, fontFamily: "monospace" }}>
                      {a > b
                        ? `${formatYen(a - b)} 超過`
                        : `残り ${formatYen(b - a)}`}
                    </div>
                  </>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* 予算設定フォーム（editing=true の時だけ表示） */}
      {editing && (
        <div>
          <div style={{ fontSize:12, color:COLOR_TEXT_HINT, marginBottom:12, lineHeight:1.6 }}>
            各カテゴリの月予算を入力してください（空欄 = 予算なし）
          </div>
          <div style={{ display:"flex", flexDirection:"column", gap:10, marginBottom:14 }}>
            {EXPENSE_CATEGORIES.map(c => (
              <div key={c} style={{ display:"flex", alignItems:"center", gap:10 }}>
                {/* カテゴリ名と絵文字 */}
                <span style={{ fontSize:13, flex:1 }}>{EXPENSE_CATEGORY_ICONS[c]} {c}</span>
                {/* 金額入力欄：幅を固定して右端に揃える */}
                <div style={{ width:150 }}>
                  <Input
                    money
                    type="number"
                    value={draft[c] || ""}
                    onChange={e => setDraft(d => ({ ...d, [c]: e.target.value }))}
                    placeholder="予算（円）"
                  />
                </div>
              </div>
            ))}
          </div>
          <div style={{ display:"flex", gap:10 }}>
            <button type="button" onClick={save} style={STYLE_BUTTON_PRIMARY}>保存</button>
            <button type="button" onClick={() => setEditing(false)} style={{ ...STYLE_BUTTON_OUTLINE, minHeight:44, padding:"11px 18px" }}>
              キャンセル
            </button>
          </div>
        </div>
      )}
      {/* 使いすぎ通知の設定（App から渡された時だけ表示） */}
      {notifySettings && (
        <OverspendNotifySettings
          enabled={notifySettings.enabled}
          onToggle={notifySettings.onToggle}
          permission={notifySettings.permission}
          onRequestPermission={notifySettings.onRequestPermission}
        />
      )}
    </div>
  );
}
