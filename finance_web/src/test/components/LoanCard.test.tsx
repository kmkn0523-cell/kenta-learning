// ────────── LoanCard コンポーネントのテスト ──────────
// ローン1件分の表示・完済表示・警告表示を確認する

import { render, screen, fireEvent } from "@testing-library/react";
import LoanCard from "../../components/LoanCard";

const noop = () => {};

// テスト用のローンサンプルデータ（未完済）
const activeLoan = {
  id: "loan-001",
  name: "アコム",
  rate: 18,
  remaining: 500000,
  monthly: 20000,
  principal: 500000,
  payDay: "10日",
  autoMode: false,
};

// テスト用：残債0（完済済み）
const paidLoan = {
  ...activeLoan,
  id: "loan-002",
  remaining: 0,
};

// テスト用：月返済額が月利息以下（永遠に完済できないパターン）
const insolventLoan = {
  ...activeLoan,
  id: "loan-003",
  remaining: 10000000, // 残債1000万
  monthly: 5000,       // 月返済5千円 < 月利息15万円
  rate: 18,
};

describe("LoanCard（通常表示）", () => {
  it("ローン名が表示される", () => {
    render(<LoanCard loan={activeLoan} onEdit={noop} onDelete={noop} payVal="20000" onPayChange={noop} onPaySubmit={noop} onToggleAuto={noop}/>);
    expect(screen.getByText("アコム")).toBeInTheDocument();
  });

  it("金利が表示される", () => {
    render(<LoanCard loan={activeLoan} onEdit={noop} onDelete={noop} payVal="20000" onPayChange={noop} onPaySubmit={noop} onToggleAuto={noop}/>);
    expect(screen.getByText(/18%/)).toBeInTheDocument();
  });

  it("引落日が設定されているとき「10日」が表示される", () => {
    render(<LoanCard loan={activeLoan} onEdit={noop} onDelete={noop} payVal="20000" onPayChange={noop} onPaySubmit={noop} onToggleAuto={noop}/>);
    expect(screen.getByText(/10日/)).toBeInTheDocument();
  });

  it("編集・削除ボタンが表示される", () => {
    render(<LoanCard loan={activeLoan} onEdit={noop} onDelete={noop} payVal="20000" onPayChange={noop} onPaySubmit={noop} onToggleAuto={noop}/>);
    expect(screen.getByText("編集")).toBeInTheDocument();
    expect(screen.getByText("削除")).toBeInTheDocument();
  });

  it("手動モードのとき「反映」ボタンが表示される", () => {
    render(<LoanCard loan={activeLoan} onEdit={noop} onDelete={noop} payVal="20000" onPayChange={noop} onPaySubmit={noop} onToggleAuto={noop}/>);
    expect(screen.getByText("反映")).toBeInTheDocument();
  });
});

describe("LoanCard（完済済み）", () => {
  it("残債が0のとき「✓ 完済」バッジが表示される", () => {
    render(<LoanCard loan={paidLoan} onEdit={noop} onDelete={noop} payVal="" onPayChange={noop} onPaySubmit={noop} onToggleAuto={noop}/>);
    expect(screen.getByText(/完済/)).toBeInTheDocument();
  });

  it("完済済みのとき「反映」ボタンは表示されない", () => {
    render(<LoanCard loan={paidLoan} onEdit={noop} onDelete={noop} payVal="" onPayChange={noop} onPaySubmit={noop} onToggleAuto={noop}/>);
    expect(screen.queryByText("反映")).not.toBeInTheDocument();
  });
});

describe("LoanCard（警告表示）", () => {
  it("月返済が月利息以下のとき警告メッセージが表示される", () => {
    const { container } = render(<LoanCard loan={insolventLoan} onEdit={noop} onDelete={noop} payVal="5000" onPayChange={noop} onPaySubmit={noop} onToggleAuto={noop}/>);
    // ページ全体の文字列に警告テキストが含まれることを確認する
    // （yen()の出力が複数テキストノードに分割されるため container.textContent で検索する）
    expect(container.textContent).toMatch(/を下回っています/);
  });
});

describe("LoanCard（ボタン操作）", () => {
  it("編集ボタンで onEdit が呼ばれる", () => {
    const mockEdit = vi.fn();
    render(<LoanCard loan={activeLoan} onEdit={mockEdit} onDelete={noop} payVal="20000" onPayChange={noop} onPaySubmit={noop} onToggleAuto={noop}/>);
    fireEvent.click(screen.getByText("編集"));
    expect(mockEdit).toHaveBeenCalledTimes(1);
  });

  it("削除ボタンで onDelete が呼ばれる", () => {
    const mockDelete = vi.fn();
    render(<LoanCard loan={activeLoan} onEdit={noop} onDelete={mockDelete} payVal="20000" onPayChange={noop} onPaySubmit={noop} onToggleAuto={noop}/>);
    fireEvent.click(screen.getByText("削除"));
    expect(mockDelete).toHaveBeenCalledTimes(1);
  });

  it("反映ボタンで onPaySubmit が呼ばれる", () => {
    const mockSubmit = vi.fn();
    render(<LoanCard loan={activeLoan} onEdit={noop} onDelete={noop} payVal="20000" onPayChange={noop} onPaySubmit={mockSubmit} onToggleAuto={noop}/>);
    fireEvent.click(screen.getByText("反映"));
    expect(mockSubmit).toHaveBeenCalledTimes(1);
  });
});
