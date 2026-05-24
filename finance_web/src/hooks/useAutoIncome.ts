// ──────── 定期収入の自動追加フック ────────
// 毎月の給与・副業収入など、定期的な収入を自動でincomeリストに追加する
// useAutoPayment のパターンを踏襲し、1日1回だけ処理が走るように管理する
import { useEffect, useRef } from "react";
import { Income, RecurringIncome } from "../types";
import { newId } from "../utils/crypto";

// このフックが受け取る引数の型定義
interface UseAutoIncomeArgs {
  // 定期収入の設定一覧（ユーザーが登録した定期収入の配列）
  recurringIncomes: RecurringIncome[];
  // 定期収入の設定を更新する関数（lastAutoAdded を書き換えるために使う）
  setRecurringIncomes: (u: RecurringIncome[] | ((p: RecurringIncome[]) => RecurringIncome[])) => void;
  // 収入一覧を更新する関数（自動追加した収入を書き込む）
  setIncomes: (u: Income[] | ((p: Income[]) => Income[])) => void;
  // 全ての usePersist が復号完了した時に true になるフラグ
  ready: boolean;
}

export function useAutoIncome(args: UseAutoIncomeArgs) {
  const { recurringIncomes, setRecurringIncomes, setIncomes, ready } = args;

  // 「最後に自動追加チェックをした日付」を記憶する入れ物（YYYY-MM-DD の文字列）
  // 同じ日に何度も処理が走らないよう見張り番として使う
  const lastAutoRunDate = useRef<string | null>(null);

  useEffect(() => {
    // データの復号がまだ終わっていないなら何もしない
    if (!ready) return;

    function runAutoIncome() {
      // ★毎回ここで現在時刻を取り直す（タブを開いたまま日付跨ぎしても正しく動く）
      const now = new Date();
      const todayKey =
        now.getFullYear() +
        "-" +
        String(now.getMonth() + 1).padStart(2, "0") +
        "-" +
        String(now.getDate()).padStart(2, "0");

      // 今日すでに実行済みならスキップ（StrictMode の二重実行も防ぐ）
      if (lastAutoRunDate.current === todayKey) return;
      lastAutoRunDate.current = todayKey;

      // 追加する収入をまとめておく配列
      const toAdd: Income[] = [];
      // 定期収入の lastAutoAdded 更新分をまとめる（id → 新しい "YYYY-MM"）
      const updatedMap: Record<string, string> = {};

      for (const rec of recurringIncomes) {
        // 停止中（active === false）はスキップ
        if (rec.active === false) continue;

        let lastAdded = rec.lastAutoAdded;
        if (!lastAdded) {
          // 初回処理：前月を基準にすると「今月の振込日が来たら初回自動追加」になる
          const d = new Date(now.getFullYear(), now.getMonth() - 1, 1);
          lastAdded =
            d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0");
        }

        let [ly, lm] = lastAdded.split("-").map(Number);
        let newLastAdded = lastAdded;

        // lastAdded の翌月から現在月まで順番に処理する
        while (true) {
          lm++;
          if (lm > 12) {
            lm = 1;
            ly++;
          }
          // 今月を超えたらループを終了
          if (
            ly > now.getFullYear() ||
            (ly === now.getFullYear() && lm > now.getMonth() + 1)
          )
            break;

          // 振込日を取得（"未設定" の場合は 1日扱い）
          let dayNum = 1;
          if (rec.payDay && rec.payDay !== "未設定") {
            dayNum = parseInt(rec.payDay);
            if (isNaN(dayNum)) dayNum = 1;
          }
          // 月末を超えないよう補正（例: 31日設定 → 2月なら28日）
          const daysInMonth = new Date(ly, lm, 0).getDate();
          const actualDay = Math.min(dayNum, daysInMonth);
          const payDate = new Date(ly, lm - 1, actualDay);

          // 振込日が来ていれば自動追加する
          if (now >= payDate) {
            const dateStr =
              ly +
              "-" +
              String(lm).padStart(2, "0") +
              "-" +
              String(actualDay).padStart(2, "0");
            toAdd.push({
              id: newId(),
              date: dateStr,
              category: rec.category,
              amount: rec.amount,
              // メモに収入名を入れることで「どの定期収入から来たか」がわかる
              memo: `[定期] ${rec.name}`,
            });
            newLastAdded = ly + "-" + String(lm).padStart(2, "0");
          }
        }

        // 変更があった場合だけ更新対象に追加
        if (newLastAdded !== rec.lastAutoAdded) {
          updatedMap[rec.id] = newLastAdded;
        }
      }

      // 自動追加する収入を一括でincomeリストの末尾に追加
      if (toAdd.length > 0) {
        setIncomes((prev) => [...prev, ...toAdd]);
      }

      // 定期収入の lastAutoAdded を更新（重複追加を防ぐために必須）
      if (Object.keys(updatedMap).length > 0) {
        setRecurringIncomes((prev) =>
          prev.map((r) =>
            updatedMap[r.id] ? { ...r, lastAutoAdded: updatedMap[r.id] } : r
          )
        );
      }
    }

    // 起動時に1回実行
    runAutoIncome();

    // タブを再表示した時にも実行（例: 前日に開いたまま翌日に戻ってきたケース）
    function onVisible() {
      if (document.visibilityState === "visible") runAutoIncome();
    }
    document.addEventListener("visibilitychange", onVisible);
    // visibilitychange を発火しないブラウザ向けの保険
    window.addEventListener("focus", runAutoIncome);

    return () => {
      document.removeEventListener("visibilitychange", onVisible);
      window.removeEventListener("focus", runAutoIncome);
    };
  }, [ready, recurringIncomes, setRecurringIncomes, setIncomes]);
}
