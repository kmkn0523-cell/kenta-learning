// ────────── HealthCheckCard（家計診断カード）のテスト ──────────
// 診断結果に連動した「あなたへの提案」枠の表示・非表示を確認する
import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import HealthCheckCard from "../../components/HealthCheckCard";

describe("HealthCheckCard 提案枠（診断連動広告）", () => {
  beforeEach(() => {
    // 月の判定を固定するため日付を 2026-06-15（申告期ではない月）に固定する
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-06-15T12:00:00"));
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it("貯蓄率20%以上かつ口座ありのとき投資系の提案が表示される", () => {
    // 収入30万・支出20万 → 貯蓄率 33%
    render(
      <HealthCheckCard
        totalIncome={300000}
        totalBurden={200000}
        totalLoanRepayment={0}
        totalFixedExpense={100000}
        net={100000}
        totalSavings={1000000}
        hasAccounts={true}
      />
    );
    expect(screen.getByText("💡 あなたへの提案")).toBeInTheDocument();
    expect(screen.getByText("DMM 株")).toBeInTheDocument();
    expect(screen.getByText("PR")).toBeInTheDocument();
  });

  it("貯蓄率が低いとき提案枠は表示されない", () => {
    // 収入30万・支出29万 → 貯蓄率 3.3%
    render(
      <HealthCheckCard
        totalIncome={300000}
        totalBurden={290000}
        totalLoanRepayment={0}
        totalFixedExpense={100000}
        net={10000}
        totalSavings={100000}
        hasAccounts={true}
      />
    );
    expect(screen.queryByText("💡 あなたへの提案")).not.toBeInTheDocument();
  });

  it("口座未登録のとき投資提案は表示されない", () => {
    render(
      <HealthCheckCard
        totalIncome={300000}
        totalBurden={200000}
        totalLoanRepayment={0}
        totalFixedExpense={100000}
        net={100000}
        totalSavings={0}
        hasAccounts={false}
      />
    );
    expect(screen.queryByText("💡 あなたへの提案")).not.toBeInTheDocument();
  });
});
