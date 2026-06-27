// ────────── calculator.ts のユニットテスト ──────────
// 電卓の状態機械（純粋関数）を一通り検証する
import { initCalc, calcReducer, currentResult, confirmValue, formatExpression, formatResult, CalcState, CalcAction } from "../../utils/calculator";

// アクションを順番に適用していくヘルパー（テストを読みやすくするため）
function run(start: CalcState, ...actions: CalcAction[]): CalcState {
  return actions.reduce((s, a) => calcReducer(s, a), start);
}
// "1250" → [{digit:"1"},{digit:"2"},...] に変換するヘルパー
const digits = (str: string): CalcAction[] => str.split("").map(d => ({ type: "digit", d }));

describe("initCalc", () => {
  it("空・0 のときは current が空", () => {
    expect(initCalc("").current).toBe("");
    expect(initCalc(0).current).toBe("");
  });
  it("既存値はそのまま current に入る（カンマは除去）", () => {
    expect(initCalc("1,000").current).toBe("1000");
    expect(initCalc(2500).current).toBe("2500");
  });
});

describe("calcReducer: 基本の四則演算", () => {
  it("足し算 1250 + 980 = 2230", () => {
    const s = run(initCalc(""), ...digits("1250"), { type: "operator", op: "+" }, ...digits("980"), { type: "equals" });
    expect(confirmValue(s)).toBe(2230);
  });
  it("引き算 1000 - 200 = 800", () => {
    const s = run(initCalc(""), ...digits("1000"), { type: "operator", op: "-" }, ...digits("200"), { type: "equals" });
    expect(confirmValue(s)).toBe(800);
  });
  it("掛け算 12 × 3 = 36", () => {
    const s = run(initCalc(""), ...digits("12"), { type: "operator", op: "*" }, ...digits("3"), { type: "equals" });
    expect(confirmValue(s)).toBe(36);
  });
});

describe("calcReducer: 逐次計算（電卓式）", () => {
  it("1 + 2 × 3 は (1+2)×3 = 9（数学の優先順位ではない）", () => {
    const s = run(initCalc(""), ...digits("1"), { type: "operator", op: "+" }, ...digits("2"), { type: "operator", op: "*" }, ...digits("3"), { type: "equals" });
    expect(confirmValue(s)).toBe(9);
  });
  it("演算子の連続入力は最後の演算子で上書き 5 +（×に変更）2 = 10", () => {
    const s = run(initCalc(""), ...digits("5"), { type: "operator", op: "+" }, { type: "operator", op: "*" }, ...digits("2"), { type: "equals" });
    expect(confirmValue(s)).toBe(10);
  });
});

describe("calcReducer: 既存値からの継続", () => {
  it("初期値1000を開いて +500 = 1500", () => {
    const s = run(initCalc("1000"), { type: "operator", op: "+" }, ...digits("500"), { type: "equals" });
    expect(confirmValue(s)).toBe(1500);
  });
  it("初期値があっても数字を先に押すと打ち直しになる（9 → 9）", () => {
    const s = run(initCalc("1000"), ...digits("9"));
    expect(confirmValue(s)).toBe(9);
  });
});

describe("currentResult: 結果の常時プレビュー", () => {
  it("980 を入力中（演算子の右辺）に結果が更新される 1250 + 980 → 2230", () => {
    const s = run(initCalc(""), ...digits("1250"), { type: "operator", op: "+" }, ...digits("980"));
    expect(currentResult(s)).toBe(2230);
  });
  it("数字だけ入力中はその数字自身", () => {
    const s = run(initCalc(""), ...digits("42"));
    expect(currentResult(s)).toBe(42);
  });
});

describe("calcReducer: ÷0 エラー", () => {
  it("10 ÷ 0 はエラーになり、結果は null", () => {
    const s = run(initCalc(""), ...digits("10"), { type: "operator", op: "/" }, ...digits("0"), { type: "equals" });
    expect(s.error).toBe(true);
    expect(currentResult(s)).toBeNull();
  });
  it("clear でエラーから復帰する", () => {
    const s = run(initCalc(""), ...digits("10"), { type: "operator", op: "/" }, ...digits("0"), { type: "equals" }, { type: "clear" });
    expect(s.error).toBe(false);
    expect(confirmValue(s)).toBe(0);
  });
});

describe("confirmValue: 小数は四捨五入で整数化", () => {
  it("10 ÷ 3 = 3.333... → 確定で 3", () => {
    const s = run(initCalc(""), ...digits("10"), { type: "operator", op: "/" }, ...digits("3"), { type: "equals" });
    expect(confirmValue(s)).toBe(3);
  });
  it("5 ÷ 2 = 2.5 → 確定で 3（四捨五入）", () => {
    const s = run(initCalc(""), ...digits("5"), { type: "operator", op: "/" }, ...digits("2"), { type: "equals" });
    expect(confirmValue(s)).toBe(3);
  });
});

describe("桁あふれガード", () => {
  it("整数13桁目は受け付けない（12桁で止まる）", () => {
    const s = run(initCalc(""), ...digits("12345678901234"));
    expect(s.current.replace(/[^\d]/g, "").length).toBe(12);
  });
});

describe("backspace と小数点", () => {
  it("backspace で1文字消える", () => {
    const s = run(initCalc(""), ...digits("123"), { type: "backspace" });
    expect(s.current).toBe("12");
  });
  it("小数点は1つしか入らない", () => {
    const s = run(initCalc(""), ...digits("1"), { type: "dot" }, { type: "dot" }, ...digits("5"));
    expect(s.current).toBe("1.5");
  });
});

describe("formatExpression / formatResult", () => {
  it("式が「1,250 ＋ 980」のように出る", () => {
    const s = run(initCalc(""), ...digits("1250"), { type: "operator", op: "+" }, ...digits("980"));
    expect(formatExpression(s)).toBe("1,250 ＋ 980");
  });
  it("formatResult はカンマ区切り、小数は最大4桁", () => {
    expect(formatResult(2230)).toBe("2,230");
    expect(formatResult(3.3333333)).toBe("3.3333");
  });
});
