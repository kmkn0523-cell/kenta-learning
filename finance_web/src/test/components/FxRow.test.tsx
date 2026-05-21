// ────────── FxRow コンポーネントのテスト ──────────
// 固定費1件の通常表示と編集フォームの切替を確認する

import { render, screen, fireEvent } from "@testing-library/react";
import FxRow from "../../components/FxRow";

// テスト用の固定費サンプルデータ
const sampleItem = {
  id: "fx-001",
  name: "家賃",
  category: "住居",
  amount: 80000,
};

// モック関数：onSave・onDelete・onMoveUp・onMoveDown の代わりに使う空の関数
const noop = () => {};

describe("FxRow（通常表示）", () => {
  it("固定費の名前が表示される", () => {
    render(<FxRow item={sampleItem} onSave={noop} onDelete={noop} onMoveUp={noop} onMoveDown={noop}/>);
    // 「家賃」という文字が画面にあることを確認する
    expect(screen.getByText("家賃")).toBeInTheDocument();
  });

  it("カテゴリ名が表示される", () => {
    render(<FxRow item={sampleItem} onSave={noop} onDelete={noop} onMoveUp={noop} onMoveDown={noop}/>);
    expect(screen.getByText("住居")).toBeInTheDocument();
  });

  it("編集・削除・上下移動ボタンが表示される", () => {
    render(<FxRow item={sampleItem} onSave={noop} onDelete={noop} onMoveUp={noop} onMoveDown={noop}/>);
    expect(screen.getByText("編集")).toBeInTheDocument();
    expect(screen.getByText("削除")).toBeInTheDocument();
    expect(screen.getByText("↑")).toBeInTheDocument();
    expect(screen.getByText("↓")).toBeInTheDocument();
  });

  it("onMoveUp が null のとき ↑ ボタンが無効になる", () => {
    render(<FxRow item={sampleItem} onSave={noop} onDelete={noop} onMoveUp={null} onMoveDown={noop}/>);
    const upBtn = screen.getByText("↑");
    // disabled 属性が付いていることを確認する
    expect(upBtn).toBeDisabled();
  });

  it("onMoveDown が null のとき ↓ ボタンが無効になる", () => {
    render(<FxRow item={sampleItem} onSave={noop} onDelete={noop} onMoveUp={noop} onMoveDown={null}/>);
    const downBtn = screen.getByText("↓");
    expect(downBtn).toBeDisabled();
  });
});

describe("FxRow（編集フォーム）", () => {
  it("編集ボタンを押すと「保存」「キャンセル」ボタンが表示される", () => {
    render(<FxRow item={sampleItem} onSave={noop} onDelete={noop} onMoveUp={noop} onMoveDown={noop}/>);
    // 編集ボタンをクリックして編集モードに切り替える
    fireEvent.click(screen.getByText("編集"));
    expect(screen.getByText("保存")).toBeInTheDocument();
    expect(screen.getByText("キャンセル")).toBeInTheDocument();
  });

  it("キャンセルボタンで通常表示に戻る", () => {
    render(<FxRow item={sampleItem} onSave={noop} onDelete={noop} onMoveUp={noop} onMoveDown={noop}/>);
    fireEvent.click(screen.getByText("編集"));
    fireEvent.click(screen.getByText("キャンセル"));
    // キャンセル後は「編集」ボタンが再表示されることを確認する
    expect(screen.getByText("編集")).toBeInTheDocument();
  });

  it("削除ボタンを押すと onDelete が呼ばれる", () => {
    // jest.fn() でモック関数を作り、呼ばれたか確認できるようにする
    const mockDelete = vi.fn();
    render(<FxRow item={sampleItem} onSave={noop} onDelete={mockDelete} onMoveUp={noop} onMoveDown={noop}/>);
    fireEvent.click(screen.getByText("削除"));
    expect(mockDelete).toHaveBeenCalledTimes(1);
  });
});
