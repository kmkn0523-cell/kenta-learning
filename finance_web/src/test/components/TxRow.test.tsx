// ────────── TxRow コンポーネントのテスト ──────────
// 収支1件の通常表示（支出・収入）と編集フォームの切替を確認する

import { render, screen, fireEvent } from "@testing-library/react";
import TxRow from "../../components/TxRow";

// テスト用のカテゴリ・絵文字マップ
const testCats = ["食費", "交通費", "娯楽"];
const testIco: Record<string, string> = { 食費: "🍽️", 交通費: "🚃", 娯楽: "🎮" };

// テスト用の支出サンプルデータ
const expenseItem = {
  id: "tx-001",
  date: "2026-05-10",
  category: "食費",
  amount: 3000,
  memo: "スーパーで買い物",
};

// テスト用の収入サンプルデータ
const incomeItem = {
  id: "tx-002",
  date: "2026-05-01",
  category: "給料",
  amount: 250000,
  memo: "5月分給与",
};

const incCats = ["給料", "副業"];
const incIco: Record<string, string> = { 給料: "💰", 副業: "💼" };

const noop = () => {};

describe("TxRow（支出の通常表示）", () => {
  it("カテゴリ名が表示される", () => {
    render(<TxRow item={expenseItem} onSave={noop} onDelete={noop} cats={testCats} ico={testIco} isInc={false}/>);
    expect(screen.getByText(/食費/)).toBeInTheDocument();
  });

  it("日付が表示される", () => {
    render(<TxRow item={expenseItem} onSave={noop} onDelete={noop} cats={testCats} ico={testIco} isInc={false}/>);
    expect(screen.getByText("2026-05-10")).toBeInTheDocument();
  });

  it("メモが表示される", () => {
    render(<TxRow item={expenseItem} onSave={noop} onDelete={noop} cats={testCats} ico={testIco} isInc={false}/>);
    expect(screen.getByText("スーパーで買い物")).toBeInTheDocument();
  });

  it("支出のとき金額に「-」プレフィックスが付く", () => {
    render(<TxRow item={expenseItem} onSave={noop} onDelete={noop} cats={testCats} ico={testIco} isInc={false}/>);
    // -¥3,000 という形式で表示されることを確認する
    expect(screen.getByText("-¥3,000")).toBeInTheDocument();
  });

  it("収入のとき金額に「+」プレフィックスが付く", () => {
    render(<TxRow item={incomeItem} onSave={noop} onDelete={noop} cats={incCats} ico={incIco} isInc={true}/>);
    expect(screen.getByText("+¥250,000")).toBeInTheDocument();
  });

  it("編集・削除ボタンが表示される", () => {
    render(<TxRow item={expenseItem} onSave={noop} onDelete={noop} cats={testCats} ico={testIco}/>);
    expect(screen.getByText("編集")).toBeInTheDocument();
    expect(screen.getByText("削除")).toBeInTheDocument();
  });
});

describe("TxRow（編集フォーム）", () => {
  it("編集ボタンを押すと「保存」「キャンセル」が表示される", () => {
    render(<TxRow item={expenseItem} onSave={noop} onDelete={noop} cats={testCats} ico={testIco}/>);
    fireEvent.click(screen.getByText("編集"));
    expect(screen.getByText("保存")).toBeInTheDocument();
    expect(screen.getByText("キャンセル")).toBeInTheDocument();
  });

  it("キャンセルで通常表示に戻る", () => {
    render(<TxRow item={expenseItem} onSave={noop} onDelete={noop} cats={testCats} ico={testIco}/>);
    fireEvent.click(screen.getByText("編集"));
    fireEvent.click(screen.getByText("キャンセル"));
    expect(screen.getByText("編集")).toBeInTheDocument();
  });

  it("削除ボタンを押すと onDelete が呼ばれる", () => {
    const mockDelete = vi.fn();
    render(<TxRow item={expenseItem} onSave={noop} onDelete={mockDelete} cats={testCats} ico={testIco}/>);
    fireEvent.click(screen.getByText("削除"));
    expect(mockDelete).toHaveBeenCalledTimes(1);
  });
});
