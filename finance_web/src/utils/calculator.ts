// ────────── 電卓の計算ロジック（純粋関数のみ） ──────────
// Reactに依存しないので、この1ファイルだけで単体テストできる
import { parseYenAmount } from "./format";

// 使える演算子の種類
export type Operator = "+" | "-" | "*" | "/";

// 電卓の状態（current=今表示・入力中の数字 / previous=演算子の左辺 / operation=押された演算子 /
//  overwrite=次に数字を押したら current を上書きするか / error=÷0などのエラー中か）
export interface CalcState {
  current: string;
  previous: number | null;
  operation: Operator | null;
  overwrite: boolean;
  error: boolean;
}

// 電卓に対する操作（ボタン1つ＝1アクション）
export type CalcAction =
  | { type: "digit"; d: string }
  | { type: "dot" }
  | { type: "operator"; op: Operator }
  | { type: "equals" }
  | { type: "clear" }
  | { type: "backspace" };

// 整数部の最大桁数（兆の手前まで）
export const MAX_INT_DIGITS = 12;

// 演算子の記号（画面表示用。マイナスは見やすい全角マイナス）
const OP_SYMBOL: Record<Operator, string> = { "+": "＋", "-": "−", "*": "×", "/": "÷" };

// まっさらな状態を作る（clear と初期化で共用）
function emptyState(): CalcState {
  return { current: "", previous: null, operation: null, overwrite: true, error: false };
}

// 初期状態を作る（金額欄の今の値を current に入れる。0や空なら空にする）
export function initCalc(initial: string | number): CalcState {
  const n = parseYenAmount(initial); // 数字以外を除いた整数
  return { ...emptyState(), current: n === 0 ? "" : String(n) };
}

// 実際の四則演算。÷0 のときだけ null を返す（呼び出し側でエラー化する）
function apply(a: number, op: Operator, b: number): number | null {
  switch (op) {
    case "+": return a + b;
    case "-": return a - b;
    case "*": return a * b;
    case "/": return b === 0 ? null : a / b;
  }
}

// エラー状態を作る共通処理
function toError(): CalcState {
  return { ...emptyState(), error: true };
}

// 状態＋アクション → 新しい状態（純粋関数）
export function calcReducer(state: CalcState, action: CalcAction): CalcState {
  switch (action.type) {
    case "clear":
      return emptyState();

    case "digit": {
      if (state.error) return state;
      // overwrite中（演算子や=の直後・開いた直後）は新しく打ち直す
      if (state.overwrite) {
        return { ...state, current: action.d, overwrite: false };
      }
      // 桁あふれガード（整数部の数字だけ数える。小数を打ち始めたら制限しない）
      const intLen = state.current.split(".")[0].replace(/[^\d]/g, "").length;
      if (!state.current.includes(".") && intLen >= MAX_INT_DIGITS) return state;
      // 先頭の余分な0を防ぐ（"0" の次は置き換え）
      if (state.current === "0") return { ...state, current: action.d };
      return { ...state, current: state.current + action.d };
    }

    case "dot": {
      if (state.error) return state;
      if (state.overwrite) return { ...state, current: "0.", overwrite: false };
      if (state.current.includes(".")) return state;
      if (state.current === "") return { ...state, current: "0." };
      return { ...state, current: state.current + "." };
    }

    case "operator": {
      if (state.error) return state;
      // まだ左辺が無いとき → current を左辺にして演算子をセット
      if (state.previous === null) {
        const cur = state.current === "" ? 0 : Number(state.current);
        return { ...state, previous: cur, operation: action.op, overwrite: true };
      }
      // 演算子の連打（overwrite中）→ 演算子だけ差し替え
      if (state.overwrite) {
        return { ...state, operation: action.op };
      }
      // 逐次計算：いったん previous と current を計算してから次の演算子へ
      const result = apply(state.previous, state.operation!, Number(state.current));
      if (result === null) return toError();
      return { ...state, previous: result, current: String(result), operation: action.op, overwrite: true };
    }

    case "equals": {
      if (state.error || state.previous === null || state.operation === null) return state;
      const right = state.current === "" ? state.previous : Number(state.current);
      const result = apply(state.previous, state.operation, right);
      if (result === null) return toError();
      return { ...state, current: String(result), previous: null, operation: null, overwrite: true };
    }

    case "backspace": {
      if (state.error) return emptyState();
      if (state.overwrite) return state;
      return { ...state, current: state.current.slice(0, -1) };
    }
  }
}

// いま画面に出すべき計算結果（演算子の右辺を入力中なら途中結果をプレビュー）
export function currentResult(state: CalcState): number | null {
  if (state.error) return null;
  // 左辺・演算子があって右辺を入力中 → 途中結果を出す
  if (state.previous !== null && state.operation && !state.overwrite && state.current !== "") {
    return apply(state.previous, state.operation, Number(state.current));
  }
  if (state.current !== "") return Number(state.current);
  if (state.previous !== null) return state.previous;
  return 0;
}

// 確定ボタンで金額欄へ渡す整数（小数は四捨五入）
export function confirmValue(state: CalcState): number {
  const r = currentResult(state);
  return Math.round(r ?? 0);
}

// 数字文字列をカンマ区切りに（入力中の小数もそのまま見せる）
function formatNumberString(numStr: string): string {
  if (numStr === "") return "";
  const [intPart, decPart] = numStr.split(".");
  const intFmt = Number(intPart || "0").toLocaleString("ja-JP");
  return decPart !== undefined ? `${intFmt}.${decPart}` : intFmt;
}

// 上段に出す式（例: "1,250 ＋ 980"）
export function formatExpression(state: CalcState): string {
  if (state.error) return "エラー";
  if (state.previous === null) return formatNumberString(state.current);
  const left = formatNumberString(String(state.previous));
  const op = state.operation ? ` ${OP_SYMBOL[state.operation]} ` : "";
  const right = state.overwrite ? "" : formatNumberString(state.current);
  return `${left}${op}${right}`.trimEnd();
}

// 結果の表示（カンマ区切り・小数は最大4桁まで）
export function formatResult(n: number): string {
  return n.toLocaleString("ja-JP", { maximumFractionDigits: 4 });
}
