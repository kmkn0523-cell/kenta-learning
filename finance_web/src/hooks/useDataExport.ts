// ──────── データ出力フック ────────
// 月次 CSV（変動費・収入）のエクスポートをまとめる
// バックアップ/復元は localStorage の暗号化データを扱うため App.tsx に残している
import { useCallback } from "react";
import { Tx, Income } from "../types";
import { transactionsToCsv, downloadFile } from "../utils/dataExport";

interface UseDataExportArgs {
  // エクスポート対象の選択月データ
  monthlyTransactions: Tx[];
  monthlyIncomes: Income[];
  // ダウンロード完了後にトーストを表示する関数
  showT: (msg: string, type?: string) => void;
}

export function useDataExport(args: UseDataExportArgs) {
  const { monthlyTransactions, monthlyIncomes, showT } = args;

  // 変動費 CSV を書き出す（ファイル名例: 支出_2026年5月.csv）
  const exportMonthlyCsv = useCallback((monthLabel: string) => {
    const csv = transactionsToCsv(monthlyTransactions);
    downloadFile(`支出_${monthLabel}.csv`, csv, "text/csv;charset=utf-8");
    showT("CSVを保存しました");
  }, [monthlyTransactions, showT]);

  // 収入 CSV を書き出す（Income は Tx と同じフィールド構成なのでそのまま渡せる）
  const exportMonthlyIncomeCsv = useCallback((monthLabel: string) => {
    // Income を Tx として扱ってよい（id/date/category/amount/memo が一致する）
    const csv = transactionsToCsv(monthlyIncomes as unknown as Tx[]);
    downloadFile(`収入_${monthLabel}.csv`, csv, "text/csv;charset=utf-8");
    showT("CSVを保存しました");
  }, [monthlyIncomes, showT]);

  return { exportMonthlyCsv, exportMonthlyIncomeCsv };
}
