// ──────── 固定費の自動月次反映フック ────────
// autoTrack=true に設定された固定費を、毎月自動で変動支出（transactions）に追加する
// useAutoExpense のパターンを踏襲して作られている
// ※ 自動追加された固定費は「[固定費] 名前」というメモ付きで transactions に入る
//    二重計上防止のため、useMonthlyData では autoTrack=true の固定費を totalFixedExpense から除外している

import { useEffect, useRef } from "react";
import { Tx, FixedExpense } from "../types";
import { newId } from "../utils/crypto";

// このフックが受け取る引数の型定義
interface UseAutoFixedExpenseArgs {
  // 固定費の一覧（autoTrack=true の項目だけが処理される）
  fixedExpenses: FixedExpense[];
  // 固定費の一覧を更新する関数（lastAutoAdded を書き換えるために使う）
  setFixedExpenses: (u: FixedExpense[] | ((p: FixedExpense[]) => FixedExpense[])) => void;
  // 変動支出一覧を更新する関数（自動追加した支出を書き込む）
  setTransactions: (u: Tx[] | ((p: Tx[]) => Tx[])) => void;
  // 全ての usePersist が復号完了した時に true になるフラグ
  ready: boolean;
  // 自動追加が発生した時に呼ばれるコールバック（通知などに使う）
  onAutoAdded?: (count: number) => void;
}

export function useAutoFixedExpense(args: UseAutoFixedExpenseArgs) {
  const { fixedExpenses, setFixedExpenses, setTransactions, ready, onAutoAdded } = args;

  // 「最後に自動追加チェックをした日付」を記憶する入れ物（YYYY-MM-DD の文字列）
  // 同じ日に何度も処理が走らないよう見張り番として使う
  const lastAutoRunDate = useRef<string | null>(null);

  useEffect(() => {
    // データの復号がまだ終わっていないなら何もしない
    if (!ready) return;

    function runAutoFixedExpense() {
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

      // 追加する支出をまとめておく配列
      const toAdd: Tx[] = [];
      // 固定費の lastAutoAdded 更新分をまとめる（id → 新しい "YYYY-MM"）
      const updatedMap: Record<string, string> = {};

      for (const fx of fixedExpenses) {
        // 停止中（active === false）または自動追加オフはスキップ
        if (fx.active === false || !fx.autoTrack) continue;

        let lastAdded = fx.lastAutoAdded;
        if (!lastAdded) {
          // 初回処理：前月を基準にすると「今月の引落日が来たら初回自動追加」になる
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

          // 引落日を取得（"未設定" の場合は 1日扱い）
          let dayNum = 1;
          if (fx.payDay && fx.payDay !== "未設定") {
            dayNum = parseInt(fx.payDay);
            if (isNaN(dayNum)) dayNum = 1;
          }
          // 月末を超えないよう補正（例: 31日設定 → 2月なら28日）
          const daysInMonth = new Date(ly, lm, 0).getDate();
          const actualDay = Math.min(dayNum, daysInMonth);
          const payDate = new Date(ly, lm - 1, actualDay);

          // 引落日が来ていれば自動追加する
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
              category: fx.category,
              amount: fx.amount,
              // メモに固定費名を入れることで「どの固定費から来たか」がわかる
              memo: `[固定費] ${fx.name}`,
            });
            newLastAdded = ly + "-" + String(lm).padStart(2, "0");
          }
        }

        // 変更があった場合だけ更新対象に追加
        if (newLastAdded !== fx.lastAutoAdded) {
          updatedMap[fx.id] = newLastAdded;
        }
      }

      // 自動追加する支出を一括で transactions の末尾に追加
      if (toAdd.length > 0) {
        setTransactions((prev) => [...prev, ...toAdd]);
        // 追加件数をコールバックで通知する（通知機能などで使う）
        if (onAutoAdded) onAutoAdded(toAdd.length);
      }

      // 固定費の lastAutoAdded を更新（重複追加を防ぐために必須）
      if (Object.keys(updatedMap).length > 0) {
        setFixedExpenses((prev) =>
          prev.map((f) =>
            updatedMap[f.id] ? { ...f, lastAutoAdded: updatedMap[f.id] } : f
          )
        );
      }
    }

    // 起動時に1回実行
    runAutoFixedExpense();

    // タブを再表示した時にも実行（例: 前日に開いたまま翌日に戻ってきたケース）
    function onVisible() {
      if (document.visibilityState === "visible") runAutoFixedExpense();
    }
    document.addEventListener("visibilitychange", onVisible);
    // visibilitychange を発火しないブラウザ向けの保険
    window.addEventListener("focus", runAutoFixedExpense);

    return () => {
      document.removeEventListener("visibilitychange", onVisible);
      window.removeEventListener("focus", runAutoFixedExpense);
    };
  }, [ready, fixedExpenses, setFixedExpenses, setTransactions]);
}
