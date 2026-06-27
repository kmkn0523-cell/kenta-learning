// ────────── Input の電卓統合テスト ──────────
import { render, screen, fireEvent } from "@testing-library/react";
import { vi } from "vitest";
import { Input } from "../../components/ui";

function press(label: string) {
  fireEvent.click(screen.getByRole("button", { name: label }));
}

describe("Input + 電卓", () => {
  it("money のとき🧮ボタンが出る", () => {
    render(<Input money value="" onChange={() => {}} placeholder="金額（円）" />);
    expect(screen.getByRole("button", { name: "電卓を開く" })).toBeInTheDocument();
  });

  it("money でないとき🧮ボタンは出ない", () => {
    render(<Input value="" onChange={() => {}} placeholder="メモ" />);
    expect(screen.queryByRole("button", { name: "電卓を開く" })).not.toBeInTheDocument();
  });

  it("🧮→計算→確定で onChange にカンマ整形済みの値が渡る", () => {
    const onChange = vi.fn();
    render(<Input money value="" onChange={onChange} placeholder="金額（円）" />);
    press("電卓を開く");
    "1250".split("").forEach(d => press(d));
    press("たす");
    "980".split("").forEach(d => press(d));
    press("確定する");
    expect(onChange).toHaveBeenCalledWith({ target: { value: "2,230" } });
  });
});
