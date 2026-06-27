// ────────── 固定費タブ ビューコンポーネント ──────────
// 毎月かかる固定費の一覧表示・追加フォームをまとめたコンポーネント
// App.tsx から切り出して、見通しを良くしている

import { useState } from "react";
import { useUI } from "../contexts/UIHelpersContext";
import { FixedExpense, CategoryConfig } from "../types";
import { formatYen } from "../utils/format";
import { COLOR_TEXT_HINT, STYLE_CARD, STYLE_BUTTON_PRIMARY, STYLE_BUTTON_OUTLINE } from "../utils/styles";
import { Input, Select } from "../components/ui";
import FxRow from "../components/FxRow";
import FixedExpenseCalendar from "../components/FixedExpenseCalendar";

// このコンポーネントが受け取るデータの型定義
interface FixedExpenseViewProps {
  // 固定費の月合計金額
  totalFixedExpense: number;
  // 固定費の一覧データ
  fixedExpenses: FixedExpense[];
  // 固定費一覧を更新する関数（直接渡すか、前の値を使って更新できる）
  setFixedExpenses: (u: FixedExpense[] | ((prev: FixedExpense[]) => FixedExpense[])) => void;
  // 追加フォームを表示するかどうか
  showFx: boolean;
  // フォームの表示・非表示を切り替える関数
  setShowFx: (v: boolean) => void;
  // 固定費を追加する処理（フォーム内容を渡す。keepOpen=true なら追加後もフォームを開いたまま）
  addFx: (form: { name: string; cat: string; amt: string; note?: string }, keepOpen?: boolean) => boolean;
  // カテゴリ設定（動的にカテゴリ名・アイコンを取得するために使う）
  categoryConfig: CategoryConfig;
  // showT/delItem は useUI() から取得
}

