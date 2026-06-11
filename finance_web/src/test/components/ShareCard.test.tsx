// ────────── ShareCard（友達に教えるカード）のテスト ──────────
// jsdom には navigator.share / navigator.clipboard が無いので、
// defineProperty で一時的にモックを生やしてテストする
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import ShareCard, { SHARE_URL } from "../../components/ShareCard";

// テストで生やしたモックを毎回掃除する
afterEach(() => {
  // テスト用に defineProperty で生やした share を消す
  delete (navigator as { share?: unknown }).share;
});

describe("ShareCard", () => {
  it("シェアボタンが表示される", () => {
    render(<ShareCard />);
    expect(screen.getByText("📣 友達に教える")).toBeInTheDocument();
  });

  it("navigator.share がある環境ではシェアシートを開く", async () => {
    const shareMock = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "share", { value: shareMock, configurable: true, writable: true });
    render(<ShareCard />);
    fireEvent.click(screen.getByText("📣 友達に教える"));
    await waitFor(() => expect(shareMock).toHaveBeenCalledTimes(1));
    // シェア内容にアプリURLが含まれている
    expect(shareMock.mock.calls[0][0].url).toBe(SHARE_URL);
  });

  it("navigator.share が無い環境ではURLをクリップボードにコピーする", async () => {
    const writeTextMock = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText: writeTextMock }, configurable: true, writable: true,
    });
    render(<ShareCard />);
    fireEvent.click(screen.getByText("📣 友達に教える"));
    // コピー成功のフィードバックがボタンに出る
    await waitFor(() => expect(screen.getByText("✓ リンクをコピーしました")).toBeInTheDocument());
    expect(writeTextMock.mock.calls[0][0]).toContain(SHARE_URL);
  });

  it("クリップボードへのコピーに失敗したらエラーメッセージを出す", async () => {
    const writeTextMock = vi.fn().mockRejectedValue(new Error("denied"));
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText: writeTextMock }, configurable: true, writable: true,
    });
    render(<ShareCard />);
    fireEvent.click(screen.getByText("📣 友達に教える"));
    await waitFor(() => expect(screen.getByText(/コピーできませんでした/)).toBeInTheDocument());
  });
});
