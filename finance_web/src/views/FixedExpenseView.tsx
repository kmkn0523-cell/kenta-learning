// ────────── 固定費タブ ビューコンポーネント ──────────
// 毎月かかる固定費の一覧表示・追加フォームをまとめたコンポーネント
// App.tsx から切り出して、見通しを良くしている

import { FixedExpense, CategoryConfig } from "../types";
import { formatYen } from "../utils/format";
import { COLOR_TEXT_HINT, STYLE_CARD, STYLE_BUTTON_PRIMARY, STYLE_BUTTON_OUTLINE } from "../utils/styles";
import { Input, Select } from "../components/ui";
import FxRow from "../components/FxRow";

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
  // 固定費追加フォームの入力値
  fxF: { name: string; cat: string; amt: string; note?: string };
  // フォームの入力値を更新する関数
  setFxF: (u: { name: string; cat: string; amt: string; note?: string } | ((prev: { name: string; cat: string; amt: string; note?: string }) => { name: string; cat: string; amt: string; note?: string })) => void;
  // 固定費を追加する処理（keepOpen=true なら追加後もフォームを開いたまま）
  addFx: (keepOpen?: boolean) => boolean;
  // トースト通知を表示する関数
  showT: (msg: string, type?: string) => void;
  // 確認ダイアログを表示する関数
  ask: (title: string, msg: string, ok: () => void) => void;
  // カテゴリ設定（動的にカテゴリ名・アイコンを取得するために使う）
  categoryConfig: CategoryConfig;
  // 削除＋Undo：即削除してToastに「元に戻す」を出す
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  delItem: (id: string, setArr: (u: any) => void, label?: string) => void;
}

// 固定費タブ全体のビュー
export default function FixedExpenseView({
  totalFixedExpense,
  fixedExpenses,
  setFixedExpenses,
  showFx,
  setShowFx,
  fxF,
  setFxF,
  addFx,
  showT,
  ask,
  categoryConfig,
  delItem,
}: FixedExpenseViewProps) {
  // categoryConfig.fixedExpense を order 順で並べ、カテゴリ名とアイコンのマップを作る
  const fixedCategoryNames = categoryConfig.fixedExpense.slice().sort((a, b) => a.order - b.order).map(c => c.name);
  const fixedCategoryIcons: Record<string, string> = Object.fromEntries(categoryConfig.fixedExpense.map(c => [c.name, c.icon]));

  return (
    <div>
      {/* 合計表示ヘッダー：月の固定費合計と件数を表示 */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18 }}>
        <div>
          <div style={{ fontSize: 9, color: COLOR_TEXT_HINT, marginBottom: 5, letterSpacing: "2px", textTransform: "uppercase" }}>毎月の固定費合計</div>
          <div style={{ fontFamily: "monospace", fontSize: 28, fontWeight: 700, letterSpacing: "-0.5px" }}>{formatYen(totalFixedExpense)}</div>
        </div>
        <div style={{ fontSize: 12, color: COLOR_TEXT_HINT }}>{fixedExpenses.length}項目</div>
      </div>

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
            <button onClick={() => addFx()} style={{ ...STYLE_BUTTON_PRIMARY, flex: "1 1 120px" }}>追加</button>
            <button onClick={() => addFx(true)} style={{ ...STYLE_BUTTON_OUTLINE, minHeight: 44, padding: "11px 14px", flex: "1 1 120px" }}>追加して続ける</button>
            <button onClick={() => setShowFx(false)} style={{ ...STYLE_BUTTON_OUTLINE, minHeight: 44, padding: "11px 14px" }}>キャンセル</button>
          </div>
        </div>
      ) : (
        // フォームが閉じているときは「追加」ボタンを表示
        <button onClick={() => setShowFx(true)} style={{ ...STYLE_BUTTON_PRIMARY, marginTop: 8 }}>＋ 固定費を追加</button>
      )}
    </div>
  );
}
