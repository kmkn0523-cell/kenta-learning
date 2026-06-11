// ────────── MonthlyReportModal（月次レポート）のテスト ──────────
import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import MonthlyReportModal from "../../components/MonthlyReportModal";

const noop = () => {};

describe("MonthlyReportModal", () => {
  beforeEach(() => {
    // 月の判定を固定するため日付を 2026-06-15（申告期ではない月）に固定する
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-06-15T12:00:00"));
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it("open=false のとき何も表示されない", () => {
    const { container } = render(
      <MonthlyReportModal open={false} onClose={noop} year={2026} month={5}
        income={300000} expense={200000} topCats={[]} overBudget={[]} hasAccounts={true} />
    );
    expect(container.firstChild).toBeNull();
  });

  it("収支サマリー（振り返りタイトル）が表示される", () => {
    render(
      <MonthlyReportModal open={true} onClose={noop} year={2026} month={5}
        income={300000} expense={200000} topCats={[]} overBudget={[]} hasAccounts={true} />
    );
    expect(screen.getByText("2026年5月の振り返り")).toBeInTheDocument();
  });

  it("貯蓄率20%以上かつ口座ありなら提案バナーが表示される", () => {
    // 収入30万・支出20万 → 貯蓄率 33%
    render(
      <MonthlyReportModal open={true} onClose={noop} year={2026} month={5}
        income={300000} expense={200000} topCats={[]} overBudget={[]} hasAccounts={true} />
    );
    expect(screen.getByText("DMM 株")).toBeInTheDocument();
  });

  it("赤字（貯蓄率マイナス）のとき提案バナーは表示されない", () => {
    render(
      <MonthlyReportModal open={true} onClose={noop} year={2026} month={5}
        income={200000} expense={300000} topCats={[]} overBudget={[]} hasAccounts={true} />
    );
    expect(screen.queryByText("DMM 株")).not.toBeInTheDocument();
  });
});
