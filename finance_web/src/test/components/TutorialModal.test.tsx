// ────────── TutorialModal コンポーネントのテスト ──────────
import { render, screen, fireEvent } from "@testing-library/react";
import { vi } from "vitest";
import TutorialModal from "../../components/TutorialModal";

const noop = () => {};

describe("TutorialModal（非表示状態）", () => {
  it("open=false のとき何も表示されない", () => {
    const { container } = render(<TutorialModal open={false} onClose={noop} />);
    expect(container.firstChild).toBeNull();
  });
});

describe("TutorialModal（表示状態）", () => {
  it("open=true のとき最初のページ（ようこそ！）が表示される", () => {
    render(<TutorialModal open={true} onClose={noop} />);
    expect(screen.getByText("ようこそ！")).toBeInTheDocument();
  });

  it("最初は「次へ」ボタンが表示される", () => {
    render(<TutorialModal open={true} onClose={noop} />);
    expect(screen.getByText("次へ")).toBeInTheDocument();
  });

  it("「次へ」を5回クリックすると「はじめる」ボタンが表示される", () => {
    render(<TutorialModal open={true} onClose={noop} />);
    const nextBtn = () => screen.getByText("次へ");
    fireEvent.click(nextBtn()); // page 1
    fireEvent.click(nextBtn()); // page 2
    fireEvent.click(nextBtn()); // page 3
    fireEvent.click(nextBtn()); // page 4
    fireEvent.click(nextBtn()); // page 5（最終）
    expect(screen.getByText("はじめる")).toBeInTheDocument();
  });

  it("「はじめる」クリックで onClose が呼ばれる", () => {
    const onClose = vi.fn();
    render(<TutorialModal open={true} onClose={onClose} />);
    // 最終ページまで進む
    for (let i = 0; i < 5; i++) fireEvent.click(screen.getByText("次へ"));
    fireEvent.click(screen.getByText("はじめる"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("✕ボタンクリックで onClose が呼ばれる", () => {
    const onClose = vi.fn();
    render(<TutorialModal open={true} onClose={onClose} />);
    fireEvent.click(screen.getByLabelText("閉じる"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("open が false → true になるとページが 0 にリセットされる", () => {
    const { rerender } = render(<TutorialModal open={true} onClose={noop} />);
    // ページを2まで進める
    fireEvent.click(screen.getByText("次へ"));
    fireEvent.click(screen.getByText("次へ"));
    // 一度閉じて再度開く
    rerender(<TutorialModal open={false} onClose={noop} />);
    rerender(<TutorialModal open={true} onClose={noop} />);
    // ページ0の内容（ようこそ！）が再表示される
    expect(screen.getByText("ようこそ！")).toBeInTheDocument();
  });
});
