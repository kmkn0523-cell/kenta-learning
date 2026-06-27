// ────────── CalculatorSheet（電卓ボトムシート）のテスト ──────────
import { render, screen, fireEvent } from "@testing-library/react";
import { vi } from "vitest";
import CalculatorSheet from "../../components/CalculatorSheet";

const noop = () => {};

// ボタンを aria-label で押すヘルパー
function press(label: string) {
  fireEvent.click(screen.getByRole("button", { name: label }));
}

describe("CalculatorSheet", () => {
  it("open=false のとき何も表示されない", () => {
    const { container } = render(
      <CalculatorSheet open={false} initialValue="" onConfirm={noop} onClose={noop} />
    );
    expect(container.firstChild).toBeNull();
  });

  it("1250 + 980 を計算して確定すると onConfirm(2230) が呼ばれる", () => {
    const onConfirm = vi.fn();
    render(<CalculatorSheet open={true} initialValue="" onConfirm={onConfirm} onClose={noop} />);
    "1250".split("").forEach(d => press(d));
    press("たす");
    "980".split("").forEach(d => press(d));
    press("確定する");
    expect(onConfirm).toHaveBeenCalledWith(2230);
  });

  it("÷0 のときは確定ボタンが無効", () => {
    render(<CalculatorSheet open={true} initialValue="" onConfirm={noop} onClose={noop} />);
    press("1"); press("0"); press("わる"); press("0"); press("イコール");
    expect(screen.getByRole("button", { name: "確定する" })).toBeDisabled();
  });

  it("背景タップで onClose が呼ばれ、onConfirm は呼ばれない", () => {
    const onConfirm = vi.fn();
    const onClose = vi.fn();
    render(<CalculatorSheet open={true} initialValue="500" onConfirm={onConfirm} onClose={onClose} />);
    fireEvent.click(screen.getByTestId("calc-overlay"));
    expect(onClose).toHaveBeenCalled();
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it("Escキーで onClose が呼ばれる", () => {
    const onClose = vi.fn();
    render(<CalculatorSheet open={true} initialValue="" onConfirm={noop} onClose={onClose} />);
    fireEvent.keyDown(window, { key: "Escape" });
    expect(onClose).toHaveBeenCalled();
  });
});