// 固定費タブ全体のビュー
export default function FixedExpenseView({
  totalFixedExpense,
  fixedExpenses,
  setFixedExpenses,
  showFx,
  setShowFx,
  addFx,
  categoryConfig,
}: FixedExpenseViewProps) {
  const { showT, delItem } = useUI();
  // categoryConfig.fixedExpense を order 順で並べ、カテゴリ名とアイコンのマップを作る
  const fixedCategoryNames = categoryConfig.fixedExpense.slice().sort((a, b) => a.order - b.order).map(c => c.name);
  const fixedCategoryIcons: Record<string, string> = Object.fromEntries(categoryConfig.fixedExpense.map(c => [c.name, c.icon]));

  // 固定費入力フォームの中身（App.tsx から降格したローカルstate）。タイピングはこの View 内で完結し、App 全体を再レンダしない。
  const [fxF, setFxF] = useState<{ name: string; cat: string; amt: string; note?: string }>({ name: "", cat: "家賃", amt: "", note: "" });

  return (
    <div>
      {/* 合計表示ヘッダー：月の固定費合計と件数を表示 */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18 }}>
        <div>
          <div style={{ fontSize: 12, color: COLOR_TEXT_HINT, marginBottom: 5, letterSpacing: "2px", textTransform: "uppercase" }}>毎月の固定費合計</div>
          <div style={{ fontFamily: FONT_NUM, fontSize: 28, fontWeight: 700, letterSpacing: "-0.5px" }}>{formatYen(totalFixedExpense)}</div>
          <div style={{ fontSize: 12, color: COLOR_TEXT_HINT, marginTop: 3 }}>年間 {formatYen(totalFixedExpense * 12)}</div>
          {/* 自動追加中の項目があれば補足説明を表示 */}
          {fixedExpenses.some(f => f.autoTrack) && (
            <div style={{ fontSize: 12, color: COLOR_TEXT_HINT, marginTop: 4 }}>
              ※ 🔁 自動追加中の項目は変動支出として集計されます
            </div>
          )}
        </div>
        <div style={{ fontSize: 12, color: COLOR_TEXT_HINT }}>{fixedExpenses.length}項目</div>
      </div>

      {/* ────────── 引落カレンダー：引落日順に今月の固定費を一覧表示 ────────── */}
      <FixedExpenseCalendar fixedExpenses={fixedExpenses}/>

      {/* 固定費が0件かつフォーム非表示のとき、空状態のメッセージを表示 */}
      {fixedExpenses.length === 0 && !showFx && (
        <div style={{ textAlign: "center", padding: "44px 0", color: COLOR_TEXT_HINT }}>
          <div style={{ fontSize: 36, marginBottom: 10 }}>📌</div>
          <div>固定費が登録されていません</div>
          <div style={{ fontSize: 12, marginTop: 8 }}>家賃・サブスクなど毎月かかる費用を登録しましょう</div>
        </div>
      )}

      {/* 固定費の一覧：各行は FxRow コンポーネントで表示 */}
      {fixedExpenses.map((item, idx) => (
        <FxRow
          key={item.id}
          item={item}
          // 編集保存時：対象IDの項目だけ更新して通知（payDay など余分なフィールドを保持するためスプレッドで合成し、amountを数値に統一）
          onSave={u => {
            setFixedExpenses(p => p.map(f => f.id === u.id ? { ...f, ...u, amount: Number(u.amount) } : f));
            showT("更新しました");
          }}
          // 削除時：即削除してToastに「元に戻す」を出す
          onDelete={() => delItem(item.id, setFixedExpenses, "固定費を削除しました")}
          // 自動追加のON/OFFを切り替える（有効にすると毎月変動支出として自動追加される）
          onToggleAutoTrack={() => setFixedExpenses(p => p.map(f =>
            f.id === item.id
              // autoTrack を反転させる。有効→無効にする場合は lastAutoAdded をリセット
              ? { ...f, autoTrack: !f.autoTrack, lastAutoAdded: f.autoTrack ? undefined : f.lastAutoAdded }
              : f
          ))}
          // 上に移動：最初の項目は移動不可（null）
          onMoveUp={idx > 0 ? () => setFixedExpenses(p => {
            const a = [...p];
            [a[idx - 1], a[idx]] = [a[idx], a[idx - 1]];
            return a;
          }) : null}
          // 下に移動：最後の項目は移動不可（null）
          onMoveDown={idx < fixedExpenses.length - 1 ? () => setFixedExpenses(p => {
            const a = [...p];
            [a[idx], a[idx + 1]] = [a[idx + 1], a[idx]];
            return a;
          }) : null}
        />
      ))}

      {/* 追加フォームまたは追加ボタンを切り替え表示 */}
      {showFx ? (
        <div style={STYLE_CARD}>
          {/* 固定費の入力フィールド群 */}
          <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 12 }}>
            <Input value={fxF.name} onChange={e => setFxF(f => ({ ...f, name: e.target.value }))} placeholder="項目名（例: Netflix）" />
            <Select value={fxF.cat} onChange={e => setFxF(f => ({ ...f, cat: e.target.value }))} options={fixedCategoryNames} icons={fixedCategoryIcons} />
            <Input money type="number" value={fxF.amt} onChange={e => setFxF(f => ({ ...f, amt: e.target.value }))} placeholder="月額（円）" />
          </div>
          {/* 追加・連続追加・キャンセルボタン（連続追加はフォームを閉じずに次の入力ができる） */}
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button type="button" onClick={() => { if (addFx(fxF)) setFxF({ name: "", cat: "家賃", amt: "", note: "" }); }} style={{ ...STYLE_BUTTON_PRIMARY, flex: "1 1 120px" }}>追加</button>
            <button type="button" onClick={() => { if (addFx(fxF, true)) setFxF({ name: "", cat: "家賃", amt: "", note: "" }); }} style={{ ...STYLE_BUTTON_OUTLINE, minHeight: 44, padding: "11px 14px", flex: "1 1 120px" }}>追加して続ける</button>
            <button type="button" onClick={() => setShowFx(false)} style={{ ...STYLE_BUTTON_OUTLINE, minHeight: 44, padding: "11px 14px" }}>キャンセル</button>
          </div>
        </div>
      ) : (
        // フォームが閉じているときは「追加」ボタンを表示
        <button type="button" onClick={() => setShowFx(true)} style={{ ...STYLE_BUTTON_PRIMARY, marginTop: 8 }}>＋ 固定費を追加</button>
      )}
    </div>
  );
}
